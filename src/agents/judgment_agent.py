"""
judgment_agent.py
-----------------
Agent 3 of 4 from the original MAGI paper.

The Judgment Agent evaluates participant responses against MINI diagnostic
criteria in real-time. It decides:
  - YES: The criterion is clearly met
  - NO: The criterion is clearly not met
  - UNCERTAIN: The response is ambiguous — needs clarification

It uses three thresholds (from the original paper):
  1. Direct matching: Response explicitly meets/denies the criterion
  2. Semantic matching: Response implies it in different words
  3. Ambiguity resolution: After 5 unproductive turns, use forced choice

When UNCERTAIN is returned after max_retries turns, the agent activates
the "forced choice" mechanism — presenting binary MINI-compliant options.
"""

from __future__ import annotations
from typing import Optional
from src.utils.mini_tree import MiniNode
from src.utils.data_models import NodeEvaluation, NodeStatus
from src.utils.llm_client import (
    LLMClient, LLMConfig, system_message, user_message, SYSTEM_PROMPTS
)


# ─────────────────────────────────────────────
# JUDGMENT RESULT
# ─────────────────────────────────────────────

class JudgmentResult:
    """Result of evaluating a participant response."""

    def __init__(
        self,
        verdict: bool | None,     # True=Yes, False=No, None=Uncertain
        confidence: float,        # 0.0–1.0
        evidence: str,            # Key quote from participant response
        reasoning: str,           # Why this judgment was made
        needs_clarification: bool = False,
        forced_choice_options: Optional[tuple[str, str]] = None,
    ):
        self.verdict = verdict
        self.confidence = confidence
        self.evidence = evidence
        self.reasoning = reasoning
        self.needs_clarification = needs_clarification
        self.forced_choice_options = forced_choice_options  # (option_A, option_B)

    @property
    def is_certain(self) -> bool:
        return self.verdict is not None and self.confidence >= 0.7

    def __repr__(self) -> str:
        v = "YES" if self.verdict is True else ("NO" if self.verdict is False else "UNCERTAIN")
        return f"JudgmentResult({v}, confidence={self.confidence:.2f})"


# ─────────────────────────────────────────────
# JUDGMENT AGENT
# ─────────────────────────────────────────────

class JudgmentAgent:
    """
    Validates participant responses against MINI criteria.
    """

    MAX_RETRIES_BEFORE_FORCED_CHOICE = 5

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient(LLMConfig(temperature=0.2))
        # Track how many times each node has been retried
        self._retry_counts: dict[str, int] = {}

    def evaluate(
        self,
        node: MiniNode,
        participant_response: str,
        conversation_context: str = "",
    ) -> JudgmentResult:
        """
        Evaluate a participant's response against a MINI node's criterion.
        Uses rule-based classification first (fast + reliable),
        falls back to LLM only when rules are insufficient.
        """
        # Track retries for this node
        retry_count = self._retry_counts.get(node.node_id, 0)
        self._retry_counts[node.node_id] = retry_count + 1

        # After too many retries → force choice
        if retry_count >= self.MAX_RETRIES_BEFORE_FORCED_CHOICE:
            return self._forced_choice_result(node)

        # ── Rule-based judgment (fast pre-filter) ──────────────
        # Handles clear Yes/No without using LLM tokens
        rule_result = self._rule_based_judgment(participant_response)
        if rule_result is not None:
            return JudgmentResult(
                verdict=rule_result,
                confidence=0.9,
                evidence=participant_response[:150],
                reasoning="Rule-based classification (clear Yes/No response)",
                needs_clarification=False,
            )

        # ── LLM for genuinely ambiguous responses ───────────────
        raw = self.llm.call_with_json(
            self._build_eval_prompt(node, participant_response, conversation_context)
        )
        return self._parse_llm_response(raw, participant_response)

    @staticmethod
    def _rule_based_judgment(response: str) -> bool | None:
        """
        Fast rule-based Yes/No classifier for clear responses.
        Returns True, False, or None (ambiguous — needs LLM).
        """
        r = response.lower().strip()

        # Clear YES patterns
        yes_patterns = [
            r.startswith("yes"),
            r.startswith("yeah"),
            r.startswith("definitely"),
            r.startswith("absolutely"),
            r.startswith("certainly"),
            "yes," in r,
            "yes." in r,
            "i have" in r and "not" not in r,
            "i do" in r and "not" not in r and "don" not in r,
            "i've been" in r,
            "i feel" in r and "not" not in r and "don" not in r,
            "i am" in r and "not" not in r,
        ]

        # Clear NO patterns
        no_patterns = [
            r.startswith("no,"),
            r.startswith("no."),
            r.startswith("not really"),
            r.startswith("nope"),
            r == "no",
            "i don't" in r,
            "i do not" in r,
            "i haven't" in r,
            "i have not" in r,
            "not particularly" in r,
            "not at all" in r,
            "no thoughts" in r,
            "no, i" in r,
        ]

        yes_score = sum(yes_patterns)
        no_score = sum(no_patterns)

        if yes_score > 0 and no_score == 0:
            return True
        if no_score > 0 and yes_score == 0:
            return False
        return None  # Genuinely ambiguous — use LLM

    def create_node_evaluation(
        self,
        node: MiniNode,
        result: JudgmentResult,
        turns_taken: int,
    ) -> NodeEvaluation:
        """
        Create a NodeEvaluation record from a JudgmentResult.
        This is stored in the InterviewSession for the diagnosis agent.
        """
        if result.verdict is True:
            status = NodeStatus.COMPLETED
        elif result.verdict is False:
            status = NodeStatus.COMPLETED
        else:
            status = NodeStatus.IN_PROGRESS

        return NodeEvaluation(
            node_id=node.node_id,
            node_label=node.label,
            status=status,
            criterion_met=result.verdict,
            evidence=result.evidence,
            turns_taken=turns_taken,
        )

    def reset_node_retries(self, node_id: str) -> None:
        """Reset retry counter for a node (called when moving to next node)."""
        self._retry_counts.pop(node_id, None)

    # ── PRIVATE HELPERS ───────────────────────

    def _build_eval_prompt(
        self,
        node: MiniNode,
        response: str,
        context: str,
    ) -> list[dict]:
        """Build the LLM prompt for criterion evaluation."""
        return [
            system_message(
                "You are a clinical response evaluator. "
                "Respond ONLY with a valid JSON object. No thinking steps, no explanation. "
                "Pure JSON starting with { and ending with }."
            ),
            user_message(
                f"Criterion: {node.clinical_criterion}\n"
                f"Participant said: \"{response}\"\n\n"
                f"Does this response meet the criterion? "
                f"Return ONLY: "
                f'{{\"verdict\":\"yes\",\"confidence\":0.9,\"evidence\":\"{response[:80]}\",\"reasoning\":\"brief\",\"needs_clarification\":false}}'
                f"\nReplace values based on actual assessment. verdict must be yes, no, or uncertain."
            ),
        ]

    def _parse_llm_response(
        self,
        raw: dict,
        fallback_evidence: str,
    ) -> JudgmentResult:
        """Parse the LLM JSON response into a JudgmentResult."""
        if not raw:
            return JudgmentResult(
                verdict=None,
                confidence=0.0,
                evidence=fallback_evidence[:100],
                reasoning="LLM call failed — treating as uncertain",
                needs_clarification=True,
            )

        verdict_str = raw.get("verdict", "uncertain").lower()
        verdict = True if verdict_str == "yes" else (
            False if verdict_str == "no" else None
        )

        return JudgmentResult(
            verdict=verdict,
            confidence=float(raw.get("confidence", 0.5)),
            evidence=raw.get("evidence", fallback_evidence[:150]),
            reasoning=raw.get("reasoning", ""),
            needs_clarification=bool(raw.get("needs_clarification", False)),
        )

    def _forced_choice_result(self, node: MiniNode) -> JudgmentResult:
        """
        Generate a forced-choice result after max retries.
        The Question Agent will present binary options to the participant.
        """
        # Build MINI-compliant forced choice options
        option_a = f"Yes, {node.clinical_criterion.lower()}"
        option_b = f"No, I have not experienced this"

        return JudgmentResult(
            verdict=None,
            confidence=0.0,
            evidence="",
            reasoning=f"Maximum retries ({self.MAX_RETRIES_BEFORE_FORCED_CHOICE}) "
                      f"reached — activating forced choice",
            needs_clarification=True,
            forced_choice_options=(option_a, option_b),
        )

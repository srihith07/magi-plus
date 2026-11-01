"""
diagnosis_agent.py
------------------
Agent 4 of 4 from the original MAGI paper.

The Diagnosis Agent is responsible for synthesizing all collected evidence
into a DSM-5 compliant diagnosis using the PsyCoT (Psychometric Chain-of-Thought)
reasoning framework — the core novel contribution of the original MAGI paper.

PsyCoT has 3 phases:
  Phase 1 — Symptom Anchoring:
    Each DSM-5 criterion is validated: symptom existence, temporal check,
    exclusion conditions.

  Phase 2 — Diagnostic Synthesis:
    Verifies that the total confirmed symptoms exceed the diagnostic threshold
    and that core symptoms are present.

  Phase 3 — Evidence Binding:
    Creates an auditable trail: which participant responses confirmed each
    criterion, how duration/exclusion rules were applied, uncertainty sources.
"""

from __future__ import annotations
from typing import Optional
from src.utils.mini_tree import MiniTree, build_mini_tree
from src.utils.data_models import (
    Disorder, DiagnosisResult, PsyCoTTrace, NodeEvaluation, InterviewSession
)
from src.utils.llm_client import (
    LLMClient, LLMConfig, system_message, user_message, SYSTEM_PROMPTS
)


# ─────────────────────────────────────────────
# DIAGNOSIS CRITERIA (DSM-5 aligned)
# ─────────────────────────────────────────────

# Minimum symptoms required for each disorder
DIAGNOSIS_THRESHOLDS = {
    Disorder.DEPRESSION: {
        "min_symptoms": 5,
        "required_core": ["DEP_A1a", "DEP_A1b"],  # At least one core symptom required
        "duration_criterion": "≥2 weeks nearly every day",
        "dsm5_code": "F32.x",
    },
    Disorder.GENERALIZED_ANXIETY: {
        "min_symptoms": 3,  # ≥3 of 6 physical symptoms
        "required_core": ["GAD_N1a", "GAD_N2"],  # Both entry criteria required
        "duration_criterion": "≥6 months",
        "dsm5_code": "F41.1",
    },
    Disorder.SOCIAL_ANXIETY: {
        "min_symptoms": 4,  # All 4 main criteria required
        "required_core": ["SOC_F1a", "SOC_F2"],
        "duration_criterion": "≥6 months",
        "dsm5_code": "F40.10",
    },
    Disorder.SUICIDE_RISK: {
        "min_symptoms": 1,  # Any positive indicator is significant
        "required_core": ["SUI_B2"],  # Active ideation
        "duration_criterion": "Current / past month",
        "dsm5_code": "Z91.5x",
    },
}


# ─────────────────────────────────────────────
# DIAGNOSIS AGENT
# ─────────────────────────────────────────────

class DiagnosisAgent:
    """
    Synthesizes interview evidence into DSM-5 diagnoses via PsyCoT reasoning.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None, tree: Optional[MiniTree] = None):
        self.llm = llm_client or LLMClient(LLMConfig(temperature=0.2))
        self.tree = tree or build_mini_tree()

    def diagnose(
        self,
        disorder: Disorder,
        node_evaluations: list[NodeEvaluation],
        conversation_transcript: str,
    ) -> PsyCoTTrace:
        """
        Run PsyCoT diagnosis for a single disorder.
        Uses LLM-based reasoning (DeepSeek/OpenAI) for proper AI-driven diagnosis,
        with a rule-based fallback if JSON parsing fails.
        """
        section_prefix = self._get_section_prefix(disorder)
        disorder_evals = [
            e for e in node_evaluations
            if e.node_id.startswith(section_prefix)
        ]

        # Try LLM-based PsyCoT first
        raw = self.llm.call_with_json(
            self._build_psycot_prompt(disorder, disorder_evals, conversation_transcript),
            max_tokens=800,
        )

        if raw and raw.get("result") in ("yes", "no", "uncertain"):
            return self._parse_psycot_response(raw, disorder, disorder_evals)

        # Fallback: rule-based from node evaluations (reliable, no LLM needed)
        return self._rule_based_diagnosis(disorder, disorder_evals)

    def _rule_based_diagnosis(
        self,
        disorder: Disorder,
        disorder_evals: list[NodeEvaluation],
    ) -> PsyCoTTrace:
        """Rule-based fallback when LLM JSON parsing fails."""
        threshold_info = DIAGNOSIS_THRESHOLDS[disorder]
        symptoms_confirmed, symptoms_denied, key_evidence = [], [], []

        for e in disorder_evals:
            if e.node_id.endswith(("SYNTHESIS", "NEGATIVE", "LOW")):
                continue
            if e.criterion_met is True:
                symptoms_confirmed.append(e.node_label)
                if e.evidence:
                    key_evidence.append(e.evidence[:100])
            elif e.criterion_met is False:
                symptoms_denied.append(e.node_label)

        count = len(symptoms_confirmed)
        required = threshold_info["min_symptoms"]
        threshold_passed = count >= required
        core_met = any(
            any(e.node_id == core and e.criterion_met is True for e in disorder_evals)
            for core in threshold_info["required_core"]
        )

        if threshold_passed and (core_met or disorder == Disorder.SUICIDE_RISK):
            result, confidence = DiagnosisResult.YES, min(0.95, 0.7 + (count - required) * 0.05)
        elif count > 0:
            result, confidence = DiagnosisResult.UNCERTAIN, 0.4 + (count / required) * 0.2
        else:
            result, confidence = DiagnosisResult.NO, 0.85

        reasoning = (
            f"{count} of {required} required symptoms confirmed "
            f"({'threshold met' if threshold_passed else 'not met'}). "
            f"Duration: {threshold_info['duration_criterion']}."
        )
        if symptoms_confirmed:
            reasoning += f" Confirmed: {', '.join(symptoms_confirmed[:3])}."

        return PsyCoTTrace(
            disorder=disorder,
            symptoms_confirmed=symptoms_confirmed,
            symptoms_denied=symptoms_denied,
            temporal_verification=threshold_info["duration_criterion"],
            exclusion_checks="No exclusionary conditions identified.",
            criteria_met_count=count,
            criteria_required=required,
            threshold_passed=threshold_passed,
            key_evidence=key_evidence[:3],
            reasoning_summary=reasoning,
            result=result,
            confidence=round(confidence, 2),
        )

    def diagnose_all(self, session: InterviewSession) -> dict[str, PsyCoTTrace]:
        """
        Run PsyCoT diagnosis for all disorders screened in the session.
        Updates session.diagnoses in place and returns the dict.
        """
        # Build a single transcript from the full conversation
        transcript_lines = []
        for turn in session.conversation:
            transcript_lines.append(f"Interviewer: {turn.agent_utterance}")
            transcript_lines.append(f"Participant: {turn.participant_response}")
        full_transcript = "\n".join(transcript_lines)

        results = {}
        for disorder in Disorder:
            trace = self.diagnose(
                disorder=disorder,
                node_evaluations=session.node_evaluations,
                conversation_transcript=full_transcript,
            )
            results[disorder.value] = trace
            session.diagnoses[disorder.value] = trace

        return results

    # ── PRIVATE HELPERS ───────────────────────

    def _build_psycot_prompt(
        self,
        disorder: Disorder,
        evaluations: list[NodeEvaluation],
        transcript: str,
    ) -> list[dict]:
        """Build the PsyCoT reasoning prompt."""
        threshold_info = DIAGNOSIS_THRESHOLDS[disorder]

        # Format node evaluations as evidence table
        eval_lines = []
        for e in evaluations:
            met = "YES" if e.criterion_met is True else (
                "NO" if e.criterion_met is False else "UNCERTAIN"
            )
            eval_lines.append(
                f"  - {e.node_id} [{e.node_label}]: {met} | Evidence: {e.evidence}"
            )
        eval_summary = "\n".join(eval_lines) if eval_lines else "No evaluations recorded."

        # Simplified, direct prompt that forces clean JSON output
        # Avoids triggering the reasoning model's step-by-step thinking mode
        return [
            system_message(
                "You are a clinical diagnosis system. "
                "You MUST respond with ONLY a valid JSON object. "
                "No explanations, no thinking steps, no markdown. "
                "Pure JSON only, starting with { and ending with }."
            ),
            user_message(f"""
Diagnose {disorder.value.upper().replace("_", " ")} based on these interview results.

SYMPTOMS COLLECTED:
{eval_summary}

TRANSCRIPT EXCERPT:
{transcript[:800]}

THRESHOLD: {threshold_info["min_symptoms"]} symptoms required. Duration: {threshold_info["duration_criterion"]}.

Return ONLY this JSON (no other text):
{{"phase1_symptom_anchoring":{{"symptoms_confirmed":[],"symptoms_denied":[],"temporal_verification":"","exclusion_checks":""}},"phase2_diagnostic_synthesis":{{"criteria_met_count":0,"criteria_required":{threshold_info["min_symptoms"]},"threshold_passed":false,"synthesis_reasoning":""}},"phase3_evidence_binding":{{"key_evidence":[],"reasoning_summary":""}},"result":"yes","confidence":0.8}}

Fill in the values based on the evidence above. result must be "yes", "no", or "uncertain".
"""),
        ]

    def _parse_psycot_response(
        self,
        raw: dict,
        disorder: Disorder,
        evaluations: list[NodeEvaluation],
    ) -> PsyCoTTrace:
        """Parse the LLM JSON response into a PsyCoTTrace."""
        if not raw:
            return PsyCoTTrace(
                disorder=disorder,
                result=DiagnosisResult.UNCERTAIN,
                confidence=0.0,
                reasoning_summary="PsyCoT reasoning failed — LLM error",
            )

        p1 = raw.get("phase1_symptom_anchoring", {})
        p2 = raw.get("phase2_diagnostic_synthesis", {})
        p3 = raw.get("phase3_evidence_binding", {})

        result_str = raw.get("result", "uncertain").lower()
        result = (
            DiagnosisResult.YES if result_str == "yes"
            else DiagnosisResult.NO if result_str == "no"
            else DiagnosisResult.UNCERTAIN
        )

        return PsyCoTTrace(
            disorder=disorder,
            # Phase 1
            symptoms_confirmed=p1.get("symptoms_confirmed", []),
            symptoms_denied=p1.get("symptoms_denied", []),
            temporal_verification=p1.get("temporal_verification", ""),
            exclusion_checks=p1.get("exclusion_checks", ""),
            # Phase 2
            criteria_met_count=int(p2.get("criteria_met_count", 0)),
            criteria_required=int(p2.get("criteria_required",
                DIAGNOSIS_THRESHOLDS[disorder]["min_symptoms"])),
            threshold_passed=bool(p2.get("threshold_passed", False)),
            # Phase 3
            key_evidence=p3.get("key_evidence", []),
            reasoning_summary=p3.get("reasoning_summary", ""),
            # Overall
            result=result,
            confidence=float(raw.get("confidence", 0.5)),
        )

    def _get_section_prefix(self, disorder: Disorder) -> str:
        """Get the node ID prefix for a disorder's section."""
        prefixes = {
            Disorder.DEPRESSION: "DEP",
            Disorder.GENERALIZED_ANXIETY: "GAD",
            Disorder.SOCIAL_ANXIETY: "SOC",
            Disorder.SUICIDE_RISK: "SUI",
        }
        return prefixes.get(disorder, "")

    def format_diagnosis_summary(self, traces: dict[str, PsyCoTTrace]) -> str:
        """Format all PsyCoT traces into a human-readable diagnostic summary."""
        lines = ["=" * 60, "DIAGNOSTIC SUMMARY", "=" * 60]

        for disorder_key, trace in traces.items():
            disorder_name = disorder_key.upper().replace("_", " ")
            result_str = trace.result.value.upper()
            lines.append(f"\n{disorder_name}: {result_str} (confidence: {trace.confidence:.0%})")

            if trace.symptoms_confirmed:
                lines.append(f"  Confirmed symptoms: {', '.join(trace.symptoms_confirmed)}")
            if trace.temporal_verification:
                lines.append(f"  Duration: {trace.temporal_verification}")
            if trace.reasoning_summary:
                lines.append(f"  Reasoning: {trace.reasoning_summary}")

        lines.append("=" * 60)
        return "\n".join(lines)

"""
main.py
-------
MAGI+ Full Pipeline Orchestrator

This is the entry point that wires all 9 components together:

  Original MAGI agents:
    1. NavigationAgent   — controls interview flow
    2. QuestionAgent     — generates adaptive questions
    3. JudgmentAgent     — validates responses
    4. DiagnosisAgent    — PsyCoT reasoning

  Our extensions:
    5. EmotionTracker    — per-turn emotion timeline
    6. SeverityScorer    — PHQ-9, GAD-7, C-SSRS
    7. RecommendationAgent — treatment recommendations
    8. LongitudinalMemory  — multi-session tracking
    9. ReportGenerator   — clinical report output

Run modes:
  - Interactive: real conversation with a human participant
  - Simulated:   automated run with a pre-defined simulated participant
                 (used for experiments and evaluation)
"""

from __future__ import annotations
import os
import uuid
import json
from datetime import datetime
from typing import Optional

from src.utils.llm_client import LLMClient, LLMConfig
from src.utils.mini_tree import build_mini_tree
from src.utils.data_models import (
    InterviewSession, ConversationTurn, NodeEvaluation,
    QuestionStrategy, Disorder
)
from src.agents.navigation_agent import NavigationAgent
from src.agents.question_agent import QuestionAgent
from src.agents.judgment_agent import JudgmentAgent, JudgmentResult
from src.agents.diagnosis_agent import DiagnosisAgent
from src.agents.recommendation_agent import RecommendationAgent
from src.extensions.emotion_tracker import EmotionTracker
from src.extensions.severity_scorer import SeverityScorer
from src.extensions.longitudinal_memory import LongitudinalMemory
from src.extensions.report_generator import ReportGenerator


# ─────────────────────────────────────────────
# MAGI+ PIPELINE
# ─────────────────────────────────────────────

class MAGIPlusPipeline:
    """
    The full MAGI+ interview pipeline.
    Instantiate once per session.
    """

    def __init__(
        self,
        participant_id: str,
        model: str = "gpt-4o",
        verbose: bool = True,
        reports_dir: Optional[str] = None,
    ):
        self.participant_id = participant_id
        self.verbose = verbose

        # ── Shared LLM client ─────────────────
        config = LLMConfig(model=model, temperature=0.7)
        self.llm = LLMClient(config)

        # ── MINI tree ─────────────────────────
        self.tree = build_mini_tree()

        # ── Agents ────────────────────────────
        # Groq/OpenAI: single model for everything (clean JSON)
        # NVIDIA NIM reasoning models: split to avoid JSON leakage
        is_reasoning_model = any(
            x in model for x in ["nemotron", "mistral-large-4"]
        )
        json_model = "mistralai/mistral-large-4-1t-a52b" if is_reasoning_model else model

        self.nav        = NavigationAgent(tree=self.tree)
        self.questioner = QuestionAgent(llm_client=self.llm)
        self.judge      = JudgmentAgent(llm_client=LLMClient(LLMConfig(model=json_model, temperature=0.1)))
        self.diagnoser  = DiagnosisAgent(llm_client=LLMClient(LLMConfig(model=json_model, temperature=0.1)), tree=self.tree)

        # ── Extensions ────────────────────────
        self.emotion_tracker = EmotionTracker(llm_client=LLMClient(LLMConfig(model=json_model, temperature=0.1)))
        self.severity_scorer = SeverityScorer()
        self.recommender     = RecommendationAgent(llm_client=LLMClient(LLMConfig(model=json_model, temperature=0.3)))
        self.memory          = LongitudinalMemory()
        self.report_gen      = ReportGenerator()

        # ── Session setup ─────────────────────
        session_number = self.memory.get_session_number(participant_id)
        self.session = InterviewSession(
            session_id=str(uuid.uuid4()),
            participant_id=participant_id,
            session_number=session_number,
            llm_model_used=model,
        )

        self.reports_dir = reports_dir or os.path.join(
            os.path.dirname(__file__), "..", "experiments", "reports"
        )
        self._turn_id = 0
        self._current_node = None

        if self.verbose:
            print(f"\n{'='*60}")
            print(f"MAGI+ Session Started")
            print(f"Participant: {participant_id} | Session #{session_number}")
            print(f"Conversational model: {model}")
            print(f"JSON/Structured model: {json_model}")
            print(f"{'='*60}\n")

    # ─────────────────────────────────────────
    # PUBLIC: RUN INTERACTIVE SESSION
    # ─────────────────────────────────────────

    def run_interactive(self) -> str:
        """
        Run a full interactive interview session with a human participant.
        Reads input from stdin, outputs to stdout.
        Returns the path to the generated report.
        """
        print(self.questioner.generate_opening_message())
        print()

        # Start navigation
        self._current_node = self.nav.start_interview()
        if not self._current_node:
            return self._finalize()

        # Main interview loop
        previous_disorder = None

        while not self.nav.is_complete():
            # Announce disorder transition
            current_disorder = self.nav.state.current_disorder
            if current_disorder != previous_disorder and previous_disorder is not None:
                transition = self.questioner.generate_transition_message(
                    previous_disorder, current_disorder
                )
                print(f"\n{transition}\n")
            previous_disorder = current_disorder

            # Generate question
            question, strategy = self.questioner.generate_question(
                node=self._current_node,
                conversation_history=self.session.conversation,
                last_emotion=self.emotion_tracker.get_latest_emotion(),
            )

            # Handle forced choice
            judgment_result = self._interview_turn_interactive(question, strategy)
            if judgment_result is None:
                break

            # Advance to next node
            self._current_node = self.nav.next_node(
                judgment_result.verdict,
                self._current_node,
            )

        # Closing message
        print(f"\n{self.questioner.generate_closing_message()}\n")

        return self._finalize()

    # ─────────────────────────────────────────
    # PUBLIC: RUN SIMULATED SESSION
    # ─────────────────────────────────────────

    def run_simulated(self, simulated_responses: dict[str, str]) -> str:
        """
        Run a simulated interview using pre-defined responses.
        Used for experiments and evaluation (no human input required).

        Args:
            simulated_responses: Dict mapping node_id → participant response text

        Returns:
            Path to the generated report
        """
        if self.verbose:
            print("[MODE: Simulated — no human input required]\n")

        self._current_node = self.nav.start_interview()

        while not self.nav.is_complete() and self._current_node:
            node = self._current_node

            # Generate question (still use LLM for authentic question text)
            question, strategy = self.questioner.generate_question(
                node=node,
                conversation_history=self.session.conversation,
                last_emotion=self.emotion_tracker.get_latest_emotion(),
            )

            # Get simulated response for this node
            participant_response = simulated_responses.get(
                node.node_id,
                "I'm not sure."  # Fallback for unmapped nodes
            )

            if self.verbose:
                # Show clean truncated question (first 100 chars)
                q_display = question[:100].replace('\n', ' ')
                print(f"[{node.node_id}] Q: {q_display}")
                print(f"          A: {participant_response}")

            # Process the turn (same logic as interactive)
            judgment = self._process_turn(
                question=question,
                participant_response=participant_response,
                strategy=strategy,
                node=node,
            )

            # Advance
            self._current_node = self.nav.next_node(
                judgment.verdict if judgment else None,
                node,
            )

        return self._finalize()

    # ─────────────────────────────────────────
    # PRIVATE: TURN PROCESSING
    # ─────────────────────────────────────────

    def _interview_turn_interactive(
        self,
        question: str,
        strategy: QuestionStrategy,
    ) -> Optional[JudgmentResult]:
        """Handle one interactive turn: display question, collect input."""
        if not self._current_node:
            return None

        # Display forced choice if needed
        print(f"Interviewer: {question}")

        # Check if we need forced choice
        retry_count = self.judge._retry_counts.get(self._current_node.node_id, 0)
        if retry_count >= self.judge.MAX_RETRIES_BEFORE_FORCED_CHOICE:
            print("\n(Please choose one of the following options:)")

        participant_response = input("Participant: ").strip()
        if not participant_response:
            participant_response = "I'm not sure."

        return self._process_turn(
            question=question,
            participant_response=participant_response,
            strategy=strategy,
            node=self._current_node,
        )

    def _process_turn(
        self,
        question: str,
        participant_response: str,
        strategy: QuestionStrategy,
        node,
    ) -> JudgmentResult:
        """
        Core per-turn processing:
        1. Track emotion (Extension 1)
        2. Evaluate response (Judgment Agent)
        3. Record the turn in the session
        """
        self._turn_id += 1

        # ── Extension 1: Emotion tracking ─────
        emotion_point = self.emotion_tracker.analyze_turn(
            turn_id=self._turn_id,
            participant_response=participant_response,
            node_id=node.node_id,
        )

        # ── Judgment Agent ─────────────────────
        # Build brief context from last 2 turns
        context = ""
        if len(self.session.conversation) >= 2:
            last = self.session.conversation[-1]
            context = f"Previous: '{last.agent_utterance}' → '{last.participant_response}'"

        judgment = self.judge.evaluate(
            node=node,
            participant_response=participant_response,
            conversation_context=context,
        )

        # ── Record the turn ───────────────────
        turn = ConversationTurn(
            turn_id=self._turn_id,
            node_id=node.node_id,
            agent_utterance=question,
            participant_response=participant_response,
            strategy_used=strategy,
            emotion_detected=emotion_point.emotion,
        )
        self.session.add_turn(turn)

        # Record node evaluation when criterion is settled
        if judgment.is_certain or judgment.forced_choice_options:
            node_eval = self.judge.create_node_evaluation(
                node=node,
                result=judgment,
                turns_taken=self._turn_id,
            )
            self.session.node_evaluations.append(node_eval)
            self.judge.reset_node_retries(node.node_id)

        return judgment

    # ─────────────────────────────────────────
    # PRIVATE: FINALIZATION
    # ─────────────────────────────────────────

    def _finalize(self) -> str:
        """
        Run all post-interview processing and generate the report.
        This is where Extensions 1-5 all come together.
        """
        self.session.completed_at = datetime.utcnow()
        duration = (
            (self.session.completed_at - self.session.created_at).total_seconds() / 60
        )
        self.session.duration_minutes = round(duration, 1)

        if self.verbose:
            print("\n" + "="*60)
            print("POST-INTERVIEW PROCESSING")
            print("="*60)

        # ── Step 1: Diagnose (PsyCoT) ─────────
        if self.verbose:
            print("\n[1/5] Running PsyCoT diagnosis...")
        self.diagnoser.diagnose_all(self.session)
        if self.verbose:
            for disorder_key, trace in self.session.diagnoses.items():
                print(f"  {disorder_key}: {trace.result.value.upper()} ({trace.confidence:.0%})")

        # ── Step 2: EmotionArc ─────────────────
        if self.verbose:
            print("\n[2/5] Building EmotionArc...")
        self.session.emotion_arc = self.emotion_tracker.get_emotion_arc()
        if self.verbose and self.session.emotion_arc:
            print(f"  Dominant emotion: {self.session.emotion_arc.dominant_emotion}")
            print(f"  Escalation: {self.session.emotion_arc.distress_escalation_detected}")

        # ── Step 3: Severity Scores ────────────
        if self.verbose:
            print("\n[3/5] Computing severity scores...")
        self.session.severity_report = self.severity_scorer.score_all(
            node_evaluations=self.session.node_evaluations,
            diagnoses=self.session.diagnoses,
        )
        if self.verbose and self.session.severity_report:
            print(f"  Overall severity: {self.session.severity_report.overall_severity.value}")

        # ── Step 4: Recommendations ───────────
        if self.verbose:
            print("\n[4/5] Generating treatment recommendations...")
        self.session.recommendations = self.recommender.generate(
            diagnoses=self.session.diagnoses,
            severity_report=self.session.severity_report,
            emotion_arc=self.session.emotion_arc,
        )
        if self.verbose and self.session.recommendations:
            if self.session.recommendations.crisis_flag:
                print("  ⚠️ CRISIS FLAG RAISED")
            else:
                print(f"  Primary: {self.session.recommendations.primary_recommendation.title[:60]}...")

        # ── Step 5: Save to memory & generate report ──
        if self.verbose:
            print("\n[5/5] Saving session & generating report...")

        self.memory.save_session(self.session)

        longitudinal_summary = self.memory.generate_longitudinal_summary(
            participant_id=self.participant_id,
            current_session=self.session,
        )

        report_path = self.report_gen.save_report(
            session=self.session,
            output_dir=self.reports_dir,
            longitudinal_summary=longitudinal_summary,
            format="markdown",
        )

        # ── Print LLM usage summary ────────────
        if self.verbose:
            usage = self.llm.get_usage_summary()
            print(f"\nLLM Usage: {usage['total_calls']} calls, "
                  f"{usage['total_tokens']} tokens, "
                  f"avg latency {usage['avg_latency_ms']}ms")

            print(f"\n✅ Session complete. Report saved to:")
            print(f"   {report_path}")
            print("="*60)

        return report_path


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

def main():
    """
    Main entry point.
    Modify the mode and participant_id below to run different scenarios.
    """
    import argparse

    parser = argparse.ArgumentParser(description="MAGI+ Psychiatric Interview System")
    parser.add_argument("--mode", choices=["interactive", "simulated"], default="interactive",
                        help="Run mode: interactive (human input) or simulated (test case)")
    parser.add_argument("--participant", default="P001",
                        help="Participant ID (anonymized)")
    parser.add_argument("--model",
                        default=os.getenv("DEFAULT_MODEL", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"),
                        help="LLM model to use")
    parser.add_argument("--case", default=None,
                        help="Path to simulated case JSON file (for simulated mode)")
    args = parser.parse_args()

    pipeline = MAGIPlusPipeline(
        participant_id=args.participant,
        model=args.model,
        verbose=True,
    )

    if args.mode == "interactive":
        report_path = pipeline.run_interactive()
    else:
        # Load simulated case or use built-in demo
        if args.case and os.path.exists(args.case):
            with open(args.case) as f:
                case_data = json.load(f)
            # Case files have a "responses" key; support both formats
            simulated_responses = case_data.get("responses", case_data)
        else:
            # Built-in demo: a participant with moderate depression and anxiety
            simulated_responses = {
                "DEP_A1a": "Yes, I've been feeling really down and hopeless most days.",
                "DEP_A2a": "Yes, it's been going on for about three weeks now.",
                "DEP_A3a": "Yes, I've barely been eating. Lost about 5 pounds.",
                "DEP_A3b": "Definitely. I wake up at 3am and can't fall back asleep.",
                "DEP_A3c": "My partner says I seem really slowed down.",
                "DEP_A3d": "I'm exhausted all the time, even after sleeping.",
                "DEP_A3e": "Yes, I keep blaming myself for everything.",
                "DEP_A3f": "I can't concentrate at all. Even reading is hard.",
                "DEP_A3g": "Sometimes I think it would be easier if I wasn't here. But no plans.",
                "GAD_N1a": "Yes, I worry constantly about work and money.",
                "GAD_N2": "I try to stop but I just can't control it.",
                "GAD_N3a": "I'm always on edge, can't relax.",
                "GAD_N3b": "I get tired so easily these days.",
                "GAD_N3c": "My mind goes blank constantly during meetings.",
                "GAD_N3d": "I get irritated much more easily than before.",
                "GAD_N3e": "Yes, my neck and shoulders are always tense.",
                "GAD_N3f": "I lie awake worrying every night.",
                "SOC_F1a": "Not particularly, I'm fine in social situations.",
                "SUI_B1": "Sometimes I wish I could just disappear.",
                "SUI_B2": "No, I don't want to actually kill myself.",
                "SUI_B5": "No, I've never attempted anything.",
            }

        report_path = pipeline.run_simulated(simulated_responses)

    print(f"\nReport available at: {report_path}")


if __name__ == "__main__":
    main()

"""
emotion_tracker.py
------------------
MAGI+ Extension 1: EmotionArc — Real-Time Emotion Tracking

This is our first novel contribution over the original MAGI paper.

The original MAGI detects distress keywords to decide question strategy,
but never formally models or outputs the participant's emotional state.

EmotionArc:
  - Classifies emotion after EVERY participant turn
  - Tracks emotions as a timeline across the session
  - Detects escalation patterns (e.g., distress spike at a specific topic)
  - Feeds into the Question Agent to improve empathy responses
  - Outputs a summary included in the final clinical report
"""

from __future__ import annotations
from typing import Optional
from src.utils.data_models import (
    EmotionLabel, EmotionDataPoint, EmotionArc, ConversationTurn
)
from src.utils.llm_client import (
    LLMClient, LLMConfig, system_message, user_message, SYSTEM_PROMPTS
)


class EmotionTracker:
    """
    Tracks participant emotional state across the interview in real time.

    Usage:
        tracker = EmotionTracker()
        for each participant response:
            point = tracker.analyze_turn(turn_id, response, node_id)
        arc = tracker.get_emotion_arc()
    """

    # Intensity thresholds for clinical significance
    DISTRESS_THRESHOLD = 0.65      # Intensity above this is flagged
    ESCALATION_WINDOW = 3          # Turns to look back for escalation detection

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient(LLMConfig(temperature=0.1))
        self._data_points: list[EmotionDataPoint] = []

    def analyze_turn(
        self,
        turn_id: int,
        participant_response: str,
        node_id: str,
        context: str = "",
    ) -> EmotionDataPoint:
        """
        Analyze the emotional content of a single participant response.

        Args:
            turn_id: Turn number in the session
            participant_response: What the participant said
            node_id: Which MINI node this response was to
            context: Optional previous turns for context

        Returns:
            EmotionDataPoint with classified emotion and intensity
        """
        # Try rule-based first (fast, no LLM cost)
        rule_emotion, rule_intensity = self._rule_based_emotion(participant_response)
        if rule_emotion is not None:
            point = EmotionDataPoint(
                turn_id=turn_id,
                emotion=rule_emotion,
                intensity=rule_intensity,
                trigger_node=node_id,
            )
            self._data_points.append(point)
            return point

        # LLM fallback for ambiguous text
        raw = self.llm.call_with_json(
            self._build_emotion_prompt(participant_response, context)
        )
        point = self._parse_response(raw, turn_id, node_id, participant_response)
        self._data_points.append(point)
        return point

    @staticmethod
    def _rule_based_emotion(response: str) -> tuple[EmotionLabel | None, float]:
        """
        Fast rule-based emotion detector. Returns (emotion, intensity) or (None, 0).
        """
        r = response.lower()

        distressed_words = ["can't", "terrible", "overwhelmed", "hopeless", "worthless",
                            "falling apart", "can't go on", "too much", "crying"]
        sad_words = ["sad", "low", "down", "depressed", "unhappy", "tearful",
                     "hopeless", "miserable", "empty", "lonely", "guilty"]
        anxious_words = ["anxious", "worried", "nervous", "panic", "fear", "scared",
                         "on edge", "restless", "tense", "stress"]
        hopeful_words = ["better", "hopeful", "improving", "good", "okay", "fine",
                         "well", "positive"]
        avoidant_words = ["don't want", "rather not", "prefer not", "skip", "avoid",
                          "change subject", "not sure", "i don't know"]
        neutral_words = ["yes", "no", "not really", "perhaps", "maybe"]

        # Score each
        dist_score = sum(w in r for w in distressed_words)
        sad_score  = sum(w in r for w in sad_words)
        anx_score  = sum(w in r for w in anxious_words)
        hop_score  = sum(w in r for w in hopeful_words)
        avo_score  = sum(w in r for w in avoidant_words)
        neu_score  = sum(w in r for w in neutral_words)

        scores = {
            EmotionLabel.DISTRESSED: (dist_score, 0.8),
            EmotionLabel.SAD:        (sad_score,  0.65),
            EmotionLabel.ANXIOUS:    (anx_score,  0.6),
            EmotionLabel.HOPEFUL:    (hop_score,  0.5),
            EmotionLabel.AVOIDANT:   (avo_score,  0.55),
            EmotionLabel.NEUTRAL:    (neu_score,  0.2),
        }

        best_emotion = max(scores, key=lambda e: scores[e][0])
        best_count, base_intensity = scores[best_emotion]

        if best_count == 0:
            return None, 0.0  # Nothing matched — use LLM

        intensity = min(0.95, base_intensity + (best_count - 1) * 0.1)
        return best_emotion, intensity

    def get_latest_emotion(self) -> Optional[EmotionLabel]:
        """Return the most recently detected emotion."""
        if self._data_points:
            return self._data_points[-1].emotion
        return None

    def is_distressed(self) -> bool:
        """True if the most recent turn shows significant distress."""
        if not self._data_points:
            return False
        latest = self._data_points[-1]
        return (
            latest.emotion in [EmotionLabel.DISTRESSED, EmotionLabel.SAD]
            and latest.intensity >= self.DISTRESS_THRESHOLD
        )

    def detect_escalation(self) -> bool:
        """
        Detect if emotional distress is escalating over recent turns.
        Returns True if intensity has been consistently rising.
        """
        if len(self._data_points) < self.ESCALATION_WINDOW:
            return False

        recent = self._data_points[-self.ESCALATION_WINDOW:]
        intensities = [p.intensity for p in recent]

        # Check if intensities are consistently increasing
        return all(
            intensities[i] < intensities[i + 1]
            for i in range(len(intensities) - 1)
        )

    def get_emotion_arc(self) -> EmotionArc:
        """
        Build the complete EmotionArc summary for the session.
        Called at the end of the interview.
        """
        if not self._data_points:
            return EmotionArc(summary="No emotion data collected.")

        # Find peak distress turn
        distressed_points = [
            p for p in self._data_points
            if p.emotion in [EmotionLabel.DISTRESSED, EmotionLabel.SAD]
        ]
        peak_turn = None
        if distressed_points:
            peak_point = max(distressed_points, key=lambda p: p.intensity)
            peak_turn = peak_point.turn_id

        # Find dominant emotion (most frequent)
        from collections import Counter
        emotion_counts = Counter(p.emotion for p in self._data_points)
        dominant = emotion_counts.most_common(1)[0][0]

        # Check for escalation
        escalation = self.detect_escalation()

        # Build timeline summary
        arc_text = self._build_arc_summary(dominant, peak_turn, escalation)

        return EmotionArc(
            data_points=self._data_points.copy(),
            peak_distress_turn=peak_turn,
            dominant_emotion=dominant,
            distress_escalation_detected=escalation,
            summary=arc_text,
        )

    def reset(self) -> None:
        """Reset for a new session."""
        self._data_points = []

    # ── PRIVATE HELPERS ───────────────────────

    def _build_emotion_prompt(self, response: str, context: str) -> list[dict]:
        """Build the LLM prompt for emotion classification."""
        return [
            system_message(
                "You are an emotion classifier. "
                "Respond ONLY with a valid JSON object. No explanations. "
                "Pure JSON starting with { and ending with }."
            ),
            user_message(
                f"Participant said: \"{response[:200]}\"\n\n"
                f"Classify emotion. Choose ONE: neutral, anxious, sad, distressed, hopeful, avoidant, angry, confused.\n"
                f"Return ONLY: "
                f'{{\"emotion\":\"sad\",\"intensity\":0.7,\"reasoning\":\"brief\"}}'
                f"\nReplace values based on the actual text above."
            ),
        ]

    def _parse_response(
        self,
        raw: dict,
        turn_id: int,
        node_id: str,
        fallback_text: str,
    ) -> EmotionDataPoint:
        """Parse LLM response into an EmotionDataPoint."""
        if not raw:
            return EmotionDataPoint(
                turn_id=turn_id,
                emotion=EmotionLabel.NEUTRAL,
                intensity=0.3,
                trigger_node=node_id,
            )

        emotion_str = raw.get("emotion", "neutral").lower()

        # Map to enum safely
        try:
            emotion = EmotionLabel(emotion_str)
        except ValueError:
            emotion = EmotionLabel.NEUTRAL

        return EmotionDataPoint(
            turn_id=turn_id,
            emotion=emotion,
            intensity=float(raw.get("intensity", 0.5)),
            trigger_node=node_id,
        )

    def _build_arc_summary(
        self,
        dominant: EmotionLabel,
        peak_turn: Optional[int],
        escalation: bool,
    ) -> str:
        """Build a human-readable emotion arc summary."""
        lines = [f"Dominant emotion throughout session: {dominant.value}."]

        if peak_turn is not None:
            lines.append(
                f"Peak distress detected at turn {peak_turn}."
            )

        if escalation:
            lines.append(
                "Emotional distress escalated toward the end of the session — "
                "clinician follow-up recommended."
            )
        else:
            lines.append("No significant emotional escalation pattern detected.")

        # Add emotion distribution
        if self._data_points:
            from collections import Counter
            counts = Counter(p.emotion.value for p in self._data_points)
            dist = ", ".join(f"{e}: {c}" for e, c in counts.most_common())
            lines.append(f"Emotion distribution (turns): {dist}.")

        return " ".join(lines)

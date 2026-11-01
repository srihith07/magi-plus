"""
data_models.py
--------------
Core data structures for the MAGI+ system.
All data flowing through the system is represented by these Pydantic models.
This ensures type safety, easy serialization, and clear documentation.
"""

from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


# ─────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────

class Disorder(str, Enum):
    """Psychiatric disorders covered by our MINI implementation."""
    DEPRESSION = "depression"
    GENERALIZED_ANXIETY = "generalized_anxiety"
    SOCIAL_ANXIETY = "social_anxiety"
    SUICIDE_RISK = "suicide_risk"


class DiagnosisResult(str, Enum):
    """Outcome of a diagnostic evaluation for a disorder."""
    YES = "yes"           # Disorder criteria met
    NO = "no"             # Disorder criteria not met
    UNCERTAIN = "uncertain"  # Insufficient evidence


class SeverityLevel(str, Enum):
    """Clinical severity tiers (aligns with PHQ-9 / GAD-7 conventions)."""
    NONE = "none"
    MINIMAL = "minimal"
    MILD = "mild"
    MODERATE = "moderate"
    MODERATELY_SEVERE = "moderately_severe"
    SEVERE = "severe"


class EmotionLabel(str, Enum):
    """Emotion categories tracked per conversational turn."""
    NEUTRAL = "neutral"
    ANXIOUS = "anxious"
    SAD = "sad"
    DISTRESSED = "distressed"
    HOPEFUL = "hopeful"
    AVOIDANT = "avoidant"
    ANGRY = "angry"
    CONFUSED = "confused"


class QuestionStrategy(str, Enum):
    """Strategy the Question Agent uses to phrase a question."""
    PROBE = "probe"          # Standard diagnostic probing
    EXPLAIN = "explain"      # Clarify a clinical concept
    EMPATHIZE = "empathize"  # Emotional support response


class NodeStatus(str, Enum):
    """Status of a MINI interview tree node."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class RecommendationTier(str, Enum):
    """Tiers of clinical recommendations based on severity."""
    SELF_HELP = "self_help"
    OUTPATIENT_THERAPY = "outpatient_therapy"
    PSYCHIATRIC_CONSULTATION = "psychiatric_consultation"
    CRISIS_INTERVENTION = "crisis_intervention"


# ─────────────────────────────────────────────
# CONVERSATION TURN
# ─────────────────────────────────────────────

class ConversationTurn(BaseModel):
    """A single exchange in the interview (one question + one answer)."""
    turn_id: int
    node_id: str                          # Which MINI node this turn belongs to
    agent_utterance: str                  # What the AI said
    participant_response: str             # What the participant said
    strategy_used: QuestionStrategy       # How the question was framed
    emotion_detected: Optional[EmotionLabel] = None  # EmotionArc (our extension)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────────
# NODE EVALUATION
# ─────────────────────────────────────────────

class NodeEvaluation(BaseModel):
    """Judgment Agent's evaluation of a MINI tree node."""
    node_id: str
    node_label: str                       # Human-readable name (e.g., "Depressed mood")
    status: NodeStatus
    criterion_met: Optional[bool] = None  # True / False / None (uncertain)
    evidence: str = ""                    # Relevant quote from participant
    turns_taken: int = 0                  # How many turns to complete this node


# ─────────────────────────────────────────────
# PSYCOT REASONING TRACE
# ─────────────────────────────────────────────

class PsyCoTTrace(BaseModel):
    """
    Psychometric Chain-of-Thought reasoning trace produced by the Diagnosis Agent.
    Mirrors the 3-phase structure from the original MAGI paper.
    """
    disorder: Disorder

    # Phase 1: Symptom Anchoring
    symptoms_confirmed: list[str] = Field(default_factory=list)
    symptoms_denied: list[str] = Field(default_factory=list)
    temporal_verification: str = ""       # e.g., "Symptoms present for >2 weeks"
    exclusion_checks: str = ""            # e.g., "Not substance-induced"

    # Phase 2: Diagnostic Synthesis
    criteria_met_count: int = 0
    criteria_required: int = 0
    threshold_passed: bool = False

    # Phase 3: Evidence Binding
    key_evidence: list[str] = Field(default_factory=list)  # Quotes from dialogue
    reasoning_summary: str = ""

    # Final outcome
    result: DiagnosisResult = DiagnosisResult.UNCERTAIN
    confidence: float = 0.0              # 0.0 – 1.0


# ─────────────────────────────────────────────
# SEVERITY SCORES (OUR EXTENSION)
# ─────────────────────────────────────────────

class PHQ9Score(BaseModel):
    """PHQ-9 Depression severity score (0–27)."""
    score: int = 0
    severity: SeverityLevel = SeverityLevel.NONE
    item_scores: dict[str, int] = Field(default_factory=dict)  # Per-item breakdown


class GAD7Score(BaseModel):
    """GAD-7 Anxiety severity score (0–21)."""
    score: int = 0
    severity: SeverityLevel = SeverityLevel.NONE
    item_scores: dict[str, int] = Field(default_factory=dict)


class CSSRSScore(BaseModel):
    """Columbia Suicide Severity Rating Scale."""
    ideation_level: int = 0              # 0–5 (0=none, 5=active with plan+intent)
    behavior_present: bool = False
    severity: SeverityLevel = SeverityLevel.NONE
    risk_category: str = "no_risk"       # no_risk / low / moderate / high / imminent


class SeverityReport(BaseModel):
    """Complete severity assessment output (our Extension 2)."""
    phq9: Optional[PHQ9Score] = None
    gad7: Optional[GAD7Score] = None
    cssrs: Optional[CSSRSScore] = None
    overall_severity: SeverityLevel = SeverityLevel.NONE


# ─────────────────────────────────────────────
# EMOTION ARC (OUR EXTENSION)
# ─────────────────────────────────────────────

class EmotionDataPoint(BaseModel):
    """A single emotion measurement at a specific turn."""
    turn_id: int
    emotion: EmotionLabel
    intensity: float = 0.5               # 0.0 (low) to 1.0 (high)
    trigger_node: Optional[str] = None   # Which MINI node triggered this


class EmotionArc(BaseModel):
    """Complete emotion timeline for a session (our Extension 1)."""
    data_points: list[EmotionDataPoint] = Field(default_factory=list)
    peak_distress_turn: Optional[int] = None
    dominant_emotion: Optional[EmotionLabel] = None
    distress_escalation_detected: bool = False
    summary: str = ""


# ─────────────────────────────────────────────
# TREATMENT RECOMMENDATION (OUR EXTENSION)
# ─────────────────────────────────────────────

class TreatmentRecommendation(BaseModel):
    """A single evidence-based treatment recommendation."""
    tier: RecommendationTier
    title: str
    description: str
    resources: list[str] = Field(default_factory=list)  # Links / names
    urgency: str = "routine"             # routine / soon / urgent / immediate


class RecommendationOutput(BaseModel):
    """Full output of the Recommendation Agent (our Extension 3)."""
    primary_recommendation: TreatmentRecommendation
    additional_recommendations: list[TreatmentRecommendation] = Field(default_factory=list)
    crisis_flag: bool = False
    crisis_message: str = ""
    disclaimer: str = (
        "This is an AI-assisted assessment. These recommendations are not a "
        "substitute for professional clinical evaluation. Please consult a "
        "licensed mental health professional."
    )


# ─────────────────────────────────────────────
# FULL SESSION
# ─────────────────────────────────────────────

class InterviewSession(BaseModel):
    """
    The complete record of one MAGI+ interview session.
    This is the central data structure — everything flows in and out of this.
    """
    session_id: str
    participant_id: str                  # Anonymized ID
    session_number: int = 1             # 1 for first session, increments after
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    # Interview content
    conversation: list[ConversationTurn] = Field(default_factory=list)
    node_evaluations: list[NodeEvaluation] = Field(default_factory=list)

    # Diagnoses (one per disorder screened)
    diagnoses: dict[str, PsyCoTTrace] = Field(default_factory=dict)

    # Our extensions
    emotion_arc: Optional[EmotionArc] = None          # Extension 1
    severity_report: Optional[SeverityReport] = None  # Extension 2
    recommendations: Optional[RecommendationOutput] = None  # Extension 3

    # Metadata
    llm_model_used: str = "gpt-4o"
    total_turns: int = 0
    duration_minutes: Optional[float] = None

    def add_turn(self, turn: ConversationTurn) -> None:
        """Add a conversation turn and update the turn count."""
        self.conversation.append(turn)
        self.total_turns = len(self.conversation)

    def get_diagnosis(self, disorder: Disorder) -> Optional[PsyCoTTrace]:
        """Retrieve the diagnosis trace for a specific disorder."""
        return self.diagnoses.get(disorder.value)

    def is_crisis(self) -> bool:
        """Check if this session flagged a crisis situation."""
        if self.recommendations:
            return self.recommendations.crisis_flag
        return False


# ─────────────────────────────────────────────
# LONGITUDINAL RECORD (OUR EXTENSION)
# ─────────────────────────────────────────────

class SessionSummary(BaseModel):
    """Condensed summary of a session for longitudinal comparison."""
    session_id: str
    session_number: int
    date: datetime
    diagnoses: dict[str, str]            # disorder → "yes"/"no"/"uncertain"
    severity_overall: str
    phq9_score: Optional[int] = None
    gad7_score: Optional[int] = None
    dominant_emotion: Optional[str] = None


class LongitudinalRecord(BaseModel):
    """
    Multi-session history for a single participant (our Extension 4).
    Tracks progress and trends across all sessions.
    """
    participant_id: str
    sessions: list[SessionSummary] = Field(default_factory=list)
    trend_depression: Optional[str] = None     # improving / stable / worsening
    trend_anxiety: Optional[str] = None
    trend_suicide_risk: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    def add_session(self, summary: SessionSummary) -> None:
        self.sessions.append(summary)
        self.sessions.sort(key=lambda s: s.session_number)
        self.last_updated = datetime.utcnow()

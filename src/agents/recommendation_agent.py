"""
recommendation_agent.py
-----------------------
MAGI+ Extension 3: The Recommendation Agent (5th Agent)

This is our most impactful novel contribution. The original MAGI stops at
diagnosis. Real clinical practice always follows diagnosis with a treatment plan.

The Recommendation Agent:
  - Takes: diagnosis results + severity scores + emotion arc
  - Outputs: tiered, evidence-based treatment recommendations
  - Handles: crisis escalation for high suicide risk (immediate referral)

Recommendation Tiers (based on APA, WHO, NICE guidelines):
  SELF_HELP              — mild cases (apps, psychoeducation, exercises)
  OUTPATIENT_THERAPY     — moderate cases (CBT, DBT, counseling)
  PSYCHIATRIC_CONSULT    — moderate-severe (medication evaluation)
  CRISIS_INTERVENTION    — severe suicide risk (immediate action required)
"""

from __future__ import annotations
from typing import Optional
from src.utils.data_models import (
    Disorder, DiagnosisResult, SeverityLevel, SeverityReport,
    PsyCoTTrace, EmotionArc, TreatmentRecommendation,
    RecommendationOutput, RecommendationTier
)
from src.utils.llm_client import (
    LLMClient, LLMConfig, system_message, user_message, SYSTEM_PROMPTS
)


# ─────────────────────────────────────────────
# KNOWLEDGE BASE (Evidence-based recommendations)
# ─────────────────────────────────────────────

TREATMENT_KNOWLEDGE_BASE = {
    Disorder.DEPRESSION: {
        SeverityLevel.MINIMAL: TreatmentRecommendation(
            tier=RecommendationTier.SELF_HELP,
            title="Lifestyle & Self-Help for Low-Level Depressive Symptoms",
            description=(
                "Your responses suggest minimal depressive symptoms. "
                "Lifestyle adjustments and psychoeducation are recommended "
                "as a first step."
            ),
            resources=[
                "Woebot (CBT-based app) — woebot.io",
                "MoodTools app (PHQ-9 tracker + behavioral activation)",
                "WHO: Living with Depression guide",
                "Behavioral Activation worksheet (free PDF, Psychology Tools)",
                "Regular physical exercise (30 min/day, 5 days/week — evidence-based)",
            ],
            urgency="routine",
        ),
        SeverityLevel.MILD: TreatmentRecommendation(
            tier=RecommendationTier.SELF_HELP,
            title="Self-Guided CBT & Psychoeducation for Mild Depression",
            description=(
                "Mild depression is highly responsive to structured self-help. "
                "Cognitive Behavioral Therapy (CBT) techniques and behavioral "
                "activation are the recommended first-line approaches."
            ),
            resources=[
                "Mind over Mood (book) — Greenberger & Padesky",
                "Beating the Blues (online CBT program) — beatingtheblues.co.uk",
                "Mindfulness-Based Cognitive Therapy (MBCT) resources",
                "Exercise prescription: aerobic exercise 3x/week",
                "Sleep hygiene protocol (CBT-I)",
            ],
            urgency="routine",
        ),
        SeverityLevel.MODERATE: TreatmentRecommendation(
            tier=RecommendationTier.OUTPATIENT_THERAPY,
            title="Outpatient Psychotherapy for Moderate Depression",
            description=(
                "Moderate depression typically requires structured psychotherapy. "
                "Cognitive Behavioral Therapy (CBT) is the gold-standard "
                "first-line treatment."
            ),
            resources=[
                "Cognitive Behavioral Therapy (CBT) — 12-20 sessions",
                "Behavioral Activation Therapy",
                "Interpersonal Therapy (IPT)",
                "BetterHelp / Talkspace (online therapy platforms)",
                "Find a local therapist: Psychology Today directory",
                "Consider GP consultation about antidepressant options if therapy alone insufficient",
            ],
            urgency="soon",
        ),
        SeverityLevel.MODERATELY_SEVERE: TreatmentRecommendation(
            tier=RecommendationTier.PSYCHIATRIC_CONSULTATION,
            title="Psychiatric Consultation for Moderately Severe Depression",
            description=(
                "This severity level typically requires a combination of "
                "psychotherapy and pharmacotherapy. A psychiatrist evaluation "
                "is strongly recommended."
            ),
            resources=[
                "Psychiatrist evaluation — consider antidepressant medication",
                "Concurrent CBT/DBT with medication",
                "SSRI/SNRI first-line medications (under medical supervision)",
                "Crisis line: 988 Suicide & Crisis Lifeline (call/text 988)",
            ],
            urgency="urgent",
        ),
        SeverityLevel.SEVERE: TreatmentRecommendation(
            tier=RecommendationTier.PSYCHIATRIC_CONSULTATION,
            title="Urgent Psychiatric Care for Severe Depression",
            description=(
                "Severe depression requires prompt psychiatric intervention. "
                "Please contact a mental health professional as soon as possible."
            ),
            resources=[
                "Immediate psychiatrist or GP referral",
                "Emergency mental health services if safety is a concern",
                "988 Suicide & Crisis Lifeline",
                "Consider intensive outpatient program (IOP)",
            ],
            urgency="urgent",
        ),
    },

    Disorder.GENERALIZED_ANXIETY: {
        SeverityLevel.MINIMAL: TreatmentRecommendation(
            tier=RecommendationTier.SELF_HELP,
            title="Anxiety Management Techniques for Low-Level Worry",
            description=(
                "Minimal anxiety symptoms can be effectively managed with "
                "self-help relaxation and mindfulness techniques."
            ),
            resources=[
                "Calm or Headspace app (mindfulness meditation)",
                "Diaphragmatic breathing exercises (4-7-8 technique)",
                "Progressive Muscle Relaxation (PMR) guide",
                "Worry time scheduling technique",
            ],
            urgency="routine",
        ),
        SeverityLevel.MILD: TreatmentRecommendation(
            tier=RecommendationTier.SELF_HELP,
            title="Self-Guided CBT for Mild Generalized Anxiety",
            description=(
                "Mild GAD responds well to self-guided CBT and relaxation "
                "training. Focus on challenging worry thoughts and reducing "
                "avoidance."
            ),
            resources=[
                "The Anxiety and Worry Workbook — Clark & Beck",
                "Worry Well app",
                "Mindfulness-Based Stress Reduction (MBSR) program",
                "Limiting caffeine and alcohol (evidence-based lifestyle change)",
            ],
            urgency="routine",
        ),
        SeverityLevel.MODERATE: TreatmentRecommendation(
            tier=RecommendationTier.OUTPATIENT_THERAPY,
            title="Outpatient CBT for Moderate Generalized Anxiety",
            description=(
                "Moderate GAD is best treated with structured CBT. "
                "12-20 sessions are typically recommended."
            ),
            resources=[
                "CBT for GAD (12-20 sessions with a licensed therapist)",
                "Acceptance and Commitment Therapy (ACT)",
                "Online CBT: IESO Digital Health, SilverCloud",
                "Discuss medication (buspirone, SSRIs) with GP if needed",
            ],
            urgency="soon",
        ),
        SeverityLevel.SEVERE: TreatmentRecommendation(
            tier=RecommendationTier.PSYCHIATRIC_CONSULTATION,
            title="Psychiatric Consultation for Severe Anxiety",
            description=(
                "Severe GAD often requires combined treatment. "
                "Psychiatric evaluation for pharmacotherapy is recommended."
            ),
            resources=[
                "Psychiatrist evaluation — SSRI/SNRI or buspirone",
                "Concurrent CBT",
                "Anxiety & Depression Association of America (ADAA): adaa.org",
            ],
            urgency="urgent",
        ),
    },

    Disorder.SOCIAL_ANXIETY: {
        SeverityLevel.MILD: TreatmentRecommendation(
            tier=RecommendationTier.SELF_HELP,
            title="Gradual Exposure for Mild Social Anxiety",
            description=(
                "Mild social anxiety responds well to gradual exposure "
                "techniques and self-help CBT."
            ),
            resources=[
                "The Shyness and Social Anxiety Workbook — Antony & Swinson",
                "Virtual exposure exercises (video calls, online groups)",
                "Toastmasters International (public speaking practice)",
            ],
            urgency="routine",
        ),
        SeverityLevel.MODERATE: TreatmentRecommendation(
            tier=RecommendationTier.OUTPATIENT_THERAPY,
            title="CBT with Exposure Therapy for Social Anxiety",
            description=(
                "Cognitive Behavioral Therapy with structured exposure is "
                "the gold-standard treatment for social anxiety disorder."
            ),
            resources=[
                "CBT with in-vivo exposure (therapist-guided)",
                "Group CBT for social anxiety (highly effective)",
                "Social skills training",
                "Online: Anxiety Canada MindShift app",
            ],
            urgency="soon",
        ),
        SeverityLevel.SEVERE: TreatmentRecommendation(
            tier=RecommendationTier.PSYCHIATRIC_CONSULTATION,
            title="Combined Treatment for Severe Social Anxiety",
            description=(
                "Severe social anxiety disorder may require combined "
                "psychotherapy and pharmacotherapy."
            ),
            resources=[
                "Psychiatrist evaluation — SSRIs (sertraline, paroxetine)",
                "Intensive CBT with exposure",
                "Social Anxiety Institute: socialanxietyinstitute.org",
            ],
            urgency="urgent",
        ),
    },

    Disorder.SUICIDE_RISK: {
        SeverityLevel.MILD: TreatmentRecommendation(
            tier=RecommendationTier.OUTPATIENT_THERAPY,
            title="Safety Planning & Outpatient Support for Low Suicide Risk",
            description=(
                "Passive suicidal ideation detected. A safety plan and "
                "regular therapeutic contact are recommended."
            ),
            resources=[
                "Safety Planning Intervention (SPI) — stanleybrownsafetyplanning.com",
                "988 Suicide & Crisis Lifeline (call or text 988)",
                "Crisis Text Line — text HOME to 741741",
                "Schedule appointment with therapist or counselor soon",
            ],
            urgency="soon",
        ),
        SeverityLevel.MODERATE: TreatmentRecommendation(
            tier=RecommendationTier.PSYCHIATRIC_CONSULTATION,
            title="Psychiatric Consultation for Moderate Suicide Risk",
            description=(
                "Active suicidal ideation detected. Psychiatric evaluation "
                "is required promptly."
            ),
            resources=[
                "Immediate psychiatric or emergency GP consultation",
                "988 Suicide & Crisis Lifeline",
                "Remove access to lethal means (standard safety protocol)",
                "Dialectical Behavior Therapy (DBT) for chronic ideation",
            ],
            urgency="urgent",
        ),
        SeverityLevel.SEVERE: TreatmentRecommendation(
            tier=RecommendationTier.CRISIS_INTERVENTION,
            title="⚠️ CRISIS INTERVENTION — Immediate Action Required",
            description=(
                "High suicide risk detected (active plan and/or intent). "
                "This requires immediate professional intervention."
            ),
            resources=[
                "CALL 988 (Suicide & Crisis Lifeline) NOW",
                "Go to nearest emergency room or call 911",
                "Crisis Text Line: text HOME to 741741",
                "Do not leave the person alone",
                "Remove access to all lethal means immediately",
            ],
            urgency="immediate",
        ),
    },
}


# ─────────────────────────────────────────────
# RECOMMENDATION AGENT
# ─────────────────────────────────────────────

class RecommendationAgent:
    """
    The 5th agent in MAGI+. Generates evidence-based treatment recommendations
    from diagnosis results and severity scores.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient(LLMConfig(temperature=0.4))

    def generate(
        self,
        diagnoses: dict[str, PsyCoTTrace],
        severity_report: SeverityReport,
        emotion_arc: Optional[EmotionArc] = None,
    ) -> RecommendationOutput:
        """
        Generate treatment recommendations for all active diagnoses.

        Args:
            diagnoses: Dict of disorder → PsyCoTTrace from DiagnosisAgent
            severity_report: Severity scores from SeverityScorer
            emotion_arc: Optional emotion timeline from EmotionTracker

        Returns:
            RecommendationOutput with tiered recommendations and crisis flag
        """
        active_diagnoses = {
            k: v for k, v in diagnoses.items()
            if v.result == DiagnosisResult.YES
        }

        # ── Crisis check first (highest priority) ──────────────
        crisis_flag, crisis_message = self._check_crisis(
            severity_report, active_diagnoses
        )

        if crisis_flag:
            primary = TREATMENT_KNOWLEDGE_BASE[Disorder.SUICIDE_RISK][SeverityLevel.SEVERE]
            return RecommendationOutput(
                primary_recommendation=primary,
                additional_recommendations=[],
                crisis_flag=True,
                crisis_message=crisis_message,
            )

        # ── Build recommendations for each active diagnosis ─────
        all_recommendations: list[TreatmentRecommendation] = []

        # Prioritize by severity
        disorder_severity_pairs = self._rank_by_severity(
            active_diagnoses, severity_report
        )

        for disorder, severity in disorder_severity_pairs:
            rec = self._get_recommendation(disorder, severity)
            if rec:
                all_recommendations.append(rec)

        # If no active diagnoses
        if not all_recommendations:
            return self._generate_no_diagnosis_response()

        # Personalize the primary recommendation using LLM
        primary = self._personalize(all_recommendations[0], emotion_arc)

        return RecommendationOutput(
            primary_recommendation=primary,
            additional_recommendations=all_recommendations[1:],
            crisis_flag=False,
        )

    # ── PRIVATE HELPERS ───────────────────────

    def _check_crisis(
        self,
        severity_report: SeverityReport,
        active_diagnoses: dict,
    ) -> tuple[bool, str]:
        """
        Check for crisis-level suicide risk requiring immediate intervention.
        Returns (is_crisis, crisis_message).
        """
        if not severity_report.cssrs:
            return False, ""

        cssrs = severity_report.cssrs

        # Imminent or high risk → crisis
        if cssrs.risk_category in ("imminent", "high") or cssrs.ideation_level >= 4:
            return True, (
                "⚠️ HIGH SUICIDE RISK DETECTED. "
                "Active suicidal ideation with plan and/or intent identified. "
                "Immediate professional intervention is required. "
                "Please call 988 or go to the nearest emergency room."
            )

        # Active ideation with past attempt → elevated crisis concern
        if cssrs.ideation_level >= 2 and cssrs.behavior_present:
            return True, (
                "⚠️ ELEVATED SUICIDE RISK. "
                "Active ideation combined with history of suicide attempt detected. "
                "Urgent psychiatric consultation is required within 24 hours."
            )

        return False, ""

    def _rank_by_severity(
        self,
        active_diagnoses: dict[str, PsyCoTTrace],
        severity_report: SeverityReport,
    ) -> list[tuple[Disorder, SeverityLevel]]:
        """
        Rank active diagnoses from most to least severe.
        Returns list of (disorder, severity_level) tuples.
        """
        severity_order = [
            SeverityLevel.NONE, SeverityLevel.MINIMAL, SeverityLevel.MILD,
            SeverityLevel.MODERATE, SeverityLevel.MODERATELY_SEVERE, SeverityLevel.SEVERE
        ]

        pairs = []
        for disorder_key in active_diagnoses:
            disorder = Disorder(disorder_key)
            severity = self._get_severity_for_disorder(disorder, severity_report)
            pairs.append((disorder, severity))

        return sorted(
            pairs,
            key=lambda p: severity_order.index(p[1]),
            reverse=True
        )

    def _get_severity_for_disorder(
        self,
        disorder: Disorder,
        severity_report: SeverityReport,
    ) -> SeverityLevel:
        """Extract the severity level for a specific disorder."""
        if disorder == Disorder.DEPRESSION and severity_report.phq9:
            return severity_report.phq9.severity
        elif disorder == Disorder.GENERALIZED_ANXIETY and severity_report.gad7:
            return severity_report.gad7.severity
        elif disorder == Disorder.SUICIDE_RISK and severity_report.cssrs:
            return severity_report.cssrs.severity
        elif disorder == Disorder.SOCIAL_ANXIETY:
            return severity_report.overall_severity
        return SeverityLevel.MILD  # Fallback

    def _get_recommendation(
        self,
        disorder: Disorder,
        severity: SeverityLevel,
    ) -> Optional[TreatmentRecommendation]:
        """
        Look up the best matching recommendation for disorder + severity.
        Falls back to the closest available severity if exact match not found.
        """
        disorder_recs = TREATMENT_KNOWLEDGE_BASE.get(disorder, {})
        if not disorder_recs:
            return None

        # Try exact match first
        if severity in disorder_recs:
            return disorder_recs[severity]

        # Fallback: find nearest severity with a recommendation
        severity_order = [
            SeverityLevel.MINIMAL, SeverityLevel.MILD,
            SeverityLevel.MODERATE, SeverityLevel.MODERATELY_SEVERE,
            SeverityLevel.SEVERE
        ]
        try:
            idx = severity_order.index(severity)
        except ValueError:
            idx = 1  # Default to mild

        # Search outward from current severity
        for offset in range(1, len(severity_order)):
            for direction in [1, -1]:
                candidate_idx = idx + (offset * direction)
                if 0 <= candidate_idx < len(severity_order):
                    candidate = severity_order[candidate_idx]
                    if candidate in disorder_recs:
                        return disorder_recs[candidate]

        return None

    def _personalize(
        self,
        recommendation: TreatmentRecommendation,
        emotion_arc: Optional[EmotionArc],
    ) -> TreatmentRecommendation:
        """
        Use the LLM to slightly personalize the recommendation text
        based on the emotion arc from the session.
        """
        if not emotion_arc or not emotion_arc.summary:
            return recommendation

        raw = self.llm.call_with_json([
            system_message(
                "You personalize clinical recommendations. "
                "Respond ONLY with valid JSON. No explanations. Pure JSON only."
            ),
            user_message(
                f"Base description: {recommendation.description}\n"
                f"Emotional profile: {emotion_arc.summary[:200]}\n\n"
                f"Return ONLY: "
                f'{{\"personalized_description\":\"your 2-3 sentence personalized version here\"}}'
                f"\nKeep clinical accuracy. Adjust tone to match emotional profile."
            ),
        ])

        if raw and "personalized_description" in raw:
            # Return a copy with updated description
            return TreatmentRecommendation(
                tier=recommendation.tier,
                title=recommendation.title,
                description=raw["personalized_description"],
                resources=recommendation.resources,
                urgency=recommendation.urgency,
            )

        return recommendation

    def _generate_no_diagnosis_response(self) -> RecommendationOutput:
        """Response when no disorders met diagnostic threshold."""
        return RecommendationOutput(
            primary_recommendation=TreatmentRecommendation(
                tier=RecommendationTier.SELF_HELP,
                title="No Clinical Threshold Met — Preventive Wellbeing Recommendations",
                description=(
                    "Your responses did not meet the clinical threshold for any "
                    "of the assessed conditions. This is a positive result. "
                    "The following resources can support ongoing mental wellbeing."
                ),
                resources=[
                    "Headspace or Calm (mindfulness apps) for stress management",
                    "Regular physical exercise (30 min/day)",
                    "Maintaining social connections",
                    "If concerns persist, consider speaking with a counselor",
                ],
                urgency="routine",
            ),
            crisis_flag=False,
        )

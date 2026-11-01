"""
severity_scorer.py
------------------
MAGI+ Extension 2: Standardized Severity Scoring

Original MAGI produces binary Yes/No diagnoses.
We map collected symptoms to validated clinical severity scales:
  - PHQ-9  (Patient Health Questionnaire-9) for Depression
  - GAD-7  (Generalized Anxiety Disorder 7-item scale) for Anxiety
  - C-SSRS (Columbia Suicide Severity Rating Scale) for Suicide Risk
  - LSAS-SR for Social Anxiety (simplified mapping)

This makes the output directly usable in clinical settings and enables
longitudinal severity tracking across sessions.
"""

from __future__ import annotations
from typing import Optional
from src.utils.data_models import (
    Disorder, DiagnosisResult, PsyCoTTrace, SeverityLevel,
    PHQ9Score, GAD7Score, CSSRSScore, SeverityReport, NodeEvaluation
)


# ─────────────────────────────────────────────
# PHQ-9 SCORING LOGIC
# ─────────────────────────────────────────────

# PHQ-9 severity bands (score → severity)
PHQ9_BANDS = [
    (0, 4,   SeverityLevel.MINIMAL),
    (5, 9,   SeverityLevel.MILD),
    (10, 14, SeverityLevel.MODERATE),
    (15, 19, SeverityLevel.MODERATELY_SEVERE),
    (20, 27, SeverityLevel.SEVERE),
]

# Maps MINI node IDs to PHQ-9 items (item_name → max_score)
PHQ9_NODE_MAPPING = {
    "DEP_A1a": ("depressed_mood",         3),
    "DEP_A1b": ("anhedonia",              3),
    "DEP_A3a": ("appetite_change",        3),
    "DEP_A3b": ("sleep_disturbance",      3),
    "DEP_A3c": ("psychomotor_change",     3),
    "DEP_A3d": ("fatigue",                3),
    "DEP_A3e": ("worthlessness_guilt",    3),
    "DEP_A3f": ("concentration",          3),
    "DEP_A3g": ("suicidal_thoughts",      3),
}


# ─────────────────────────────────────────────
# GAD-7 SCORING LOGIC
# ─────────────────────────────────────────────

GAD7_BANDS = [
    (0,  4,  SeverityLevel.MINIMAL),
    (5,  9,  SeverityLevel.MILD),
    (10, 14, SeverityLevel.MODERATE),
    (15, 21, SeverityLevel.SEVERE),
]

GAD7_NODE_MAPPING = {
    "GAD_N3a": ("feeling_nervous",            3),
    "GAD_N3b": ("uncontrollable_worry",       3),
    "GAD_N3c": ("excessive_worrying",         3),
    "GAD_N3d": ("trouble_relaxing",           3),
    "GAD_N3e": ("restlessness",               3),
    "GAD_N3f": ("irritability",               3),
    "GAD_N1a": ("feeling_afraid",             3),
}


# ─────────────────────────────────────────────
# C-SSRS LEVEL MAPPING
# ─────────────────────────────────────────────

# C-SSRS ideation levels (0–5)
CSSRS_IDEATION_MAPPING = {
    "SUI_B1": 1,   # Passive ideation (wish to be dead)
    "SUI_B2": 2,   # Active ideation without plan
    "SUI_B3": 3,   # Active ideation with some plan
    "SUI_B4": 4,   # Active ideation with intent to act
    "SUI_B5": 2,   # Past attempt (adds to risk regardless of current ideation)
}

CSSRS_RISK_CATEGORIES = {
    0: ("no_risk",  SeverityLevel.NONE),
    1: ("low",      SeverityLevel.MILD),
    2: ("low",      SeverityLevel.MILD),
    3: ("moderate", SeverityLevel.MODERATE),
    4: ("high",     SeverityLevel.SEVERE),
    5: ("imminent", SeverityLevel.SEVERE),
}


# ─────────────────────────────────────────────
# SEVERITY SCORER
# ─────────────────────────────────────────────

class SeverityScorer:
    """
    Maps MINI interview results to validated clinical severity scores.
    """

    def score_all(
        self,
        node_evaluations: list[NodeEvaluation],
        diagnoses: dict[str, PsyCoTTrace],
    ) -> SeverityReport:
        """
        Compute all severity scores from interview data.

        Args:
            node_evaluations: List of all node evaluation records
            diagnoses: Dict of disorder → PsyCoTTrace from DiagnosisAgent

        Returns:
            SeverityReport with PHQ-9, GAD-7, C-SSRS scores
        """
        # Build a lookup: node_id → criterion_met (True/False/None)
        node_lookup = {e.node_id: e.criterion_met for e in node_evaluations}

        # Compute individual scores
        phq9 = self._compute_phq9(node_lookup, diagnoses)
        gad7 = self._compute_gad7(node_lookup, diagnoses)
        cssrs = self._compute_cssrs(node_lookup, diagnoses)

        # Determine overall severity (worst of all active diagnoses)
        overall = self._compute_overall_severity(phq9, gad7, cssrs, diagnoses)

        return SeverityReport(
            phq9=phq9,
            gad7=gad7,
            cssrs=cssrs,
            overall_severity=overall,
        )

    # ── PHQ-9 ─────────────────────────────────

    def _compute_phq9(
        self,
        node_lookup: dict[str, Optional[bool]],
        diagnoses: dict[str, PsyCoTTrace],
    ) -> PHQ9Score:
        """Compute PHQ-9 score from depression node evaluations."""
        dep_trace = diagnoses.get(Disorder.DEPRESSION.value)

        # If depression was not diagnosed, return zero score
        if dep_trace and dep_trace.result == DiagnosisResult.NO:
            return PHQ9Score(score=0, severity=SeverityLevel.NONE)

        item_scores = {}
        total = 0

        for node_id, (item_name, max_score) in PHQ9_NODE_MAPPING.items():
            met = node_lookup.get(node_id)
            # Score: 0 if not met/unknown, max_score if met
            # (In a full implementation, scores 0-3 would come from
            # frequency ratings; here we use 0 or max as binary)
            score = max_score if met is True else 0
            item_scores[item_name] = score
            total += score

        # Cap at 27 (max PHQ-9 score)
        total = min(total, 27)
        severity = self._band_lookup(total, PHQ9_BANDS)

        return PHQ9Score(score=total, severity=severity, item_scores=item_scores)

    # ── GAD-7 ─────────────────────────────────

    def _compute_gad7(
        self,
        node_lookup: dict[str, Optional[bool]],
        diagnoses: dict[str, PsyCoTTrace],
    ) -> GAD7Score:
        """Compute GAD-7 score from anxiety node evaluations."""
        gad_trace = diagnoses.get(Disorder.GENERALIZED_ANXIETY.value)

        if gad_trace and gad_trace.result == DiagnosisResult.NO:
            return GAD7Score(score=0, severity=SeverityLevel.NONE)

        item_scores = {}
        total = 0

        for node_id, (item_name, max_score) in GAD7_NODE_MAPPING.items():
            met = node_lookup.get(node_id)
            score = max_score if met is True else 0
            item_scores[item_name] = score
            total += score

        total = min(total, 21)
        severity = self._band_lookup(total, GAD7_BANDS)

        return GAD7Score(score=total, severity=severity, item_scores=item_scores)

    # ── C-SSRS ────────────────────────────────

    def _compute_cssrs(
        self,
        node_lookup: dict[str, Optional[bool]],
        diagnoses: dict[str, PsyCoTTrace],
    ) -> CSSRSScore:
        """Compute C-SSRS score from suicide risk node evaluations."""
        sui_trace = diagnoses.get(Disorder.SUICIDE_RISK.value)

        if sui_trace and sui_trace.result == DiagnosisResult.NO:
            return CSSRSScore(
                ideation_level=0,
                behavior_present=False,
                severity=SeverityLevel.NONE,
                risk_category="no_risk",
            )

        # Find highest ideation level confirmed
        max_level = 0
        behavior_present = False

        for node_id, level in CSSRS_IDEATION_MAPPING.items():
            if node_lookup.get(node_id) is True:
                if node_id == "SUI_B5":
                    behavior_present = True
                else:
                    max_level = max(max_level, level)

        # Past attempt elevates risk even if current ideation is low
        if behavior_present and max_level < 2:
            max_level = 2

        risk_category, severity = CSSRS_RISK_CATEGORIES.get(
            max_level, ("unknown", SeverityLevel.NONE)
        )

        return CSSRSScore(
            ideation_level=max_level,
            behavior_present=behavior_present,
            severity=severity,
            risk_category=risk_category,
        )

    # ── OVERALL ───────────────────────────────

    def _compute_overall_severity(
        self,
        phq9: PHQ9Score,
        gad7: GAD7Score,
        cssrs: CSSRSScore,
        diagnoses: dict[str, PsyCoTTrace],
    ) -> SeverityLevel:
        """
        Determine the overall severity — the most severe active condition.
        Suicide risk always takes precedence if present.
        """
        # C-SSRS takes precedence
        if cssrs.severity != SeverityLevel.NONE:
            return cssrs.severity

        # Check PHQ-9 and GAD-7
        severity_order = [
            SeverityLevel.NONE,
            SeverityLevel.MINIMAL,
            SeverityLevel.MILD,
            SeverityLevel.MODERATE,
            SeverityLevel.MODERATELY_SEVERE,
            SeverityLevel.SEVERE,
        ]

        scores = [phq9.severity, gad7.severity]
        max_sev = max(scores, key=lambda s: severity_order.index(s))
        return max_sev

    # ── HELPERS ───────────────────────────────

    @staticmethod
    def _band_lookup(
        score: int,
        bands: list[tuple[int, int, SeverityLevel]],
    ) -> SeverityLevel:
        """Map a numeric score to a severity level using band definitions."""
        for low, high, level in bands:
            if low <= score <= high:
                return level
        return SeverityLevel.SEVERE

    @staticmethod
    def format_severity_report(report: SeverityReport) -> str:
        """Format severity scores as human-readable text."""
        lines = ["SEVERITY ASSESSMENT", "-" * 40]

        if report.phq9:
            lines.append(
                f"PHQ-9 (Depression): {report.phq9.score}/27 — "
                f"{report.phq9.severity.value.upper()}"
            )

        if report.gad7:
            lines.append(
                f"GAD-7 (Anxiety):    {report.gad7.score}/21 — "
                f"{report.gad7.severity.value.upper()}"
            )

        if report.cssrs:
            lines.append(
                f"C-SSRS (Suicide):   Level {report.cssrs.ideation_level}/5 — "
                f"{report.cssrs.risk_category.upper()} RISK"
            )

        lines.append(
            f"\nOverall Severity: {report.overall_severity.value.upper()}"
        )
        return "\n".join(lines)

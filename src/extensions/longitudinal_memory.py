"""
longitudinal_memory.py
----------------------
MAGI+ Extension 4: Longitudinal Session Memory & Trend Tracking

The original MAGI is single-session only. Mental health care is ongoing —
treatment effectiveness must be monitored over time.

This module:
  - Persists each completed session to a local JSON database
  - Loads prior session history for returning participants
  - Compares current session against previous ones
  - Detects trends: improving / stable / worsening per disorder
  - Generates a longitudinal summary for the clinical report
"""

from __future__ import annotations
import json
import os
from datetime import datetime
from typing import Optional
from tinydb import TinyDB, Query

from src.utils.data_models import (
    InterviewSession, SessionSummary, LongitudinalRecord,
    Disorder, DiagnosisResult, SeverityLevel, SeverityReport, PsyCoTTrace
)


# ─────────────────────────────────────────────
# TREND DETECTION
# ─────────────────────────────────────────────

SEVERITY_NUMERIC = {
    SeverityLevel.NONE: 0,
    SeverityLevel.MINIMAL: 1,
    SeverityLevel.MILD: 2,
    SeverityLevel.MODERATE: 3,
    SeverityLevel.MODERATELY_SEVERE: 4,
    SeverityLevel.SEVERE: 5,
}


def _score_to_numeric(score: Optional[int], max_score: int) -> float:
    """Normalize a score to 0–1 range."""
    if score is None:
        return 0.0
    return score / max_score


def _detect_trend(values: list[float]) -> str:
    """
    Detect trend direction from a list of numeric values (oldest → newest).
    Returns: 'improving', 'worsening', or 'stable'
    """
    if len(values) < 2:
        return "stable"

    # Compare last vs average of previous
    recent = values[-1]
    prior_avg = sum(values[:-1]) / len(values[:-1])
    delta = recent - prior_avg

    if delta <= -0.1:
        return "improving"   # Lower score = less severe = improving
    elif delta >= 0.1:
        return "worsening"
    else:
        return "stable"


# ─────────────────────────────────────────────
# LONGITUDINAL MEMORY
# ─────────────────────────────────────────────

class LongitudinalMemory:
    """
    Manages multi-session history for participants.

    Uses TinyDB (a lightweight JSON database) to persist session records.
    No external database server required — data is stored in a local JSON file.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the memory store.

        Args:
            db_path: Path to the JSON database file.
                     Defaults to data/sessions/sessions_db.json
        """
        if db_path is None:
            db_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "data",
                "sessions", "sessions_db.json"
            )
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db = TinyDB(db_path)
        self._sessions_table = self.db.table("sessions")
        self._records_table = self.db.table("longitudinal_records")

    # ── SAVE / LOAD ───────────────────────────

    def save_session(self, session: InterviewSession) -> None:
        """
        Persist a completed session and update the longitudinal record.
        """
        # Save the full session
        session_data = session.model_dump(mode="json")
        Q = Query()
        existing = self._sessions_table.search(Q.session_id == session.session_id)
        if existing:
            self._sessions_table.update(session_data, Q.session_id == session.session_id)
        else:
            self._sessions_table.insert(session_data)

        # Update the participant's longitudinal record
        self._update_longitudinal_record(session)
        print(f"[Memory] Session {session.session_id} saved for participant {session.participant_id}")

    def load_session(self, session_id: str) -> Optional[InterviewSession]:
        """Load a specific session by ID."""
        Q = Query()
        results = self._sessions_table.search(Q.session_id == session_id)
        if results:
            return InterviewSession.model_validate(results[0])
        return None

    def get_participant_sessions(self, participant_id: str) -> list[SessionSummary]:
        """Get all session summaries for a participant, ordered by date."""
        Q = Query()
        record_data = self._records_table.search(Q.participant_id == participant_id)
        if not record_data:
            return []
        record = LongitudinalRecord.model_validate(record_data[0])
        return sorted(record.sessions, key=lambda s: s.session_number)

    def get_longitudinal_record(self, participant_id: str) -> Optional[LongitudinalRecord]:
        """Get the full longitudinal record for a participant."""
        Q = Query()
        results = self._records_table.search(Q.participant_id == participant_id)
        if results:
            return LongitudinalRecord.model_validate(results[0])
        return None

    def get_session_number(self, participant_id: str) -> int:
        """Return what session number the next session would be."""
        sessions = self.get_participant_sessions(participant_id)
        return len(sessions) + 1

    # ── COMPARISON & TRENDS ───────────────────

    def compare_with_previous(
        self,
        current_session: InterviewSession,
    ) -> Optional[dict]:
        """
        Compare the current session with the participant's session history.

        Returns a comparison dict, or None if this is the first session.
        """
        prior_sessions = self.get_participant_sessions(current_session.participant_id)

        if not prior_sessions:
            return None  # First session — nothing to compare

        # Build comparison
        comparison = {
            "sessions_total": len(prior_sessions) + 1,
            "first_session_date": prior_sessions[0].date.strftime("%Y-%m-%d"),
            "disorder_trends": {},
            "severity_trends": {},
            "overall_trend": "stable",
            "notable_changes": [],
        }

        # ── Disorder-level comparison ──────────
        current_diags = {}
        for disorder_key, trace in current_session.diagnoses.items():
            current_diags[disorder_key] = trace.result.value

        for disorder_key in current_diags:
            prior_results = [
                s.diagnoses.get(disorder_key, "unknown")
                for s in prior_sessions
            ]
            current_result = current_diags[disorder_key]

            # Check for new diagnosis
            if prior_results and all(r == "no" for r in prior_results) and current_result == "yes":
                comparison["notable_changes"].append(
                    f"NEW: {disorder_key.replace('_', ' ').title()} diagnosed this session"
                )
            # Check for resolved diagnosis
            elif prior_results and any(r == "yes" for r in prior_results) and current_result == "no":
                comparison["notable_changes"].append(
                    f"RESOLVED: {disorder_key.replace('_', ' ').title()} no longer meets criteria"
                )

            comparison["disorder_trends"][disorder_key] = {
                "history": prior_results,
                "current": current_result,
            }

        # ── PHQ-9 trend ────────────────────────
        if current_session.severity_report and current_session.severity_report.phq9:
            prior_phq9 = [s.phq9_score for s in prior_sessions if s.phq9_score is not None]
            current_phq9 = current_session.severity_report.phq9.score
            if prior_phq9:
                values = [_score_to_numeric(s, 27) for s in prior_phq9]
                values.append(_score_to_numeric(current_phq9, 27))
                trend = _detect_trend(values)
                comparison["severity_trends"]["depression_phq9"] = {
                    "history": prior_phq9,
                    "current": current_phq9,
                    "trend": trend,
                }
                if trend != "stable":
                    comparison["notable_changes"].append(
                        f"Depression severity {trend}: PHQ-9 {prior_phq9[-1]} → {current_phq9}"
                    )

        # ── GAD-7 trend ────────────────────────
        if current_session.severity_report and current_session.severity_report.gad7:
            prior_gad7 = [s.gad7_score for s in prior_sessions if s.gad7_score is not None]
            current_gad7 = current_session.severity_report.gad7.score
            if prior_gad7:
                values = [_score_to_numeric(s, 21) for s in prior_gad7]
                values.append(_score_to_numeric(current_gad7, 21))
                trend = _detect_trend(values)
                comparison["severity_trends"]["anxiety_gad7"] = {
                    "history": prior_gad7,
                    "current": current_gad7,
                    "trend": trend,
                }
                if trend != "stable":
                    comparison["notable_changes"].append(
                        f"Anxiety severity {trend}: GAD-7 {prior_gad7[-1]} → {current_gad7}"
                    )

        # ── Overall trend ──────────────────────
        if comparison["severity_trends"]:
            trends = [v["trend"] for v in comparison["severity_trends"].values()]
            if "worsening" in trends:
                comparison["overall_trend"] = "worsening"
            elif all(t == "improving" for t in trends):
                comparison["overall_trend"] = "improving"
            else:
                comparison["overall_trend"] = "mixed"

        return comparison

    def generate_longitudinal_summary(
        self,
        participant_id: str,
        current_session: InterviewSession,
    ) -> str:
        """
        Generate a human-readable longitudinal summary for the clinical report.
        """
        comparison = self.compare_with_previous(current_session)

        if comparison is None:
            return "This is the participant's first assessment session. No longitudinal comparison available."

        lines = [
            f"Longitudinal Assessment Summary (Session {comparison['sessions_total']} of {comparison['sessions_total']})",
            f"First assessed: {comparison['first_session_date']}",
            "",
        ]

        # Overall trend
        trend_emoji = {"improving": "📈", "worsening": "📉", "stable": "➡️", "mixed": "↕️"}
        emoji = trend_emoji.get(comparison["overall_trend"], "")
        lines.append(f"Overall trend: {emoji} {comparison['overall_trend'].upper()}")
        lines.append("")

        # Notable changes
        if comparison["notable_changes"]:
            lines.append("Notable changes since last session:")
            for change in comparison["notable_changes"]:
                lines.append(f"  • {change}")
        else:
            lines.append("No significant changes noted compared to previous session.")

        # Severity score trends
        if comparison["severity_trends"]:
            lines.append("")
            lines.append("Severity score trends:")
            for metric, data in comparison["severity_trends"].items():
                metric_name = metric.replace("_", " ").title()
                lines.append(
                    f"  • {metric_name}: {data['history'][-1]} → {data['current']} ({data['trend']})"
                )

        return "\n".join(lines)

    # ── PRIVATE ───────────────────────────────

    def _update_longitudinal_record(self, session: InterviewSession) -> None:
        """Update or create the longitudinal record for a participant."""
        Q = Query()
        existing = self._records_table.search(Q.participant_id == session.participant_id)

        # Build session summary
        diag_summary = {
            k: v.result.value
            for k, v in session.diagnoses.items()
        }

        phq9_score = None
        gad7_score = None
        dominant_emotion = None
        overall_severity = SeverityLevel.NONE.value

        if session.severity_report:
            if session.severity_report.phq9:
                phq9_score = session.severity_report.phq9.score
            if session.severity_report.gad7:
                gad7_score = session.severity_report.gad7.score
            overall_severity = session.severity_report.overall_severity.value

        if session.emotion_arc and session.emotion_arc.dominant_emotion:
            dominant_emotion = session.emotion_arc.dominant_emotion.value

        summary = SessionSummary(
            session_id=session.session_id,
            session_number=session.session_number,
            date=session.created_at,
            diagnoses=diag_summary,
            severity_overall=overall_severity,
            phq9_score=phq9_score,
            gad7_score=gad7_score,
            dominant_emotion=dominant_emotion,
        )

        if existing:
            record = LongitudinalRecord.model_validate(existing[0])
            # Replace if session already in record, else add
            record.sessions = [
                s for s in record.sessions
                if s.session_id != session.session_id
            ]
            record.add_session(summary)
            self._records_table.update(
                record.model_dump(mode="json"),
                Q.participant_id == session.participant_id,
            )
        else:
            record = LongitudinalRecord(participant_id=session.participant_id)
            record.add_session(summary)
            self._records_table.insert(record.model_dump(mode="json"))

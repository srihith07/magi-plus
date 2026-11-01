"""
navigation_agent.py
-------------------
Agent 1 of 4 from the original MAGI paper.

The Navigation Agent is the "conductor" of the interview.
It maintains overall control of the dialogue by:
  - Tracking which MINI node we are currently on
  - Deciding which node to go to next based on judgment results
  - Ensuring no critical diagnostic nodes are skipped
  - Coordinating with all other agents
  - Detecting if suicidal ideation triggers the suicide risk section
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from src.utils.mini_tree import MiniTree, MiniNode, build_mini_tree
from src.utils.data_models import (
    NodeStatus, NodeEvaluation, InterviewSession, Disorder
)


# ─────────────────────────────────────────────
# NAVIGATION STATE
# ─────────────────────────────────────────────

@dataclass
class NavigationState:
    """
    Tracks the current state of the interview navigation.
    One instance lives for the duration of a session.
    """
    current_node_id: Optional[str] = None
    current_disorder: Optional[str] = None
    disorders_queue: list[str] = field(default_factory=list)
    completed_disorders: list[str] = field(default_factory=list)
    node_history: list[str] = field(default_factory=list)    # All nodes visited
    suicide_flag: bool = False    # True if suicide risk section was triggered
    interview_complete: bool = False

    def push_node(self, node_id: str) -> None:
        """Record a visited node."""
        self.node_history.append(node_id)
        self.current_node_id = node_id


# ─────────────────────────────────────────────
# NAVIGATION AGENT
# ─────────────────────────────────────────────

class NavigationAgent:
    """
    The Navigation Agent manages interview flow.

    It operates as a state machine over the MINI decision tree,
    transitioning between nodes based on the Judgment Agent's verdicts.
    """

    # Disorders screened in order (matching original MAGI paper)
    DEFAULT_DISORDER_ORDER = [
        "depression",
        "generalized_anxiety",
        "social_anxiety",
        "suicide_risk",
    ]

    def __init__(self, tree: Optional[MiniTree] = None):
        self.tree = tree or build_mini_tree()
        self.state = NavigationState()

    def start_interview(
        self,
        disorders: Optional[list[str]] = None
    ) -> MiniNode:
        """
        Begin the interview. Returns the first node to ask about.

        Args:
            disorders: List of disorders to screen (uses default order if None)

        Returns:
            The first MiniNode to present to the Question Agent
        """
        self.state = NavigationState()
        self.state.disorders_queue = disorders or self.DEFAULT_DISORDER_ORDER.copy()

        # Start with the first disorder
        return self._advance_to_next_disorder()

    def next_node(
        self,
        judgment_result: bool | None,
        current_node: MiniNode,
    ) -> Optional[MiniNode]:
        """
        Given the Judgment Agent's verdict on the current node,
        determine and return the next node.

        Args:
            judgment_result: True (criterion met), False (not met), None (uncertain)
            current_node: The node that was just evaluated

        Returns:
            The next MiniNode, or None if the interview is complete
        """
        # Determine branch to follow
        if judgment_result is True:
            next_id = current_node.branch_yes
            # Special case: depression suicidal ideation → also trigger suicide section
            if (current_node.node_id == "DEP_A3g"
                    and not self.state.suicide_flag):
                self._trigger_suicide_section()
        elif judgment_result is False:
            next_id = current_node.branch_no
        else:
            # Uncertain: follow uncertain branch or stay on current node
            next_id = current_node.branch_uncertain or current_node.node_id

        # If the next node is a terminal, move to the next disorder
        if next_id is None or self._is_terminal(next_id):
            return self._advance_to_next_disorder()

        # Get the actual node
        node = self.tree.get_node(next_id)
        if node:
            self.state.push_node(node.node_id)

        return node

    def get_current_node(self) -> Optional[MiniNode]:
        """Return the currently active node."""
        if self.state.current_node_id:
            return self.tree.get_node(self.state.current_node_id)
        return None

    def is_complete(self) -> bool:
        """True if all disorders have been screened."""
        return self.state.interview_complete

    def get_progress(self) -> dict:
        """Return a summary of interview progress."""
        total = len(self.DEFAULT_DISORDER_ORDER)
        done = len(self.state.completed_disorders)
        return {
            "completed_disorders": self.state.completed_disorders,
            "remaining_disorders": self.state.disorders_queue,
            "current_disorder": self.state.current_disorder,
            "progress_pct": round((done / total) * 100) if total > 0 else 0,
            "nodes_visited": len(self.state.node_history),
        }

    # ── PRIVATE HELPERS ───────────────────────

    def _advance_to_next_disorder(self) -> Optional[MiniNode]:
        """
        Move to the next disorder in the queue.
        Returns the entry node of the next disorder, or None if done.
        """
        # Mark current disorder as complete
        if self.state.current_disorder:
            self.state.completed_disorders.append(self.state.current_disorder)

        # No more disorders
        if not self.state.disorders_queue:
            self.state.interview_complete = True
            return None

        # Move to next disorder
        next_disorder = self.state.disorders_queue.pop(0)
        self.state.current_disorder = next_disorder

        # Get the entry node
        entry_node = self.tree.get_entry_node(next_disorder)
        if entry_node:
            self.state.push_node(entry_node.node_id)

        return entry_node

    def _is_terminal(self, node_id: str) -> bool:
        """True if this node ID leads to a synthesis or screen-negative terminal."""
        node = self.tree.get_node(node_id)
        return node.is_terminal if node else False

    def _trigger_suicide_section(self) -> None:
        """
        Ensure the suicide risk section is included.
        Called when suicidal ideation is detected in the depression section.
        """
        if "suicide_risk" not in self.state.disorders_queue:
            # Prioritize it — add to the front of the queue
            self.state.disorders_queue.insert(0, "suicide_risk")
        self.state.suicide_flag = True
        print("[Navigation] Suicide risk section triggered due to ideation detection.")

    def force_node(self, node_id: str) -> Optional[MiniNode]:
        """
        Forcefully jump to a specific node.
        Used when the Judgment Agent detects crisis signals.
        """
        node = self.tree.get_node(node_id)
        if node:
            self.state.push_node(node_id)
        return node

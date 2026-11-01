"""
mini_tree.py
------------
The MINI (Mini International Neuropsychiatric Interview) decision tree.

This module represents the MINI protocol as a navigable data structure.
The Navigation Agent uses this to determine which question node to visit next
based on participant responses (branching logic).

Each node has:
- A unique ID
- The diagnostic criterion it tests
- Branching rules (which node to go to based on Yes/No)
- Whether it is a required node (cannot be skipped)
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel
import json
import os


# ─────────────────────────────────────────────
# NODE DATA STRUCTURE
# ─────────────────────────────────────────────

class MiniNode(BaseModel):
    """A single node in the MINI interview decision tree."""
    node_id: str                         # e.g., "DEP_A1a"
    disorder: str                        # e.g., "depression"
    section: str                         # e.g., "A" (MINI section label)
    label: str                           # Human-readable criterion name
    clinical_criterion: str              # The DSM-5 criterion this tests
    question_intent: str                 # What the question is trying to find out
    example_question: str                # A sample question (used by Question Agent)
    required: bool = True                # Cannot be skipped
    branch_yes: Optional[str] = None     # Node ID to go to if answer is Yes
    branch_no: Optional[str] = None      # Node ID to go to if answer is No
    branch_uncertain: Optional[str] = None  # Node to go to if unclear
    is_terminal: bool = False            # True = no more questions after this
    notes: str = ""                      # Clinical notes for the agent


class MiniSection(BaseModel):
    """A section of the MINI covering one disorder."""
    section_id: str                      # e.g., "A"
    disorder: str                        # e.g., "depression"
    name: str                            # e.g., "Major Depressive Episode"
    entry_node: str                      # First node to visit
    nodes: dict[str, MiniNode]          # All nodes in this section


class MiniTree(BaseModel):
    """The complete MINI interview tree."""
    sections: dict[str, MiniSection]     # Keyed by section_id
    version: str = "MINI 7.0.2"

    def get_node(self, node_id: str) -> Optional[MiniNode]:
        """Find a node by its ID across all sections."""
        for section in self.sections.values():
            if node_id in section.nodes:
                return section.nodes[node_id]
        return None

    def get_section_for_disorder(self, disorder: str) -> Optional[MiniSection]:
        """Get the section for a given disorder name."""
        for section in self.sections.values():
            if section.disorder == disorder:
                return section
        return None

    def get_entry_node(self, disorder: str) -> Optional[MiniNode]:
        """Get the first node to ask for a disorder."""
        section = self.get_section_for_disorder(disorder)
        if section:
            return section.nodes.get(section.entry_node)
        return None


# ─────────────────────────────────────────────
# MINI TREE DEFINITION
# ─────────────────────────────────────────────

def build_mini_tree() -> MiniTree:
    """
    Build and return the MINI interview tree covering:
    - Section A: Major Depressive Episode (Depression)
    - Section N: Generalized Anxiety Disorder
    - Section F: Social Anxiety Disorder
    - Section B: Suicidality

    This follows the MINI 7.0.2 structure (Sheehan et al.).
    """

    # ── SECTION A: DEPRESSION ─────────────────

    dep_nodes = {
        "DEP_A1a": MiniNode(
            node_id="DEP_A1a",
            disorder="depression",
            section="A",
            label="Depressed mood",
            clinical_criterion="Depressed mood most of the day, nearly every day",
            question_intent="Assess presence of persistent low mood",
            example_question=(
                "Over the past two weeks, have you felt depressed, down, "
                "or hopeless most of the time?"
            ),
            branch_yes="DEP_A2a",
            branch_no="DEP_A1b",
        ),
        "DEP_A1b": MiniNode(
            node_id="DEP_A1b",
            disorder="depression",
            section="A",
            label="Anhedonia",
            clinical_criterion="Markedly diminished interest or pleasure in activities",
            question_intent="Assess loss of interest/pleasure as alternative entry criterion",
            example_question=(
                "In the past two weeks, have you lost interest or pleasure "
                "in most activities you usually enjoy?"
            ),
            branch_yes="DEP_A2a",
            branch_no="DEP_SCREEN_NEGATIVE",
        ),
        "DEP_A2a": MiniNode(
            node_id="DEP_A2a",
            disorder="depression",
            section="A",
            label="Duration check",
            clinical_criterion="Symptoms present for at least 2 weeks",
            question_intent="Confirm temporal criterion",
            example_question=(
                "Have these feelings been present nearly every day for "
                "at least two weeks?"
            ),
            branch_yes="DEP_A3a",
            branch_no="DEP_SCREEN_NEGATIVE",
        ),
        "DEP_A3a": MiniNode(
            node_id="DEP_A3a",
            disorder="depression",
            section="A",
            label="Appetite/weight change",
            clinical_criterion="Significant weight change or appetite disturbance",
            question_intent="Assess appetite/weight as supporting symptom",
            example_question=(
                "Have you noticed a significant change in your appetite or "
                "weight recently — either eating much more or much less than usual?"
            ),
            branch_yes="DEP_A3b",
            branch_no="DEP_A3b",
        ),
        "DEP_A3b": MiniNode(
            node_id="DEP_A3b",
            disorder="depression",
            section="A",
            label="Sleep disturbance",
            clinical_criterion="Insomnia or hypersomnia nearly every night",
            question_intent="Assess sleep as supporting symptom",
            example_question=(
                "Have you been having trouble sleeping — either too little "
                "or too much — nearly every night?"
            ),
            branch_yes="DEP_A3c",
            branch_no="DEP_A3c",
        ),
        "DEP_A3c": MiniNode(
            node_id="DEP_A3c",
            disorder="depression",
            section="A",
            label="Psychomotor changes",
            clinical_criterion="Psychomotor agitation or retardation observable by others",
            question_intent="Assess psychomotor symptoms",
            example_question=(
                "Have others noticed that you seem unusually slowed down, "
                "or on the contrary, very agitated or restless?"
            ),
            branch_yes="DEP_A3d",
            branch_no="DEP_A3d",
        ),
        "DEP_A3d": MiniNode(
            node_id="DEP_A3d",
            disorder="depression",
            section="A",
            label="Fatigue",
            clinical_criterion="Fatigue or loss of energy nearly every day",
            question_intent="Assess energy levels",
            example_question=(
                "Have you been feeling unusually tired or lacking energy "
                "nearly every day?"
            ),
            branch_yes="DEP_A3e",
            branch_no="DEP_A3e",
        ),
        "DEP_A3e": MiniNode(
            node_id="DEP_A3e",
            disorder="depression",
            section="A",
            label="Worthlessness/guilt",
            clinical_criterion="Feelings of worthlessness or excessive guilt",
            question_intent="Assess cognitive symptoms of depression",
            example_question=(
                "Have you been feeling worthless or excessively guilty "
                "about things, even when others say you shouldn't?"
            ),
            branch_yes="DEP_A3f",
            branch_no="DEP_A3f",
        ),
        "DEP_A3f": MiniNode(
            node_id="DEP_A3f",
            disorder="depression",
            section="A",
            label="Concentration difficulty",
            clinical_criterion="Diminished ability to think, concentrate, or decide",
            question_intent="Assess cognitive function",
            example_question=(
                "Have you been having difficulty concentrating, thinking clearly, "
                "or making decisions that you wouldn't normally struggle with?"
            ),
            branch_yes="DEP_A3g",
            branch_no="DEP_A3g",
        ),
        "DEP_A3g": MiniNode(
            node_id="DEP_A3g",
            disorder="depression",
            section="A",
            label="Suicidal ideation",
            clinical_criterion="Recurrent thoughts of death or suicidal ideation",
            question_intent="Screen for suicidality",
            example_question=(
                "Have you had recurring thoughts about death, or felt that "
                "you would be better off dead?"
            ),
            branch_yes="DEP_SYNTHESIS",
            branch_no="DEP_SYNTHESIS",
            notes="If Yes → also trigger Suicide Risk section",
        ),
        "DEP_SYNTHESIS": MiniNode(
            node_id="DEP_SYNTHESIS",
            disorder="depression",
            section="A",
            label="Synthesis",
            clinical_criterion="≥5 symptoms including depressed mood or anhedonia",
            question_intent="Synthesize all evidence for diagnosis",
            example_question="",
            is_terminal=True,
        ),
        "DEP_SCREEN_NEGATIVE": MiniNode(
            node_id="DEP_SCREEN_NEGATIVE",
            disorder="depression",
            section="A",
            label="Screen negative",
            clinical_criterion="Entry criteria not met",
            question_intent="Exit depression section",
            example_question="",
            is_terminal=True,
        ),
    }

    # ── SECTION N: GENERALIZED ANXIETY ────────

    gad_nodes = {
        "GAD_N1a": MiniNode(
            node_id="GAD_N1a",
            disorder="generalized_anxiety",
            section="N",
            label="Excessive worry",
            clinical_criterion="Excessive anxiety and worry about multiple events/activities",
            question_intent="Assess presence and breadth of worry",
            example_question=(
                "Over the past 6 months, have you been excessively anxious "
                "or worried about several different things in your life, "
                "such as work, finances, health, or family?"
            ),
            branch_yes="GAD_N2",
            branch_no="GAD_SCREEN_NEGATIVE",
        ),
        "GAD_N2": MiniNode(
            node_id="GAD_N2",
            disorder="generalized_anxiety",
            section="N",
            label="Uncontrollability",
            clinical_criterion="Difficulty controlling the worry",
            question_intent="Assess uncontrollability of worry",
            example_question=(
                "Do you find it difficult to control or stop this worrying, "
                "even when you try?"
            ),
            branch_yes="GAD_N3a",
            branch_no="GAD_SCREEN_NEGATIVE",
        ),
        "GAD_N3a": MiniNode(
            node_id="GAD_N3a",
            disorder="generalized_anxiety",
            section="N",
            label="Restlessness",
            clinical_criterion="Restlessness or feeling keyed up or on edge",
            question_intent="Assess physical anxiety symptoms",
            example_question=(
                "Do you often feel restless, keyed up, or on edge?"
            ),
            branch_yes="GAD_N3b",
            branch_no="GAD_N3b",
        ),
        "GAD_N3b": MiniNode(
            node_id="GAD_N3b",
            disorder="generalized_anxiety",
            section="N",
            label="Fatigue from anxiety",
            clinical_criterion="Being easily fatigued",
            question_intent="Assess anxiety-related fatigue",
            example_question=(
                "Do you tire easily — more than you would expect given your activities?"
            ),
            branch_yes="GAD_N3c",
            branch_no="GAD_N3c",
        ),
        "GAD_N3c": MiniNode(
            node_id="GAD_N3c",
            disorder="generalized_anxiety",
            section="N",
            label="Concentration difficulty",
            clinical_criterion="Difficulty concentrating or mind going blank",
            question_intent="Assess cognitive anxiety symptoms",
            example_question=(
                "Do you have difficulty concentrating, or does your mind "
                "go blank during the day?"
            ),
            branch_yes="GAD_N3d",
            branch_no="GAD_N3d",
        ),
        "GAD_N3d": MiniNode(
            node_id="GAD_N3d",
            disorder="generalized_anxiety",
            section="N",
            label="Irritability",
            clinical_criterion="Irritability",
            question_intent="Assess mood-related anxiety symptoms",
            example_question=(
                "Have you been more irritable than usual — getting annoyed "
                "or frustrated more easily?"
            ),
            branch_yes="GAD_N3e",
            branch_no="GAD_N3e",
        ),
        "GAD_N3e": MiniNode(
            node_id="GAD_N3e",
            disorder="generalized_anxiety",
            section="N",
            label="Muscle tension",
            clinical_criterion="Muscle tension",
            question_intent="Assess somatic anxiety symptoms",
            example_question=(
                "Do you experience muscle tension, stiffness, or aches "
                "related to your anxiety?"
            ),
            branch_yes="GAD_N3f",
            branch_no="GAD_N3f",
        ),
        "GAD_N3f": MiniNode(
            node_id="GAD_N3f",
            disorder="generalized_anxiety",
            section="N",
            label="Sleep disturbance",
            clinical_criterion="Sleep disturbance due to worry",
            question_intent="Assess anxiety-related sleep problems",
            example_question=(
                "Do you have trouble falling asleep, staying asleep, or "
                "do you wake up feeling unrested because of your worrying?"
            ),
            branch_yes="GAD_SYNTHESIS",
            branch_no="GAD_SYNTHESIS",
        ),
        "GAD_SYNTHESIS": MiniNode(
            node_id="GAD_SYNTHESIS",
            disorder="generalized_anxiety",
            section="N",
            label="Synthesis",
            clinical_criterion="Excessive worry + uncontrollability + ≥3 physical symptoms",
            question_intent="Synthesize GAD diagnosis",
            example_question="",
            is_terminal=True,
        ),
        "GAD_SCREEN_NEGATIVE": MiniNode(
            node_id="GAD_SCREEN_NEGATIVE",
            disorder="generalized_anxiety",
            section="N",
            label="Screen negative",
            clinical_criterion="Entry criteria not met",
            question_intent="Exit GAD section",
            example_question="",
            is_terminal=True,
        ),
    }

    # ── SECTION F: SOCIAL ANXIETY ──────────────

    soc_nodes = {
        "SOC_F1a": MiniNode(
            node_id="SOC_F1a",
            disorder="social_anxiety",
            section="F",
            label="Fear of social situations",
            clinical_criterion="Marked fear of social or performance situations",
            question_intent="Screen for social anxiety",
            example_question=(
                "Do you feel very anxious or fearful in social situations — "
                "like speaking in public, being at parties, meeting new people, "
                "or being watched while doing something?"
            ),
            branch_yes="SOC_F2",
            branch_no="SOC_SCREEN_NEGATIVE",
        ),
        "SOC_F2": MiniNode(
            node_id="SOC_F2",
            disorder="social_anxiety",
            section="F",
            label="Fear of negative evaluation",
            clinical_criterion="Fear of embarrassment or negative judgment",
            question_intent="Assess the nature of social fear",
            example_question=(
                "Are you afraid that you might embarrass yourself, or that "
                "others will judge or negatively evaluate you in these situations?"
            ),
            branch_yes="SOC_F3",
            branch_no="SOC_SCREEN_NEGATIVE",
        ),
        "SOC_F3": MiniNode(
            node_id="SOC_F3",
            disorder="social_anxiety",
            section="F",
            label="Avoidance",
            clinical_criterion="Avoidance of feared situations or endurance with intense anxiety",
            question_intent="Assess behavioral impact",
            example_question=(
                "Do you avoid these situations, or endure them with significant "
                "distress or anxiety?"
            ),
            branch_yes="SOC_F4",
            branch_no="SOC_SCREEN_NEGATIVE",
        ),
        "SOC_F4": MiniNode(
            node_id="SOC_F4",
            disorder="social_anxiety",
            section="F",
            label="Functional impairment",
            clinical_criterion="Significant impact on social or occupational functioning",
            question_intent="Assess severity of impairment",
            example_question=(
                "Has this fear or avoidance significantly affected your work, "
                "school, social life, or other important areas?"
            ),
            branch_yes="SOC_F5",
            branch_no="SOC_SCREEN_NEGATIVE",
        ),
        "SOC_F5": MiniNode(
            node_id="SOC_F5",
            disorder="social_anxiety",
            section="F",
            label="Duration",
            clinical_criterion="Symptoms present for ≥6 months",
            question_intent="Confirm chronicity",
            example_question=(
                "Have these fears and avoidance been present for at least "
                "6 months?"
            ),
            branch_yes="SOC_SYNTHESIS",
            branch_no="SOC_SCREEN_NEGATIVE",
        ),
        "SOC_SYNTHESIS": MiniNode(
            node_id="SOC_SYNTHESIS",
            disorder="social_anxiety",
            section="F",
            label="Synthesis",
            clinical_criterion="Social fear + avoidance + impairment + ≥6 months",
            question_intent="Synthesize social anxiety diagnosis",
            example_question="",
            is_terminal=True,
        ),
        "SOC_SCREEN_NEGATIVE": MiniNode(
            node_id="SOC_SCREEN_NEGATIVE",
            disorder="social_anxiety",
            section="F",
            label="Screen negative",
            clinical_criterion="Entry criteria not met",
            question_intent="Exit social anxiety section",
            example_question="",
            is_terminal=True,
        ),
    }

    # ── SECTION B: SUICIDE RISK ─────────────────

    sui_nodes = {
        "SUI_B1": MiniNode(
            node_id="SUI_B1",
            disorder="suicide_risk",
            section="B",
            label="Passive suicidal ideation",
            clinical_criterion="Wishes to be dead or thoughts of being better off dead",
            question_intent="Screen for passive ideation",
            example_question=(
                "In the past month, have you had any thoughts that you would "
                "be better off dead, or wishes to be dead?"
            ),
            branch_yes="SUI_B2",
            branch_no="SUI_B2",
            notes="Even if No, continue to active ideation check",
        ),
        "SUI_B2": MiniNode(
            node_id="SUI_B2",
            disorder="suicide_risk",
            section="B",
            label="Active suicidal ideation",
            clinical_criterion="Thoughts of killing oneself",
            question_intent="Assess active suicidal thoughts",
            example_question=(
                "Have you had any thoughts of killing yourself or taking "
                "your own life?"
            ),
            branch_yes="SUI_B3",
            branch_no="SUI_SCREEN_LOW",
        ),
        "SUI_B3": MiniNode(
            node_id="SUI_B3",
            disorder="suicide_risk",
            section="B",
            label="Suicidal plan",
            clinical_criterion="Has thought about how to commit suicide",
            question_intent="Assess presence of a plan",
            example_question=(
                "Have you thought about how you would do it — do you have "
                "a plan?"
            ),
            branch_yes="SUI_B4",
            branch_no="SUI_B4",
        ),
        "SUI_B4": MiniNode(
            node_id="SUI_B4",
            disorder="suicide_risk",
            section="B",
            label="Suicidal intent",
            clinical_criterion="Has intention to act on suicidal thoughts",
            question_intent="Assess intent to act",
            example_question=(
                "Do you have any intention of acting on these thoughts?"
            ),
            branch_yes="SUI_B5",
            branch_no="SUI_B5",
        ),
        "SUI_B5": MiniNode(
            node_id="SUI_B5",
            disorder="suicide_risk",
            section="B",
            label="Past attempt",
            clinical_criterion="Has made a suicide attempt in the past",
            question_intent="Assess history of attempts",
            example_question=(
                "Have you ever attempted to take your own life in the past?"
            ),
            branch_yes="SUI_SYNTHESIS",
            branch_no="SUI_SYNTHESIS",
        ),
        "SUI_SYNTHESIS": MiniNode(
            node_id="SUI_SYNTHESIS",
            disorder="suicide_risk",
            section="B",
            label="Synthesis",
            clinical_criterion="Risk stratification based on ideation/plan/intent/history",
            question_intent="Synthesize suicide risk level",
            example_question="",
            is_terminal=True,
        ),
        "SUI_SCREEN_LOW": MiniNode(
            node_id="SUI_SCREEN_LOW",
            disorder="suicide_risk",
            section="B",
            label="Low/no risk",
            clinical_criterion="No active suicidal ideation detected",
            question_intent="Exit suicide section — low risk",
            example_question="",
            is_terminal=True,
        ),
    }

    # ── ASSEMBLE THE TREE ──────────────────────

    tree = MiniTree(
        sections={
            "A": MiniSection(
                section_id="A",
                disorder="depression",
                name="Major Depressive Episode",
                entry_node="DEP_A1a",
                nodes=dep_nodes,
            ),
            "N": MiniSection(
                section_id="N",
                disorder="generalized_anxiety",
                name="Generalized Anxiety Disorder",
                entry_node="GAD_N1a",
                nodes=gad_nodes,
            ),
            "F": MiniSection(
                section_id="F",
                disorder="social_anxiety",
                name="Social Anxiety Disorder",
                entry_node="SOC_F1a",
                nodes=soc_nodes,
            ),
            "B": MiniSection(
                section_id="B",
                disorder="suicide_risk",
                name="Suicidality",
                entry_node="SUI_B1",
                nodes=sui_nodes,
            ),
        }
    )

    return tree


# ─────────────────────────────────────────────
# SAVE / LOAD HELPERS
# ─────────────────────────────────────────────

def save_mini_tree(tree: MiniTree, path: str) -> None:
    """Serialize the MINI tree to a JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(tree.model_dump_json(indent=2))
    print(f"MINI tree saved to {path}")


def load_mini_tree(path: str) -> MiniTree:
    """Load a MINI tree from a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return MiniTree.model_validate(data)


# ─────────────────────────────────────────────
# MAIN: Generate and save the tree
# ─────────────────────────────────────────────

if __name__ == "__main__":
    tree = build_mini_tree()
    output_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "mini_protocol", "mini_tree.json"
    )
    save_mini_tree(tree, output_path)

    # Quick sanity check
    node = tree.get_entry_node("depression")
    print(f"Depression entry node: {node.node_id} — {node.label}")
    print(f"Total sections: {len(tree.sections)}")
    total_nodes = sum(len(s.nodes) for s in tree.sections.values())
    print(f"Total nodes: {total_nodes}")

"""
question_agent.py
-----------------
Agent 2 of 4 from the original MAGI paper.

The Question Agent generates the actual questions asked to participants.
It has 3 strategies (from the original paper):
  1. PROBE    — Standard diagnostic probing, rephrased conversationally
  2. EXPLAIN  — Clarifies a clinical concept the participant is confused about
  3. EMPATHIZE — Responds with emotional support when distress is detected,
                 then gently redirects to the diagnostic question

The agent selects a strategy based on:
  - The current node's question intent
  - Whether distress was detected in the last turn
  - Whether the participant expressed confusion
  - Conversation history context
"""

from __future__ import annotations
from typing import Optional
from src.utils.mini_tree import MiniNode
from src.utils.data_models import (
    QuestionStrategy, ConversationTurn, EmotionLabel
)
from src.utils.llm_client import LLMClient, LLMConfig, system_message, user_message, SYSTEM_PROMPTS
import json


class QuestionAgent:
    """
    Generates adaptive, empathetic questions for each MINI node.
    """

    # Keywords that suggest participant confusion
    CONFUSION_KEYWORDS = [
        "what do you mean", "i don't understand", "can you explain",
        "what is", "i'm not sure what", "clarify", "confused",
        "what does that mean", "i don't know what"
    ]

    # Keywords that suggest distress
    DISTRESS_KEYWORDS = [
        "i can't", "it's too much", "i don't want to", "please stop",
        "this is hard", "i'm scared", "overwhelmed", "crying",
        "i hate", "awful", "terrible", "hopeless", "can't go on"
    ]

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient(LLMConfig(temperature=0.8))

    def generate_question(
        self,
        node: MiniNode,
        conversation_history: list[ConversationTurn],
        last_emotion: Optional[EmotionLabel] = None,
        force_strategy: Optional[QuestionStrategy] = None,
    ) -> tuple[str, QuestionStrategy]:
        """
        Generate the next question for a given MINI node.

        Args:
            node: The current MINI interview node
            conversation_history: All previous turns in this session
            last_emotion: Emotion detected in the participant's last response
            force_strategy: Override strategy selection (used by Navigation Agent)

        Returns:
            (question_text, strategy_used)
        """
        # Determine which strategy to use
        strategy = force_strategy or self._select_strategy(
            conversation_history, last_emotion
        )

        # Build prompt based on strategy
        question = self._generate_with_llm(node, conversation_history, strategy)

        return question, strategy

    def _select_strategy(
        self,
        history: list[ConversationTurn],
        last_emotion: Optional[EmotionLabel],
    ) -> QuestionStrategy:
        """
        Automatically select the most appropriate question strategy.
        """
        # Check last participant response for signals
        if history:
            last_response = history[-1].participant_response.lower()

            # Distress signals → empathize first
            if (last_emotion in [EmotionLabel.DISTRESSED, EmotionLabel.SAD]
                    or any(kw in last_response for kw in self.DISTRESS_KEYWORDS)):
                return QuestionStrategy.EMPATHIZE

            # Confusion signals → explain
            if any(kw in last_response for kw in self.CONFUSION_KEYWORDS):
                return QuestionStrategy.EXPLAIN

        # Default → probe
        return QuestionStrategy.PROBE

    def _generate_with_llm(
        self,
        node: MiniNode,
        history: list[ConversationTurn],
        strategy: QuestionStrategy,
    ) -> str:
        """
        Use the LLM to generate a contextually appropriate question.
        """
        # Build conversation context (last 4 turns max to keep prompt short)
        context_lines = []
        for turn in history[-4:]:
            context_lines.append(f"Interviewer: {turn.agent_utterance}")
            context_lines.append(f"Participant: {turn.participant_response}")
        context_str = "\n".join(context_lines) if context_lines else "This is the start of the interview."

        strategy_instructions = {
            QuestionStrategy.PROBE: (
                "Generate a conversational, non-clinical question that probes "
                "for the presence of this symptom. Rephrase the clinical language "
                "into everyday words. Keep it to 1-2 sentences."
            ),
            QuestionStrategy.EXPLAIN: (
                "The participant seems confused about the clinical concept. "
                "First briefly explain what the term means in everyday language, "
                "then ask the question again clearly. Keep it friendly and simple."
            ),
            QuestionStrategy.EMPATHIZE: (
                "The participant seems distressed. First acknowledge their feelings "
                "with genuine empathy (1 sentence). Then gently transition back "
                "to the diagnostic question. Do not push hard — be supportive."
            ),
        }

        messages = [
            system_message(SYSTEM_PROMPTS["question"]),
            user_message(f"""
Current diagnostic node:
- Node ID: {node.node_id}
- Criterion being assessed: {node.clinical_criterion}
- Question intent: {node.question_intent}
- Example question (for reference, do NOT copy verbatim): {node.example_question}

Strategy to use: {strategy.value.upper()}
Instructions: {strategy_instructions[strategy]}

Recent conversation history:
{context_str}

Generate the next interviewer message. Output ONLY the message text, no labels or JSON.
"""),
        ]

        response = self.llm.call(messages, temperature=0.85, max_tokens=200)

        if response.success and response.content.strip():
            return response.content.strip()

        # Fallback: use the example question from the node definition
        return node.example_question

    def generate_transition_message(
        self,
        from_disorder: str,
        to_disorder: str,
    ) -> str:
        """
        Generate a smooth transition message when moving between disorder sections.
        """
        disorder_names = {
            "depression": "mood",
            "generalized_anxiety": "anxiety and worry",
            "social_anxiety": "social situations",
            "suicide_risk": "personal safety",
        }

        from_name = disorder_names.get(from_disorder, from_disorder)
        to_name = disorder_names.get(to_disorder, to_disorder)

        messages = [
            system_message(SYSTEM_PROMPTS["question"]),
            user_message(
                f"Generate a brief, warm transition sentence to move from "
                f"questions about {from_name} to questions about {to_name}. "
                f"Keep it to 1-2 sentences. Be natural and reassuring."
            ),
        ]

        response = self.llm.call(messages, temperature=0.7, max_tokens=100)

        if response.success and response.content.strip():
            return response.content.strip()

        return (
            f"Thank you for sharing that. I'd like to ask you about some "
            f"different experiences now."
        )

    def generate_opening_message(self) -> str:
        """Generate the interview opening message."""
        messages = [
            system_message(SYSTEM_PROMPTS["question"]),
            user_message(
                "Generate a warm, welcoming opening message for a mental health "
                "screening interview. Explain that the conversation is confidential, "
                "that there are no right or wrong answers, and that they should "
                "answer as honestly as they feel comfortable. Keep it to 3-4 sentences."
            ),
        ]

        response = self.llm.call(messages, temperature=0.7, max_tokens=150)

        if response.success and response.content.strip():
            return response.content.strip()

        return (
            "Welcome. This is a confidential mental health screening conversation. "
            "There are no right or wrong answers — please share whatever you feel "
            "comfortable with. We'll go through some questions together about how "
            "you've been feeling recently."
        )

    def generate_closing_message(self) -> str:
        """Generate the interview closing message."""
        messages = [
            system_message(SYSTEM_PROMPTS["question"]),
            user_message(
                "Generate a warm, supportive closing message for a mental health "
                "screening interview. Thank the participant, acknowledge their courage "
                "in sharing, mention that results will be reviewed, and remind them "
                "that support is available. Keep it to 3-4 sentences."
            ),
        ]

        response = self.llm.call(messages, temperature=0.7, max_tokens=150)

        if response.success and response.content.strip():
            return response.content.strip()

        return (
            "Thank you so much for sharing with me today. It takes real courage "
            "to talk about these experiences. Your responses will be carefully "
            "reviewed, and appropriate support will be recommended based on "
            "what you've shared."
        )

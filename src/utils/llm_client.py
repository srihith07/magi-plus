"""
llm_client.py
-------------
A clean wrapper around the OpenAI API (or any compatible LLM).

All agents in MAGI+ call LLMs through this single module.
This makes it easy to:
  - Switch between GPT-4o, DeepSeek, or a local model (Ollama)
  - Log all LLM calls for reproducibility
  - Track token usage for experiments
  - Handle errors consistently
"""

from __future__ import annotations
import os
import json
import time
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()

# ─────────────────────────────────────────────
# PROVIDER DETECTION
# ─────────────────────────────────────────────

def _detect_provider() -> tuple[str, str]:
    """
    Detect API provider from the key prefix and return (api_key, base_url).
    Supports OpenAI, NVIDIA NIM, DeepSeek, and Groq.
    """
    key = os.getenv("OPENAI_API_KEY", "")
    if key.startswith("nvapi-"):
        return key, "https://integrate.api.nvidia.com/v1"
    if key.startswith("sk-") and len(key) == 35:
        return key, "https://api.deepseek.com/v1"
    if key.startswith("gsk_"):
        return key, "https://api.groq.com/openai/v1"
    # Default: OpenAI
    return key, "https://api.openai.com/v1"

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

_API_KEY, _BASE_URL = _detect_provider()

_PROVIDER_DEFAULTS = {
    "https://integrate.api.nvidia.com/v1":  "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
    "https://api.deepseek.com/v1":          "deepseek-chat",
    "https://api.groq.com/openai/v1":       "llama-3.1-8b-instant",
    "https://api.openai.com/v1":            "gpt-4o",
}
_DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", _PROVIDER_DEFAULTS.get(_BASE_URL, "gpt-4o"))

class LLMConfig(BaseModel):
    """Configuration for the LLM client."""
    model: str = _DEFAULT_MODEL
    temperature: float = 0.7
    max_tokens: int = 1024
    timeout: int = 30          # Groq is fast; 30s is plenty
    max_retries: int = 3


# ─────────────────────────────────────────────
# LLM RESPONSE
# ─────────────────────────────────────────────

class LLMResponse(BaseModel):
    """Structured response from the LLM."""
    content: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None


# ─────────────────────────────────────────────
# MESSAGE BUILDER
# ─────────────────────────────────────────────

def system_message(content: str) -> dict:
    """Create a system message dict."""
    return {"role": "system", "content": content}


def user_message(content: str) -> dict:
    """Create a user message dict."""
    return {"role": "user", "content": content}


def assistant_message(content: str) -> dict:
    """Create an assistant message dict."""
    return {"role": "assistant", "content": content}


# ─────────────────────────────────────────────
# MAIN CLIENT
# ─────────────────────────────────────────────

class LLMClient:
    """
    Wrapper around the OpenAI API.
    All agents in MAGI+ use this to call the LLM.
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        api_key, base_url = _detect_provider()
        if not api_key:
            print("WARNING: OPENAI_API_KEY not found. Create a .env file with your key.")
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self._base_url = base_url
        self._is_nvidia_nim = "nvidia.com" in base_url
        self._is_deepseek   = "deepseek.com" in base_url
        self._is_groq       = "groq.com" in base_url
        # These providers need prompt-injected JSON (no response_format support)
        self._use_prompt_json = self._is_nvidia_nim or self._is_deepseek
        self._call_log: list[dict] = []

        provider = (
            "NVIDIA NIM" if self._is_nvidia_nim
            else "DeepSeek" if self._is_deepseek
            else "Groq"    if self._is_groq
            else "OpenAI"
        )
        print(f"[LLMClient] Provider: {provider} → {self.config.model}")

    def call(
        self,
        messages: list[dict],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        """
        Send messages to the LLM and return a structured response.

        Args:
            messages: List of message dicts (system/user/assistant)
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            json_mode: If True, force JSON output (response_format)

        Returns:
            LLMResponse with content and token usage
        """
        temp = temperature if temperature is not None else self.config.temperature
        tokens = max_tokens if max_tokens is not None else self.config.max_tokens

        kwargs = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temp,
            "max_tokens": tokens,
        }

        # response_format=json_object only supported on OpenAI, not NIM/DeepSeek
        # For those providers we inject a JSON instruction into the prompt instead
        if json_mode and not self._use_prompt_json:
            kwargs["response_format"] = {"type": "json_object"}

        for attempt in range(1, self.config.max_retries + 1):
            try:
                start = time.time()
                response = self.client.chat.completions.create(**kwargs)
                elapsed_ms = (time.time() - start) * 1000

                content = response.choices[0].message.content or ""
                # Reasoning models (NIM) may put output in reasoning_content
                if not content:
                    rc = getattr(response.choices[0].message, 'reasoning_content', None)
                    if rc:
                        content = rc

                # Strip chain-of-thought "thinking" that reasoning models
                # sometimes leak into content. Keep only text after the
                # last occurrence of a natural answer delimiter.
                content = self._strip_reasoning_traces(content)
                result = LLMResponse(
                    content=content,
                    model=response.model,
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                    latency_ms=round(elapsed_ms, 1),
                    success=True,
                )

                # Log the call
                self._call_log.append({
                    "model": self.config.model,
                    "messages_count": len(messages),
                    "tokens": result.total_tokens,
                    "latency_ms": result.latency_ms,
                })

                return result

            except Exception as e:
                if attempt == self.config.max_retries:
                    return LLMResponse(
                        content="",
                        model=self.config.model,
                        success=False,
                        error=str(e),
                    )
                wait = 2 ** attempt  # Exponential backoff
                print(f"LLM call failed (attempt {attempt}), retrying in {wait}s: {e}")
                time.sleep(wait)

        # Should never reach here
        return LLMResponse(content="", model=self.config.model, success=False)

    def call_with_json(self, messages: list[dict], **kwargs) -> dict:
        """
        Call the LLM and parse the response as JSON.
        For NVIDIA NIM, injects a JSON instruction since response_format is unsupported.
        Returns empty dict on failure.
        """
        # For NIM/DeepSeek: inject JSON instruction into last user message
        if self._use_prompt_json:
            msgs = list(messages)
            if msgs and msgs[-1]["role"] == "user":
                msgs[-1] = {
                    "role": "user",
                    "content": msgs[-1]["content"] + "\n\nIMPORTANT: Respond with ONLY valid JSON. No markdown, no explanation, no code blocks. Pure JSON only."
                }
            response = self.call(msgs, json_mode=False, **kwargs)
        else:
            response = self.call(messages, json_mode=True, **kwargs)

        if not response.success or not response.content:
            return {}

        # Extract JSON — handle markdown code blocks if model wraps it
        content = response.content.strip()
        # Strip ```json ... ``` wrappers if present
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(
                l for l in lines
                if not l.strip().startswith("```")
            ).strip()

        # Find first { to last } to extract JSON object
        start = content.find("{")
        end = content.rfind("}") + 1
        if start != -1 and end > start:
            content = content[start:end]
        elif start != -1:
            # JSON was truncated — attempt to close it
            content = self._repair_truncated_json(content[start:])

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}\nContent: {content[:300]}")
            return {}

    def _repair_truncated_json(self, content: str) -> str:
        """
        Attempt to repair truncated JSON by closing open brackets/braces/strings.
        Works for simple truncation cases (model hit max_tokens mid-JSON).
        """
        # Count open vs close braces/brackets
        stack = []
        in_string = False
        escape_next = False
        repaired = list(content)

        for ch in content:
            if escape_next:
                escape_next = False
                continue
            if ch == '\\' and in_string:
                escape_next = True
                continue
            if ch == '"' and not in_string:
                in_string = True
            elif ch == '"' and in_string:
                in_string = False
            elif not in_string:
                if ch in ('{', '['):
                    stack.append(ch)
                elif ch == '}' and stack and stack[-1] == '{':
                    stack.pop()
                elif ch == ']' and stack and stack[-1] == '[':
                    stack.pop()

        # Close any open string
        if in_string:
            repaired.append('"')

        # Close any open structures in reverse order
        for opener in reversed(stack):
            repaired.append('}' if opener == '{' else ']')

        return ''.join(repaired)

    def _strip_reasoning_traces(self, content: str) -> str:
        """
        Reasoning models (like Nemotron) sometimes output their step-by-step
        thinking before giving the final answer. This method strips that preamble
        and returns only the clean final answer.

        Heuristics used:
        - If content contains 'Thus answer:', return everything after it
        - If content contains 'Thus:', return everything after it
        - If the first line looks like reasoning (starts with 'We need to'),
          find the last quoted string or last paragraph as the real answer
        - For JSON requests: find the first '{' to last '}'
        """
        if not content:
            return content

        # Common reasoning-to-answer transition phrases
        for marker in [
            "Thus answer:", "Thus, answer:", "Thus output:", "Thus:",
            "Answer:", "Final answer:", "Output:", "My response:",
            "Let me output:", "So the output is:", "The answer is:"
        ]:
            idx = content.rfind(marker)
            if idx != -1:
                return content[idx + len(marker):].strip().strip('"').strip("'")

        # If it looks like step-by-step reasoning, take the last paragraph
        lines = [l.strip() for l in content.strip().split('\n') if l.strip()]
        if lines and any(
            lines[0].startswith(p)
            for p in ["We need", "I need", "Let's", "The user", "First,", "Step"]
        ):
            # Take the last non-empty line/paragraph as the actual answer
            # But if last part is quoted, extract the quote
            last_block = lines[-1] if lines else content
            # Remove leading quotes
            if last_block.startswith('"') and last_block.endswith('"'):
                return last_block[1:-1]
            return last_block

        return content

    def get_usage_summary(self) -> dict:
        """Return a summary of all LLM calls made in this session."""
        if not self._call_log:
            return {"total_calls": 0, "total_tokens": 0, "avg_latency_ms": 0}
        return {
            "total_calls": len(self._call_log),
            "total_tokens": sum(c["tokens"] for c in self._call_log),
            "avg_latency_ms": round(
                sum(c["latency_ms"] for c in self._call_log) / len(self._call_log), 1
            ),
        }


# ─────────────────────────────────────────────
# SYSTEM PROMPTS (shared across agents)
# ─────────────────────────────────────────────

SYSTEM_PROMPTS = {
    "navigation": """You are the Navigation Agent in a psychiatric interview system.
Your role is to manage the interview flow following the MINI (Mini International
Neuropsychiatric Interview) protocol strictly. You determine which question node
to visit next based on participant responses and the diagnostic decision tree.
You ensure no critical diagnostic nodes are skipped.
Always output valid JSON.""",

    "question": """You are the Question Agent in a psychiatric interview system.
Your role is to ask questions to participants in a way that is empathetic,
clear, and aligned with the current diagnostic node.
You have three strategies:
1. PROBE: Ask directly about a symptom in a conversational, non-clinical way
2. EXPLAIN: Clarify a clinical concept the participant seems confused about
3. EMPATHIZE: Provide emotional support when distress is detected, then gently
   redirect to the diagnostic question
Always maintain a warm, respectful, non-judgmental tone.""",

    "judgment": """You are the Judgment Agent in a psychiatric interview system.
Your role is to evaluate whether a participant's response meets the criteria
for a specific MINI diagnostic node.
You assess responses against three thresholds:
1. Direct match: The response clearly meets or denies the criterion
2. Semantic match: The response implies the criterion in different words
3. Ambiguous: The response is unclear — flag for clarification
Always output valid JSON with your assessment.""",

    "diagnosis": """You are the Diagnosis Agent in a psychiatric interview system.
Your role is to synthesize all collected evidence into a DSM-5 compliant
diagnosis using PsyCoT (Psychometric Chain-of-Thought) reasoning.
You must reason through three phases:
1. Symptom Anchoring: Confirm each criterion with evidence from the dialogue
2. Diagnostic Synthesis: Verify the symptom profile meets the threshold
3. Evidence Binding: Create an auditable trail linking dialogue to diagnosis
Always be transparent, explicit, and clinically rigorous in your reasoning.
Always output valid JSON.""",

    "recommendation": """You are the Recommendation Agent in a psychiatric interview system.
Your role is to translate diagnostic results and severity scores into
evidence-based, actionable treatment recommendations.
You follow a tiered approach:
- Mild: Self-help resources, psychoeducation, lifestyle changes
- Moderate: Outpatient therapy (CBT, DBT), online counseling
- Moderate-Severe: Psychiatric consultation, possible medication
- Severe/Crisis: Immediate intervention, crisis hotlines, emergency referral
Always prioritize participant safety. If severe suicide risk is detected,
immediately flag for crisis intervention.
Always output valid JSON.""",

    "emotion": """You are an emotion analysis agent in a psychiatric interview system.
Your role is to assess the emotional state of a participant from their text response.
Classify the emotion as one of: neutral, anxious, sad, distressed, hopeful,
avoidant, angry, confused.
Also rate the intensity from 0.0 (very mild) to 1.0 (very intense).
Always output valid JSON.""",
}


# ─────────────────────────────────────────────
# QUICK TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    client = LLMClient()
    response = client.call([
        system_message("You are a helpful assistant."),
        user_message("Say hello in one sentence."),
    ])
    if response.success:
        print(f"Response: {response.content}")
        print(f"Tokens used: {response.total_tokens}")
    else:
        print(f"Error: {response.error}")

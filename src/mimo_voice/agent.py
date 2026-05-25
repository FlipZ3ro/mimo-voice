"""Voice agent: reasoning loop with conversation memory + TTS reply."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from mimo_voice.tts import TTS, TTSResult


@dataclass
class Turn:
    role: str
    content: str


@dataclass
class VoiceAgent:
    persona: str = "helpful assistant"
    voice: str | None = None
    memory: list[Turn] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.api_key = os.environ.get("MIMO_API_KEY")
        if not self.api_key:
            raise RuntimeError("MIMO_API_KEY missing — see .env.example")
        base = os.environ.get("MIMO_BASE_URL", "https://token-plan-sgp.xiaomimimo.com/v1")
        self._client = OpenAI(api_key=self.api_key, base_url=base)
        self._reason_model = os.environ.get("MIMO_REASONING_MODEL", "mimo-v2.5-pro")
        self._tts = TTS()
        self._budget = int(os.environ.get("VOICE_MEMORY_BUDGET", "4000"))

    def _system_prompt(self) -> str:
        return (
            f"You are a voice agent with persona: {self.persona}. "
            "Reply in short, conversational sentences (<= 60 words). Avoid "
            "markdown, lists, or symbols that don't read well aloud. Be warm "
            "but concise."
        )

    def _trim_memory(self) -> None:
        # Cheap heuristic: drop oldest turns until under budget
        while sum(len(t.content) for t in self.memory) > self._budget and len(self.memory) > 2:
            self.memory.pop(0)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=15))
    def _reason(self, user_text: str) -> str:
        self.memory.append(Turn("user", user_text))
        self._trim_memory()
        messages = [{"role": "system", "content": self._system_prompt()}]
        messages += [{"role": t.role, "content": t.content} for t in self.memory]
        r = self._client.chat.completions.create(
            model=self._reason_model,
            messages=messages,
            max_tokens=400,
            temperature=0.4,
        )
        reply = (r.choices[0].message.content or "").strip()
        self.memory.append(Turn("assistant", reply))
        return reply

    def respond(self, user_text: str) -> tuple[str, TTSResult]:
        reply = self._reason(user_text)
        audio = self._tts.speak(reply, voice=self.voice)
        return reply, audio

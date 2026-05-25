"""TTS wrapper: stock, voice-clone, voice-design.

Built against the OpenAI-compatible `/audio/speech` contract. If the endpoint
is not yet exposed on a given base URL (e.g. token-plan-sgp.xiaomimimo.com at
this time), the wrapper surfaces a clear error so callers can configure an
alternate `MIMO_BASE_URL` once the audio cluster is enabled for the plan.
"""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from pathlib import Path

import requests
from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass
class TTSResult:
    audio_bytes: bytes
    content_type: str
    model: str
    voice: str


class TTSError(RuntimeError):
    pass


class TTS:
    def __init__(self) -> None:
        self.api_key = os.environ.get("MIMO_API_KEY")
        if not self.api_key:
            raise RuntimeError("MIMO_API_KEY missing — see .env.example")
        self.base_url = os.environ.get(
            "MIMO_BASE_URL", "https://token-plan-sgp.xiaomimimo.com/v1"
        ).rstrip("/")
        self.default_voice = os.environ.get("VOICE_DEFAULT_VOICE", "alloy")
        self.fmt = os.environ.get("VOICE_OUTPUT_FORMAT", "mp3")

    def _models(self) -> dict[str, str]:
        return {
            "stock":        os.environ.get("MIMO_TTS_MODEL", "mimo-v2.5-tts"),
            "voiceclone":   os.environ.get("MIMO_TTS_VOICECLONE_MODEL", "mimo-v2.5-tts-voiceclone"),
            "voicedesign":  os.environ.get("MIMO_TTS_VOICEDESIGN_MODEL", "mimo-v2.5-tts-voicedesign"),
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=15))
    def _post(self, body: dict) -> TTSResult:
        url = f"{self.base_url}/audio/speech"
        r = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=60,
        )
        if not r.ok:
            raise TTSError(f"TTS {r.status_code} on {url}: {r.text[:300]}")
        return TTSResult(
            audio_bytes=r.content,
            content_type=r.headers.get("Content-Type", "audio/mpeg"),
            model=body["model"],
            voice=str(body.get("voice", "")),
        )

    def speak(self, text: str, voice: str | None = None) -> TTSResult:
        return self._post({
            "model": self._models()["stock"],
            "input": text,
            "voice": voice or self.default_voice,
            "response_format": self.fmt,
        })

    def clone(self, text: str, reference_path: str | Path) -> TTSResult:
        ref = Path(reference_path).read_bytes()
        return self._post({
            "model": self._models()["voiceclone"],
            "input": text,
            "voice_reference": base64.b64encode(ref).decode(),
            "response_format": self.fmt,
        })

    def design(self, text: str, voice_prompt: str) -> TTSResult:
        return self._post({
            "model": self._models()["voicedesign"],
            "input": text,
            "voice_prompt": voice_prompt,
            "response_format": self.fmt,
        })

    @staticmethod
    def save(result: TTSResult, path: str | Path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(result.audio_bytes)
        return p

"""End-to-end smoke test: synthesize a single phrase."""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

from mimo_voice.tts import TTS, TTSError


def main() -> int:
    load_dotenv()
    tts = TTS()
    text = "Hello. This is a voice synthesised by MiMo TTS via the open MiMo-Voice stack."
    try:
        res = tts.speak(text)
    except TTSError as e:
        print(f"TTS endpoint not exposed on this base URL yet: {e}", file=sys.stderr)
        return 1
    out = Path(__file__).resolve().parent.parent / "out" / "hello.mp3"
    TTS.save(res, out)
    print(f"wrote {out} ({len(res.audio_bytes)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

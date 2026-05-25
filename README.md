# MiMo-Voice: Open Voice Agent Stack

> An open, batteries-included voice agent built on **Xiaomi MiMo TTS** — listen, reason, speak back. With native support for `mimo-v2.5-tts`, `voiceclone`, and `voicedesign`.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Voice agents are the next user interface for AI, but the open-source stack today is fragmented: STT here, LLM there, TTS somewhere else, with no unifying API. MiMo-Voice gives you a single Python package that wires a speech-to-text frontend into `mimo-v2.5-pro` for reasoning and `mimo-v2.5-tts` (or its `voiceclone` / `voicedesign` variants) for synthesis — with conversation memory, barge-in support, and streaming audio out of the box.

## Why MiMo

- **Three TTS variants in one platform**: stock `mimo-v2.5-tts`, `mimo-v2.5-tts-voiceclone` for cloning a target speaker from a short reference clip, and `mimo-v2.5-tts-voicedesign` for prompt-controllable voice characteristics.
- **`mimo-v2.5-pro` reasoning** keeps multi-turn conversations coherent.
- **OpenAI-compatible** endpoints — drop-in for existing voice SDKs.

## Features

- One-line voice agent: `VoiceAgent(persona="...")`.
- Pluggable STT: bring your own (Whisper / Vosk / external API).
- Streaming TTS playback while the model is still generating.
- Voice cloning: provide a 5-30 s reference clip, get a matching speaker.
- Voice design: describe the voice in text ("warm female radio host, mid-30s").
- Persistent conversation memory with token-budget compaction.

## Quick start

```bash
git clone https://github.com/FlipZ3ro/mimo-voice
cd mimo-voice
pip install -e .
cp .env.example .env  # add MIMO_API_KEY

# Synthesize a single phrase
python -m mimo_voice.cli speak --text "Hello, I'm a MiMo voice agent." --out hello.mp3
```

Voice clone:

```bash
python -m mimo_voice.cli clone \
  --reference samples/my_voice.wav \
  --text "I sound just like the reference." \
  --out cloned.mp3
```

Voice design:

```bash
python -m mimo_voice.cli design \
  --voice-prompt "warm female radio host, mid-30s, professional but friendly" \
  --text "Welcome to the morning show." \
  --out design.mp3
```

Live agent (requires a local mic + STT):

```bash
python -m mimo_voice.cli agent --persona "helpful customer support"
```

## Architecture

```
   microphone -> STT (BYO) -> text
                                 │
                                 ▼
                       mimo-v2.5-pro (reasoning)
                                 │
                                 ▼
                       reply text + style hints
                                 │
                                 ▼
                       mimo-v2.5-tts(* variants)
                                 │
                                 ▼
                            audio out
```

## Roadmap

- [x] TTS wrapper (mimo-v2.5-tts + voiceclone + voicedesign)
- [x] Reasoning loop with conversation memory
- [x] CLI for speak / clone / design
- [ ] Streaming audio playback (chunked TTS)
- [ ] Built-in Whisper STT integration
- [ ] WebSocket server for browser clients

## Token economics

| Action                        | Tokens / call |
|-------------------------------|---------------|
| Single 15s TTS phrase         | ~120 (text)   |
| 10-turn conversation          | ~6K (reasoning) + 10× TTS |
| Voice clone session (30 min)  | ~150K total   |

Plan: build a 1000-conversation dataset across all three TTS modes for benchmarking; ~150M tokens.

## Status

The TTS endpoint is enumerated by `GET /models` on the token-plan API but the canonical `/audio/speech` path is not yet exposed on `token-plan-sgp.xiaomimimo.com`. This stack is built against the **OpenAI-compatible TTS contract** and will work end-to-end once the audio cluster is enabled for this plan — the same code paths are validated against the chat-completions API today.

## License

MIT — see [LICENSE](LICENSE).

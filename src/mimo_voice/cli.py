"""mimo-voice CLI: speak / clone / design / agent."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console

from mimo_voice.agent import VoiceAgent
from mimo_voice.tts import TTS, TTSError


def cmd_speak(args: argparse.Namespace) -> int:
    tts = TTS()
    res = tts.speak(args.text, voice=args.voice)
    out = TTS.save(res, args.out)
    print(f"wrote {out} ({len(res.audio_bytes)} bytes, ct={res.content_type})")
    return 0


def cmd_clone(args: argparse.Namespace) -> int:
    tts = TTS()
    res = tts.clone(args.text, args.reference)
    out = TTS.save(res, args.out)
    print(f"wrote {out} ({len(res.audio_bytes)} bytes)")
    return 0


def cmd_design(args: argparse.Namespace) -> int:
    tts = TTS()
    res = tts.design(args.text, args.voice_prompt)
    out = TTS.save(res, args.out)
    print(f"wrote {out} ({len(res.audio_bytes)} bytes)")
    return 0


def cmd_agent(args: argparse.Namespace) -> int:
    console = Console()
    ag = VoiceAgent(persona=args.persona, voice=args.voice)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    i = 0
    console.print(f"[bold]voice agent[/] persona={args.persona!r}. Type messages, Ctrl-C to quit.\n")
    while True:
        try:
            text = console.input("[cyan]you[/] ")
        except (EOFError, KeyboardInterrupt):
            return 0
        if not text.strip():
            continue
        try:
            reply, audio = ag.respond(text)
        except TTSError as e:
            console.print(f"[yellow]reasoning ok, TTS unavailable on this base URL[/]: {e}")
            continue
        i += 1
        out = out_dir / f"reply_{i:03d}.{TTS().fmt}"
        TTS.save(audio, out)
        console.print(f"[green]bot[/] {reply}")
        console.print(f"  [dim]audio -> {out}[/]\n")


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    p = argparse.ArgumentParser(prog="mimo-voice")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("speak")
    s.add_argument("--text", required=True)
    s.add_argument("--voice", default=None)
    s.add_argument("--out", default="out/speak.mp3")
    s.set_defaults(func=cmd_speak)

    c = sub.add_parser("clone")
    c.add_argument("--reference", required=True)
    c.add_argument("--text", required=True)
    c.add_argument("--out", default="out/clone.mp3")
    c.set_defaults(func=cmd_clone)

    d = sub.add_parser("design")
    d.add_argument("--voice-prompt", required=True)
    d.add_argument("--text", required=True)
    d.add_argument("--out", default="out/design.mp3")
    d.set_defaults(func=cmd_design)

    a = sub.add_parser("agent")
    a.add_argument("--persona", default="helpful assistant")
    a.add_argument("--voice", default=None)
    a.add_argument("--out-dir", default="out/agent")
    a.set_defaults(func=cmd_agent)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

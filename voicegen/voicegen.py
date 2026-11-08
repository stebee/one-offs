#!/usr/bin/env python3
"""Generate speech from text via OpenRouter's TTS API."""

import argparse
import os
import sys
import tomllib
from pathlib import Path

import requests
from dotenv import find_dotenv, load_dotenv


def load_config(path: str) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def read_input(args: argparse.Namespace, config: dict) -> str:
    if args.input:
        return Path(args.input).read_text(encoding="utf-8").strip()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    if "script" in config:
        return config["script"].strip()
    print(
        "Error: no input text — use -i, pipe via stdin, or set 'script' in config.",
        file=sys.stderr,
    )
    sys.exit(1)


def play_audio(path: Path) -> None:
    import platform
    import subprocess

    system = platform.system()
    if system == "Darwin":
        subprocess.run(["afplay", str(path)], check=True)
        return

    # Windows and Linux: try command-line players first (blocking), fall back to OS default.
    candidates = [
        (["ffplay", "-nodisp", "-autoexit", str(path)], "ffplay"),
        (["mpg123", str(path)], "mpg123"),
        (["mpg321", str(path)], "mpg321"),
    ]
    probe = "where" if system == "Windows" else "which"
    for cmd, exe in candidates:
        if subprocess.run([probe, exe], capture_output=True).returncode == 0:
            subprocess.run(cmd, check=True)
            return

    # Last resort on Windows: open with default media app (async).
    if system == "Windows":
        os.startfile(str(path))
    else:
        print("Warning: no audio player found; install ffmpeg or mpg123.", file=sys.stderr)


def main() -> None:
    load_dotenv(find_dotenv(usecwd=True))

    parser = argparse.ArgumentParser(description="Generate speech from text via OpenRouter TTS.")
    parser.add_argument(
        "--config", default="voicegen.toml", metavar="FILE",
        help="TOML config file (default: voicegen.toml)",
    )
    parser.add_argument("-i", metavar="FILE", dest="input",
                        help="Input text file (default: stdin or config 'script')")
    parser.add_argument("-o", metavar="FILE", dest="output", default="voicegen.mp3",
                        help="Output audio file (default: voicegen.mp3)")
    parser.add_argument("-p", action="store_true", dest="play",
                        help="Play audio immediately after generating")
    args = parser.parse_args()

    config = load_config(args.config)

    api_key = os.environ.get("VOICEGEN_OPENROUTER_KEY") or os.environ.get("OPENROUTER_KEY")
    if not api_key:
        print("Error: set VOICEGEN_OPENROUTER_KEY or OPENROUTER_KEY in .env", file=sys.stderr)
        sys.exit(1)

    text = read_input(args, config)
    if config.get("stageDirections"):
        text = config["stageDirections"] + "\n\n" + text

    response = requests.post(
        "https://openrouter.ai/api/v1/audio/speech",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": config["model"],
            "input": text,
            "voice": config["voice"],
            "response_format": "mp3",
        },
        timeout=120,
    )

    if not response.ok:
        print(f"Error {response.status_code}: {response.text}", file=sys.stderr)
        sys.exit(1)

    content_type = response.headers.get("Content-Type", "")
    if not content_type.startswith("audio/"):
        print(
            f"Error: expected audio response but got Content-Type: {content_type!r}\n"
            f"Body: {response.text}",
            file=sys.stderr,
        )
        sys.exit(1)

    output_path = Path(args.output)
    output_path.write_bytes(response.content)
    print(f"Saved to {output_path}", file=sys.stderr)

    if args.play:
        play_audio(output_path)


if __name__ == "__main__":
    main()

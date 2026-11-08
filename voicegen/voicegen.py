#!/usr/bin/env python3
"""Generate speech from text via OpenRouter's TTS API."""

import argparse
import os
import platform
import subprocess
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


def _has_cmd(name: str) -> bool:
    probe = "where" if platform.system() == "Windows" else "which"
    return subprocess.run([probe, name], capture_output=True).returncode == 0


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

    print("Generating...", end="", flush=True, file=sys.stderr)

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
        stream=True,
        timeout=120,
    )

    if not response.ok:
        print(f"\nError {response.status_code}: {response.text}", file=sys.stderr)
        sys.exit(1)

    content_type = response.headers.get("Content-Type", "")
    if not content_type.startswith("audio/"):
        print(
            f"\nError: expected audio response but got Content-Type: {content_type!r}\n"
            f"Body: {response.text}",
            file=sys.stderr,
        )
        sys.exit(1)

    output_path = Path(args.output)
    use_ffplay = args.play and _has_cmd("ffplay")

    # When streaming to ffplay, start the process now so audio plays as chunks arrive.
    ffplay_proc = None
    if use_ffplay:
        print(" streaming.", file=sys.stderr)
        ffplay_proc = subprocess.Popen(
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "error", "-"],
            stdin=subprocess.PIPE,
        )

    received = 0
    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=4096):
            if chunk:
                f.write(chunk)
                received += len(chunk)
                if ffplay_proc:
                    ffplay_proc.stdin.write(chunk)
                else:
                    print(f"\r{received // 1024} KB...", end="", flush=True, file=sys.stderr)

    if ffplay_proc:
        ffplay_proc.stdin.close()
        ffplay_proc.wait()
        print(f"Saved {output_path} ({received // 1024} KB)", file=sys.stderr)
    else:
        print(f"\rSaved {output_path} ({received // 1024} KB)", file=sys.stderr)
        if args.play:
            # ffplay not available; try other blocking players then fall back to OS default.
            system = platform.system()
            for cmd, exe in [
                (["mpg123", str(output_path)], "mpg123"),
                (["mpg321", str(output_path)], "mpg321"),
            ]:
                if _has_cmd(exe):
                    subprocess.run(cmd, check=True)
                    break
            else:
                if system == "Windows":
                    os.startfile(str(output_path))
                else:
                    print("Warning: no audio player found; install ffmpeg or mpg123.", file=sys.stderr)


if __name__ == "__main__":
    main()

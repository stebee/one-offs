#!/usr/bin/env python3
"""Generate per-line MP3 files from a script file using voicegen."""

import argparse
import re
import subprocess
import sys
from pathlib import Path

VOICEGEN_DIR = Path(__file__).parent.parent / "voicegen"
VOICEGEN_PY = VOICEGEN_DIR / "voicegen.py"
VOICEGEN_CONFIG = VOICEGEN_DIR / "voicegen.toml"

SFX_PATTERN = re.compile(r"\[([^\]]+)\]")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate per-line MP3s from a script file via voicegen."
    )
    parser.add_argument("-i", required=True, metavar="FILE", dest="input",
                        help="Script file (one line of dialogue per line)")
    parser.add_argument("-o", required=True, metavar="DIR", dest="output",
                        help="Destination folder for MP3 files")
    parser.add_argument("--oops", action="store_true",
                        help="Only process lines that contain SFX placeholders (skips all others)")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    lines = Path(args.input).read_text(encoding="utf-8").splitlines()

    for lineno, line in enumerate(lines, start=1):
        if not line.strip():
            continue

        sfx_match = SFX_PATTERN.search(line)

        if args.oops and not sfx_match:
            continue
        if not args.oops and not sfx_match:
            spoken = line
        else:
            print(f"File {lineno}.mp3 needs [{sfx_match.group(1)}] SFX.")
            spoken = SFX_PATTERN.sub("", line).strip()
            if not spoken:
                continue

        output_file = output_dir / f"{lineno}.mp3"
        result = subprocess.run(
            [
                sys.executable, str(VOICEGEN_PY),
                "--config", str(VOICEGEN_CONFIG),
                "-o", str(output_file),
            ],
            input=spoken,
            text=True,
        )
        if result.returncode != 0:
            print(f"Error on line {lineno}; aborting.", file=sys.stderr)
            sys.exit(result.returncode)


if __name__ == "__main__":
    main()

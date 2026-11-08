#!/usr/bin/env bash
# Rename files whose numeric stem is shorter than 6 characters by adding leading zeros.
# Usage: pad-filenames.sh [directory]   (default: current directory)

set -euo pipefail

dir="${1:-.}"

for f in "$dir"/*; do
    [[ -f "$f" ]] || continue
    base="${f##*/}"
    stem="${base%.*}"
    ext="${base#"$stem"}"
    [[ "$stem" =~ ^[0-9]+$ ]] || continue
    if (( ${#stem} < 5 )); then
        padded=$(printf '%05d' "$stem")
        mv -- "$f" "$dir/$padded$ext"
        echo "$base -> $padded$ext"
    fi
done

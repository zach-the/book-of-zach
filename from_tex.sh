#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ $# -eq 0 ]]; then
    echo "Usage: $0 FILE.tex" >&2
    exit 1
fi

TEX_FILE="$1"

latexmk -C -outdir="$SCRIPT_DIR" "$TEX_FILE"
latexmk -f -lualatex -outdir="$SCRIPT_DIR" "$TEX_FILE"

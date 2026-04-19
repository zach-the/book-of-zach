#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_NAME="output"
URLS=()

usage() {
    echo "Usage: $0 [-o OUTPUT_NAME] URL [URL ...]"
    echo
    echo "  -o OUTPUT_NAME   Base name for output files (default: output)"
    echo "                   Produces OUTPUT_NAME.pdf and OUTPUT_NAME_booklet.pdf"
    echo
    echo "Example:"
    echo "  $0 -o my_talks https://www.churchofjesuschrist.org/study/general-conference/..."
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -o|--output)
            OUTPUT_NAME="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        -*)
            echo "Unknown option: $1" >&2
            usage
            ;;
        *)
            URLS+=("$1")
            shift
            ;;
    esac
done

if [[ ${#URLS[@]} -eq 0 ]]; then
    echo "Error: at least one URL is required." >&2
    usage
fi

TEX_FILE="$SCRIPT_DIR/${OUTPUT_NAME}.tex"
PDF_FILE="$SCRIPT_DIR/${OUTPUT_NAME}.pdf"
BOOKLET_FILE="$SCRIPT_DIR/${OUTPUT_NAME}_booklet.pdf"

echo "==> Scraping ${#URLS[@]} URL(s)..."
python3 "$SCRIPT_DIR/scrape.py" "${URLS[@]}" -o "$TEX_FILE"

echo
echo "==> Compiling ${OUTPUT_NAME}.tex..."
latexmk -C -outdir="$SCRIPT_DIR" "$TEX_FILE"
latexmk -f -lualatex -outdir="$SCRIPT_DIR" "$TEX_FILE"

echo
echo "==> Bookletizing..."
latexmk -f -lualatex -outdir="$SCRIPT_DIR" \
    -usepretex="\def\filename{${OUTPUT_NAME}.pdf}" \
    "$SCRIPT_DIR/bookletize.tex"

mv "$SCRIPT_DIR/bookletize.pdf" "$BOOKLET_FILE"

echo
echo "==> Cleaning auxiliary files..."
latexmk -c -outdir="$SCRIPT_DIR" "$TEX_FILE"
latexmk -c -outdir="$SCRIPT_DIR" "$SCRIPT_DIR/bookletize.tex"

echo
echo "Done!"
echo "  Regular PDF : $PDF_FILE"
echo "  Booklet PDF : $BOOKLET_FILE"

#!/usr/bin/env bash
# Render experiments/<exp>/writeup.md to writeup.pdf next to it.
#
#   scripts/build-writeup.sh experiments/e01_closed_census_invariants [...]
#
# Pipeline: pandoc (Markdown -> self-contained HTML, math as MathML, figures
# inlined) -> headless Chromium (print to PDF). Needs pandoc and a Chromium /
# Chrome binary; set CHROME=/path/to/chrome to override discovery.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CSS="$ROOT/docs/writeup.css"

find_chrome() {
  for c in "${CHROME:-}" chromium chromium-browser google-chrome google-chrome-stable \
           /opt/pw-browsers/chromium; do
    [[ -n "$c" ]] && command -v "$c" >/dev/null 2>&1 && { command -v "$c"; return; }
  done
  echo "No Chromium/Chrome found; set CHROME=/path/to/chrome" >&2
  return 1
}
CHROME_BIN="$(find_chrome)"
command -v pandoc >/dev/null || { echo "pandoc not found (apt-get install pandoc)" >&2; exit 1; }

for dir in "$@"; do
  dir="$(cd "$dir" && pwd)"
  md="$dir/writeup.md"
  [[ -f "$md" ]] || { echo "skip: no $md" >&2; continue; }
  html="$(mktemp --suffix=.html)"
  # Run from the experiment dir so relative figure paths resolve.
  (cd "$dir" && pandoc writeup.md --standalone --mathml --embed-resources \
      --css "$CSS" --resource-path "$dir" -o "$html")
  "$CHROME_BIN" --headless --no-sandbox --disable-gpu --no-pdf-header-footer \
      --print-to-pdf="$dir/writeup.pdf" "file://$html" 2>/dev/null
  rm -f "$html"
  echo "wrote ${dir#"$ROOT"/}/writeup.pdf"
done

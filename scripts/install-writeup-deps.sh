#!/usr/bin/env bash
# Tools for building writeups: pandoc, and matplotlib for the system Python
# that imports regina. Chromium/Chrome must already be present (see
# scripts/build-writeup.sh for how it is located).
set -euo pipefail
if [[ $EUID -eq 0 ]]; then SUDO=""; else SUDO="sudo"; fi
export DEBIAN_FRONTEND=noninteractive
$SUDO apt-get install -y -qq --no-install-recommends pandoc python3-matplotlib >/dev/null
echo "pandoc $(pandoc --version | head -1 | cut -d' ' -f2); matplotlib for $(command -v python3)"

#!/usr/bin/env bash
# Idempotent setup for a fresh (cloud) session: Regina, the mtengine submodule and
# its venv (needed for the `mtengine` MCP server in .mcp.json).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
"$ROOT/scripts/install-regina-ubuntu.sh"
git -C "$ROOT" submodule update --init --quiet engine || echo "warning: could not fetch the engine submodule" >&2
if [[ -f "$ROOT/engine/pyproject.toml" && ! -x "$ROOT/engine/.venv/bin/mtengine-mcp" ]]; then
  make -C "$ROOT" --no-print-directory engine
fi

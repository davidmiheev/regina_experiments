"""Access to mtengine (the `engine/` submodule) from experiment scripts.

mtengine runs Regina in its own process (`regina-python`), caches results keyed by
(Regina version, function, input) and attaches provenance, so experiments call it instead
of re-implementing Regina plumbing. Its API needs only the standard library, so it is
imported straight from the submodule, with no venv. The `mtengine` MCP server in .mcp.json
exposes the same functions to Claude.

    from rexp.engine import mte, value
    walk = value(mte.pachner_walk(sig, moves=10, seeds=[1, 2, 3]))
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[2] / "engine"

if not (ENGINE / "src" / "mtengine").is_dir():
    raise ImportError(f"mtengine submodule missing at {ENGINE}; run "
                      "`git submodule update --init engine`")
if str(ENGINE / "src") not in sys.path:
    sys.path.insert(0, str(ENGINE / "src"))

from mtengine import api as mte  # noqa: E402

__all__ = ["mte", "value", "engine_version"]


def value(result: dict):
    """The computed value of an mtengine call (dropping provenance / cache flag)."""
    return result["value"]


def engine_version() -> str:
    """mtengine version plus the submodule commit, for run metadata."""
    try:
        sha = subprocess.check_output(["git", "-C", str(ENGINE), "rev-parse", "--short", "HEAD"],
                                      text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        sha = "unknown"
    return f"{mte.core.__version__}@{sha}"

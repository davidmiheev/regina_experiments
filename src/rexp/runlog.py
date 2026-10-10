"""Reproducible run bookkeeping: one directory per run, metadata + JSONL records.

    with Run("e01_closed_census_invariants", params=vars(args)) as run:
        for label, tri in iter_census("closed-or", max_size=6):
            h, secs = timed(tri.homology)
            run.record(label=label, homology=str(h), secs=secs)

produces ``results/<experiment>/<UTC timestamp>/{meta.json,records.jsonl}``.
"""

from __future__ import annotations

import datetime as _dt
import json
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

import regina

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = REPO_ROOT / "results"


def timed(fn: Callable, *args, **kwargs) -> tuple[Any, float]:
    """Call ``fn`` and return ``(result, wall_seconds)``."""
    t0 = time.perf_counter()
    out = fn(*args, **kwargs)
    return out, time.perf_counter() - t0


def _git_sha() -> str | None:
    try:
        sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT,
                                      stderr=subprocess.DEVNULL, text=True).strip()
        dirty = subprocess.call(["git", "diff", "--quiet"], cwd=REPO_ROOT,
                                stderr=subprocess.DEVNULL) != 0
        return sha + ("-dirty" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return None


class Run:
    def __init__(self, experiment: str, params: dict | None = None,
                 results_dir: Path | None = None):
        stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.dir = (results_dir or RESULTS_DIR) / experiment / stamp
        self.meta = {
            "experiment": experiment,
            "params": params or {},
            "regina": regina.versionString(),
            "python": sys.version.split()[0],
            "host": platform.node(),
            "git": _git_sha(),
            "argv": sys.argv,
            "started": stamp,
        }
        self.n_records = 0
        self._fh = None
        self._t0 = 0.0

    def __enter__(self) -> "Run":
        self.dir.mkdir(parents=True, exist_ok=True)
        self._fh = open(self.dir / "records.jsonl", "w")
        self._t0 = time.perf_counter()
        self._write_meta()
        return self

    def record(self, **fields: Any) -> None:
        self._fh.write(json.dumps(fields, default=str) + "\n")
        self.n_records += 1
        if self.n_records % 500 == 0:
            self._fh.flush()

    def __exit__(self, exc_type, exc, tb) -> None:
        self._fh.close()
        self.meta["records"] = self.n_records
        self.meta["wall_seconds"] = round(time.perf_counter() - self._t0, 3)
        self.meta["status"] = "ok" if exc_type is None else f"error: {exc_type.__name__}: {exc}"
        self._write_meta()
        print(f"[{self.meta['experiment']}] {self.n_records} records -> {self.dir}",
              file=sys.stderr)

    def _write_meta(self) -> None:
        (self.dir / "meta.json").write_text(json.dumps(self.meta, indent=2, default=str) + "\n")

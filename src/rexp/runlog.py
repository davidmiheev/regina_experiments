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


def _engine_version() -> str | None:
    """mtengine version and commit, if the engine submodule is present."""
    try:
        from .engine import engine_version
        return engine_version()
    except ImportError:
        return None


# Parameters that may change between an interrupted run and its resumption.
VOLATILE_PARAMS = {"workers", "resume"}


def _comparable(params: dict) -> dict:
    return {k: v for k, v in params.items() if k not in VOLATILE_PARAMS}


class Run:
    """Log one run. Pass ``resume=<run dir>`` to append to an interrupted run;
    ``run.existing`` then holds the records already written."""

    def __init__(self, experiment: str, params: dict | None = None,
                 results_dir: Path | None = None, resume: Path | None = None):
        stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        session = {
            "regina": regina.versionString(),
            "engine": _engine_version(),
            "python": sys.version.split()[0],
            "host": platform.node(),
            "git": _git_sha(),
            "argv": sys.argv,
            "started": stamp,
        }
        self.existing: list[dict] = []
        if resume is not None:
            self.dir = Path(resume)
            self.meta = json.loads((self.dir / "meta.json").read_text())
            if self.meta["experiment"] != experiment:
                raise ValueError(f"{resume} is a run of {self.meta['experiment']}")
            if params is not None and _comparable(self.meta["params"]) != _comparable(params):
                raise ValueError(f"parameters differ from the run being resumed:\n"
                                 f"  was {self.meta['params']}\n  now {params}")
            self.existing = self._read_existing()
            self.meta.setdefault("resumes", []).append(
                {**session, "records_before": len(self.existing),
                 "previous_status": self.meta.get("status", "interrupted")})
        else:
            self.dir = (results_dir or RESULTS_DIR) / experiment / stamp
            self.meta = {"experiment": experiment, "params": params or {}, **session}
        self.n_records = len(self.existing)
        self._fh = None
        self._t0 = 0.0

    def _read_existing(self) -> list[dict]:
        """Parse records.jsonl, dropping a trailing line cut off by a kill."""
        path = self.dir / "records.jsonl"
        good, records = 0, []
        with open(path, "rb") as fh:
            for line in fh:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    break
                good += len(line)
        with open(path, "r+b") as fh:
            fh.truncate(good)
        return records

    def __enter__(self) -> "Run":
        self.dir.mkdir(parents=True, exist_ok=True)
        # Line-buffered, so a killed run loses at most the record in flight.
        self._fh = open(self.dir / "records.jsonl", "a" if self.existing else "w", buffering=1)
        self._t0 = time.perf_counter()
        self._write_meta()
        return self

    def record(self, **fields: Any) -> None:
        self._fh.write(json.dumps(fields, default=str) + "\n")
        self.n_records += 1

    def __exit__(self, exc_type, exc, tb) -> None:
        self._fh.close()
        self.meta["records"] = self.n_records
        secs = round(time.perf_counter() - self._t0, 3)
        if self.meta.get("resumes"):
            self.meta["resumes"][-1]["wall_seconds"] = secs
        else:
            self.meta["wall_seconds"] = secs
        self.meta["status"] = "ok" if exc_type is None else f"error: {exc_type.__name__}: {exc}"
        self._write_meta()
        print(f"[{self.meta['experiment']}] {self.n_records} records -> {self.dir}",
              file=sys.stderr)

    def _write_meta(self) -> None:
        (self.dir / "meta.json").write_text(json.dumps(self.meta, indent=2, default=str) + "\n")

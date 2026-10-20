#!/usr/bin/env python3
"""E02b - how reliable is greedy simplification on non-minimal triangulations?

simplify() makes random choices (random 4-4 moves, see Regina's docs), so
"simplify() reduced it" in the main E02 run is a single sample. For every
non-minimal triangulation that E02 certified, this script records:
  * local - does the deterministic simplifyToLocalMinimum() reduce it?
  * hits  - in how many of --trials independent simplify() calls does the
            size drop below n?

Usage: retry.py SOURCE_RUN_DIR [--trials K] [--max-n N]
"""

import argparse
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _bootstrap  # noqa: E402,F401

import regina  # noqa: E402
from rexp import Run  # noqa: E402

EXPERIMENT = "e02_tricensus_regeneration_retry"


def trial(job: tuple) -> dict:
    n, sig, status, trials = job
    tri = regina.Triangulation3.fromIsoSig(sig)
    local = regina.Triangulation3(tri)
    local.simplifyToLocalMinimum()
    hits = 0
    for _ in range(trials):
        t = regina.Triangulation3(tri)
        t.simplify()
        hits += t.size() < n
    return {"n": n, "isosig": sig, "status": status,
            "local": local.size() < n, "hits": hits, "trials": trials}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", type=Path, help="an E02 run directory")
    ap.add_argument("--trials", type=int, default=20)
    ap.add_argument("--max-n", type=int, default=None)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    args = ap.parse_args()

    jobs = []
    for line in open(args.source / "records.jsonl"):
        r = json.loads(line)
        if r["kind"] == "generated" and r["status"] not in ("census", "unresolved") \
                and (args.max_n is None or r["n"] <= args.max_n):
            jobs.append((r["n"], r["isosig"], r["status"], args.trials))
    params = {"source": str(args.source), "trials": args.trials, "max_n": args.max_n,
              "workers": args.workers}
    print(f"{len(jobs)} non-minimal triangulations x {args.trials} trials", file=sys.stderr)
    with Run(EXPERIMENT, params=params) as run, \
            ProcessPoolExecutor(max_workers=args.workers) as pool:
        for rec in pool.map(trial, jobs, chunksize=32):
            run.record(**rec)


if __name__ == "__main__":
    main()

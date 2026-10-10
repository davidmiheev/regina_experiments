#!/usr/bin/env python3
"""Summarise an E01 run: how many census manifolds does each invariant separate?

Usage: analyze.py [RUN_DIR]   (defaults to the latest run)
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

RESULTS = Path(__file__).resolve().parents[2] / "results" / "e01_closed_census_invariants"


def main() -> None:
    run_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else max(RESULTS.iterdir())
    recs = [json.loads(line) for line in open(run_dir / "records.jsonl")]

    # One representative per manifold; sanity-check that every triangulation of
    # the same manifold gives the same invariants (they are topological).
    by_mfd = {}
    inconsistent = []
    for r in recs:
        rep = by_mfd.setdefault(r["manifold"], r)
        if rep["h1"] != r["h1"] or any(abs(rep["tv"][t] - r["tv"][t]) > 1e-6 for t in r["tv"]):
            inconsistent.append(r["label"])
    mfds = list(by_mfd.values())
    tv_levels = sorted(mfds[0]["tv"], key=int) if mfds else []

    keys = {
        "H1": lambda r: r["h1"],
        **{f"TV_{t}": (lambda t: lambda r: r["tv"][t])(t) for t in tv_levels},
        "H1 + all TV": lambda r: (r["h1"], tuple(r["tv"][t] for t in tv_levels)),
    }

    print(f"run: {run_dir}")
    print(f"{len(recs)} triangulations, {len(mfds)} distinct manifolds")
    print(f"sanity: triangulations disagreeing with their manifold's invariants: "
          f"{len(inconsistent)} {inconsistent[:5]}\n")
    print(f"{'invariant':<14}{'classes':>9}{'separated':>11}{'largest clash':>15}")
    for name, key in keys.items():
        classes = defaultdict(list)
        for r in mfds:
            classes[key(r)].append(r["manifold"])
        singletons = sum(1 for v in classes.values() if len(v) == 1)
        worst = max(classes.values(), key=len)
        print(f"{name:<14}{len(classes):>9}{singletons:>11}{len(worst):>15}")

    full = defaultdict(list)
    for r in mfds:
        full[keys["H1 + all TV"](r)].append(r["manifold"])
    clashes = [v for v in full.values() if len(v) > 1]
    print(f"\nmanifold groups NOT separated by H1 + TV_{{{','.join(tv_levels)}}}: {len(clashes)}")
    for group in sorted(clashes, key=len, reverse=True)[:15]:
        print("  ", " | ".join(group))

    print("\nmean seconds per invariant:")
    totals = defaultdict(float)
    for r in recs:
        for k, s in r["secs"].items():
            totals[k] += s
    for k, s in totals.items():
        print(f"  {k:<6} {s / len(recs) * 1000:9.2f} ms")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Summarise an E03 run.

Usage: analyze.py [RUN_DIR] [--export DIR]
Writes summary.json, report.txt and stuck.tsv (scrambled triangulations on which a greedy
simplify() call got stuck) into RUN_DIR, and copies them to DIR with --export.
"""

import argparse
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path

RESULTS = Path(__file__).resolve().parents[2] / "results" / "e03_scramble_simplify"
CLASSES = ["S3", "lens", "Seifert", "graph", "torus bundle", "hyperbolic"]


class Report:
    def __init__(self):
        self.lines = []

    def __call__(self, *parts):
        line = " ".join(str(p) for p in parts)
        print(line)
        self.lines.append(line)


def height_needed(r) -> str:
    """0 if some greedy call reached the target, else the exhaustive height that did."""
    target = r.get("n0", r.get("target"))
    if r["greedy_best"] <= target:
        return "0"
    for s in r["exhaustive"]:
        if s["size"] <= target:
            return str(s["height"])
    return "unresolved"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", nargs="?", type=Path)
    ap.add_argument("--export", type=Path)
    args = ap.parse_args()
    run_dir = args.run_dir or max(p for p in RESULTS.iterdir() if p.is_dir())
    meta = json.loads((run_dir / "meta.json").read_text())
    recs = [json.loads(line) for line in open(run_dir / "records.jsonl")]
    out = Report()
    out(f"run: {run_dir}  (Regina {meta['regina']}, engine {meta.get('engine')}, "
        f"git {meta['git']}, {meta.get('wall_seconds')} s)")
    summary = {"run": {"dir": str(run_dir), **{k: meta.get(k) for k in
                                               ("regina", "engine", "git", "params",
                                                "wall_seconds")}}}

    # ---------------------------------------------------------------- part A
    A = [r for r in recs if r["part"] == "A"]
    M = [r for r in recs if r["part"] == "M"]
    trials = len(A[0]["greedy_sizes"])
    out(f"\n=== A: {len(A)} scrambles of {len(M)} manifolds "
        f"({dict(Counter(m['class'] for m in M))}), {trials} greedy calls each")
    reached = [r for r in A if r["final_size"] == r["n0"]]
    wrong = [r for r in reached if not r["same_manifold"]]
    unresolved = [r for r in A if r["final_size"] > r["n0"]]
    out(f"sanity: returned to the census size {len(reached)}/{len(A)}; of those, census "
        f"lookup names a different manifold: {len(wrong)}; unresolved after exhaustive "
        f"height {meta['params']['max_height']}: {len(unresolved)}")
    summary["A"] = {"scrambles": len(A), "manifolds": len(M), "trials": trials,
                    "reached": len(reached), "wrong_manifold": len(wrong),
                    "unresolved": len(unresolved)}

    def fail_rate(rows):
        calls = [s for r in rows for s in r["greedy_sizes"]]
        bad = sum(s > r["n0"] for r in rows for s in r["greedy_sizes"])
        return bad / len(calls) if calls else 0.0

    def best_fail(rows):
        return sum(r["greedy_best"] > r["n0"] for r in rows) / len(rows) if rows else 0.0

    ks = sorted({r["moves"] for r in A})
    mixes = sorted({r["mix44"] for r in A})
    out(f"\nP(one simplify() call stays above n0), by moves k (rows) and 4-4 moves per step:")
    out(f"{'k':>5}" + "".join(f"{'mix44=' + str(m):>12}" for m in mixes) + f"{'all':>10}")
    summary["A"]["fail_by_k_mix"] = {}
    for k in ks:
        row = [fail_rate([r for r in A if r["moves"] == k and r["mix44"] == m]) for m in mixes]
        summary["A"]["fail_by_k_mix"][str(k)] = dict(zip(map(str, mixes), row))
        out(f"{k:>5}" + "".join(f"{x:>12.4f}" for x in row) +
            f"{fail_rate([r for r in A if r['moves'] == k]):>10.4f}")
    out(f"overall: one call fails {fail_rate(A):.4f}; best of {trials} fails {best_fail(A):.4f}")
    summary["A"]["fail_one_call"] = fail_rate(A)
    summary["A"]["fail_best_of_trials"] = best_fail(A)

    out("\nby geometric class (one call / best of all calls):")
    summary["A"]["by_class"] = {}
    for c in CLASSES:
        rows = [r for r in A if r["class"] == c]
        if rows:
            summary["A"]["by_class"][c] = [fail_rate(rows), best_fail(rows)]
            out(f"  {c:<13}{len(rows):>6}{fail_rate(rows):>10.4f}{best_fail(rows):>10.4f}")
    out("by census size n0 (one call):")
    summary["A"]["by_n0"] = {}
    for n0 in sorted({r["n0"] for r in A}):
        rows = [r for r in A if r["n0"] == n0]
        summary["A"]["by_n0"][str(n0)] = [len(rows), fail_rate(rows)]
        out(f"  n0={n0:>2}: {len(rows):>5} scrambles, one call fails {fail_rate(rows):.4f}")

    heights = Counter(height_needed(r) for r in A)
    summary["A"]["height_needed"] = dict(heights)
    excess = Counter(s - r["n0"] for r in A for s in r["greedy_sizes"] if s > r["n0"])
    summary["A"]["stuck_excess"] = {str(k): v for k, v in sorted(excess.items())}
    out(f"height needed after {trials} greedy calls: {dict(heights)}")
    out(f"where single calls got stuck, tetrahedra above n0: {dict(sorted(excess.items()))}")

    stuck_by_m = Counter(r["manifold"] for r in A if any(s > r["n0"] for s in r["greedy_sizes"]))
    summary["A"]["stuck_manifolds"] = stuck_by_m.most_common()
    out(f"manifolds on which some call got stuck: {len(stuck_by_m)} of {len(M)}; most often: "
        f"{stuck_by_m.most_common(6)}")

    greedy_ms = defaultdict(list)
    for r in A:
        greedy_ms[r["moves"]].append(1000 * r["greedy_secs"] / trials)
    summary["A"]["greedy_ms_by_k"] = {str(k): sum(v) / len(v) for k, v in sorted(greedy_ms.items())}
    out("mean ms per simplify() call by k: " + ", ".join(
        f"{k}: {v:.2f}" for k, v in summary["A"]["greedy_ms_by_k"].items()))

    # ---------------------------------------------------------------- part B
    B = [r for r in recs if r["part"] == "B"]
    if B:
        tab = Counter((r["e02_height"], height_needed(r)) for r in B)
        out(f"\n=== B: E02's {len(B)} hard non-minimal triangulations, {trials} greedy calls + "
            f"exhaustive (height needed now vs E02's single-call classification):")
        for k, v in sorted(tab.items()):
            out(f"  E02 height {k[0]} -> now {k[1]}: {v}")
        summary["B"] = {f"{a}->{b}": v for (a, b), v in sorted(tab.items())}
        summary["B_consistent"] = all(int(b) <= a for (a, b), _ in tab.items() if b != "unresolved")

    # ---------------------------------------------------------------- part C
    C = [r for r in recs if r["part"] == "C"]
    if C:
        out(f"\n=== C: 3-sphere recognition on {len(C)} scrambled 3-spheres: recognised "
            f"{sum(r['sphere'] for r in C)}/{len(C)}")
        by = defaultdict(list)
        for r in C:
            by[r["size"]].append(r["seconds"])
        summary["C"] = {"recognised": sum(r["sphere"] for r in C), "total": len(C),
                        "seconds_by_size": {str(s): [len(v), sum(v) / len(v), max(v)]
                                            for s, v in sorted(by.items())}}
        for s, (n, mean, mx) in summary["C"]["seconds_by_size"].items():
            out(f"  {s:>4} tetrahedra: {n} triangulations, mean {mean:.3f} s, max {mx:.3f} s")

    with open(run_dir / "stuck.tsv", "w") as fh:
        fh.write("manifold\tclass\tn0\tmoves\tmix44\tseed\tgreedy_sizes\theight_needed\t"
                 "scrambled_isosig\n")
        for r in A:
            if any(s > r["n0"] for s in r["greedy_sizes"]):
                fh.write(f"{r['manifold']}\t{r['class']}\t{r['n0']}\t{r['moves']}\t{r['mix44']}\t"
                         f"{r['seed']}\t{','.join(map(str, r['greedy_sizes']))}\t"
                         f"{height_needed(r)}\t{r['scrambled_isosig']}\n")
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (run_dir / "report.txt").write_text("\n".join(out.lines) + "\n")
    if args.export:
        args.export.mkdir(parents=True, exist_ok=True)
        for f in ("summary.json", "report.txt", "stuck.tsv"):
            shutil.copy(run_dir / f, args.export / f)
        print(f"\nexported to {args.export}")


if __name__ == "__main__":
    main()

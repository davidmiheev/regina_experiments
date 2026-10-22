#!/usr/bin/env python3
"""Summarise an E02 run: did tricensus reproduce the shipped census?

Usage: analyze.py [RUN_DIR] [--export DIR]

Writes summary.json, report.txt and hard_nonminimal.tsv (non-minimal
triangulations that greedy simplify() could not reduce) into RUN_DIR, and
copies them to DIR when --export is set.
"""

import argparse
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path

RESULTS = Path(__file__).resolve().parents[2] / "results" / "e02_tricensus_regeneration"
RETRY = RESULTS.with_name("e02_tricensus_regeneration_retry")


class Report:
    def __init__(self):
        self.lines = []

    def __call__(self, *parts):
        line = " ".join(str(p) for p in parts)
        print(line)
        self.lines.append(line)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", nargs="?", type=Path)
    ap.add_argument("--export", type=Path)
    ap.add_argument("--retry", type=Path,
                    help="retry.py run to include (default: latest one made from RUN_DIR)")
    args = ap.parse_args()
    run_dir = args.run_dir or max(p for p in RESULTS.iterdir() if p.is_dir())
    meta = json.loads((run_dir / "meta.json").read_text())
    recs = [json.loads(line) for line in open(run_dir / "records.jsonl")]
    out = Report()

    gen = {r["n"]: r for r in recs if r["kind"] == "generation"}
    by_n = defaultdict(list)
    for r in recs:
        if r["kind"] == "generated":
            by_n[r["n"]].append(r)
    missing = [r for r in recs if r["kind"] == "missing"]
    ns = sorted(gen)
    # Only sizes whose classification finished (a run can stop mid-size).
    ns = [n for n in ns if len(by_n[n]) == gen[n]["triangulations"]]

    out(f"run: {run_dir}  (Regina {meta['regina']}, git {meta['git']})")
    out(f"sizes analysed: n = {ns[0]}..{ns[-1]}")

    statuses = ["census", "simplify", "exhaustive:1", "exhaustive:2", "exhaustive:3",
                "S3", "nonprime", "unresolved"]
    hdr = (f"{'n':>3}{'pairings':>10}{'generated':>11}{'gen s':>9}{'census':>8}"
           + "".join(f"{s.replace('exhaustive:', 'exh'):>11}" for s in statuses[1:])
           + f"{'missing':>9}")
    out("\n" + hdr)
    rows = {}
    for n in ns:
        c = Counter(r["status"] for r in by_n[n])
        miss = sum(1 for r in missing if r["n"] == n)
        census_count = c["census"] + miss
        rows[n] = {"pairings": gen[n]["pairings"], "generated": len(by_n[n]),
                   "gen_secs": gen[n]["secs"], "census_size": census_count,
                   "missing": miss, **{s: c[s] for s in statuses}}
        out(f"{n:>3}{gen[n]['pairings']:>10}{len(by_n[n]):>11}{gen[n]['secs']:>9.1f}"
            f"{c['census']:>8}" + "".join(f"{c[s]:>11}" for s in statuses[1:]) + f"{miss:>9}")

    total = {k: sum(row[k] for row in rows.values())
             for k in ["generated", "census_size", "missing", *statuses]}
    exact = total["missing"] == 0 and total["unresolved"] == 0
    out(f"\nverdict: census reproduced exactly for n <= {ns[-1]}: {exact}  "
        f"({total['census']} of {total['census_size']} census triangulations generated, "
        f"{total['missing']} missing, {total['unresolved']} unresolved)")
    nonmin = total["generated"] - total["census"]
    hard = [r for n in ns for r in by_n[n] if r["status"].startswith("exhaustive")]
    out(f"non-minimal triangulations certified: {nonmin}; greedy simplify() was enough "
        f"for {total['simplify']} ({100 * total['simplify'] / max(nonmin, 1):.1f}%), "
        f"exhaustive search needed for {len(hard)}"
        f" (heights: {dict(Counter(r['status'] for r in hard))})")

    # Growth of the search and of its output.
    out("\ngrowth factor from n-1 to n:")
    growth = {}
    for a, b in zip(ns, ns[1:]):
        if a >= 3:
            growth[b] = {"gen_secs": gen[b]["secs"] / max(gen[a]["secs"], 1e-9),
                         "generated": rows[b]["generated"] / rows[a]["generated"],
                         "census": rows[b]["census_size"] / rows[a]["census_size"]}
            g = growth[b]
            out(f"  n={b}: time x{g['gen_secs']:.1f}, generated x{g['generated']:.1f}, "
                f"census x{g['census']:.1f}")

    # Which manifolds have the most non-minimal triangulations at their size?
    named = Counter(r["reduced_name"].split(" : #")[0] for n in ns for r in by_n[n]
                    if r["status"] != "census" and r.get("reduced_name"))
    unnamed = sum(1 for n in ns for r in by_n[n]
                  if r["status"] != "census" and not r.get("reduced_name"))
    out(f"\nnon-minimal triangulations by manifold (after simplifying; "
        f"{unnamed} did not reach a census triangulation):")
    for m, k in named.most_common(10):
        out(f"  {k:>6}  {m}")

    # Costs.
    out("\nclassification time per triangulation (mean ms):")
    secs = {}
    for n in ns:
        keys = sorted({k for r in by_n[n] for k in r["secs"]})
        secs[n] = {k: 1000 * sum(r["secs"].get(k, 0) for r in by_n[n]) / len(by_n[n])
                   for k in keys}
        out(f"  n={n}: " + ", ".join(f"{k} {v:.2f}" for k, v in secs[n].items()))

    # --- How reliable is a single simplify() call? (retry.py)
    retry_dir = args.retry
    if retry_dir is None and RETRY.exists():
        cands = [p for p in RETRY.iterdir() if p.is_dir() and json.loads(
            (p / "meta.json").read_text())["params"]["source"] in (str(run_dir), str(
                run_dir.relative_to(RESULTS.parents[1])) if run_dir.is_absolute() else "")]
        retry_dir = max(cands) if cands else None
    retry_rows, p_hard = {}, {}
    if retry_dir and not (retry_dir / "records.jsonl").exists():
        print(f"(no retry data at {retry_dir}; skipping the simplify() reliability section)")
        retry_dir = None
    if retry_dir:
        rr = [json.loads(line) for line in open(retry_dir / "records.jsonl")]
        trials = rr[0]["trials"]
        out(f"\nsimplify() reliability ({retry_dir.name}: {len(rr)} non-minimal "
            f"triangulations x {trials} independent calls)")
        out(f"{'n':>3}{'non-min':>9}{'local min':>11}{'always':>9}{'sometimes':>11}"
            f"{'never':>7}{'P(one call fails)':>19}")
        for n in ns:
            xs = [r for r in rr if r["n"] == n]
            if not xs:
                continue
            row = {"nonminimal": len(xs), "local": sum(r["local"] for r in xs),
                   "always": sum(r["hits"] == r["trials"] for r in xs),
                   "never": sum(r["hits"] == 0 for r in xs),
                   "p_fail": sum(1 - r["hits"] / r["trials"] for r in xs) / len(xs)}
            row["sometimes"] = row["nonminimal"] - row["always"] - row["never"]
            retry_rows[n] = row
            out(f"{n:>3}{row['nonminimal']:>9}{row['local']:>11}{row['always']:>9}"
                f"{row['sometimes']:>11}{row['never']:>7}{row['p_fail']:>19.4f}")
        p_hard = {r["isosig"]: r["hits"] / r["trials"] for r in rr}

    with open(run_dir / "hard_nonminimal.tsv", "w") as fh:
        fh.write("n\theight\tisosig\treduced_size\treduced_name\tsimplify_success_rate\n")
        for r in hard:
            p = p_hard.get(r["isosig"])
            fh.write(f"{r['n']}\t{r['status'].split(':')[1]}\t{r['isosig']}\t"
                     f"{r.get('reduced_size', '')}\t{r.get('reduced_name') or ''}\t"
                     f"{'' if p is None else f'{p:.2f}'}\n")
    summary = {"sizes": ns, "rows": {str(n): rows[n] for n in ns}, "totals": total,
               "reproduced_exactly": exact, "growth": {str(k): v for k, v in growth.items()},
               "top_nonminimal_manifolds": named.most_common(25),
               "nonminimal_unnamed": unnamed, "classify_ms": {str(k): v for k, v in secs.items()},
               "missing": missing,
               "retry": {"dir": str(retry_dir) if retry_dir else None,
                         "rows": {str(k): v for k, v in retry_rows.items()}},
               "run": {"dir": str(run_dir), **{k: meta.get(k) for k in
                       ("regina", "git", "params", "wall_seconds", "started", "resumes")}}}
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (run_dir / "report.txt").write_text("\n".join(out.lines) + "\n")
    if args.export:
        args.export.mkdir(parents=True, exist_ok=True)
        for f in ("summary.json", "report.txt", "hard_nonminimal.tsv"):
            shutil.copy(run_dir / f, args.export / f)
        print(f"\nexported to {args.export}")


if __name__ == "__main__":
    main()

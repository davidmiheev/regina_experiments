#!/usr/bin/env python3
"""Summarise an E06 run.

Usage: analyze.py [RUN_DIR] [--export DIR]
Writes summary.json, report.txt and nongeometric.tsv into RUN_DIR (and DIR).
"""

import argparse
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path

RESULTS = Path(__file__).resolve().parents[2] / "results" / "e06_hyperbolic_angle_structures"
V_TET = 1.0149416064096536  # volume of the regular ideal tetrahedron
TOL = 1e-8


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
    args = ap.parse_args()
    run_dir = args.run_dir or max(p for p in RESULTS.iterdir() if p.is_dir())
    meta = json.loads((run_dir / "meta.json").read_text())
    recs = [json.loads(line) for line in open(run_dir / "records.jsonl")]
    out = Report()
    summary = {"run": {"dir": str(run_dir), **{k: meta.get(k) for k in
                                               ("regina", "git", "params", "wall_seconds")}}}
    out(f"run: {run_dir}  (Regina {meta['regina']}, git {meta['git']}, "
        f"{meta.get('wall_seconds')} s)")

    cusped = [r for r in recs if r["kind"] == "cusped"]
    nongeo_rows = []
    for census in ("cusped-hyp-or", "cusped-hyp-nor"):
        xs = [r for r in cusped if r["census"] == census]
        s = summary[census] = {}
        by_m = defaultdict(list)
        for r in xs:
            by_m[r["manifold"]].append(r)
        out(f"\n=== {census}: {len(xs)} triangulations of {len(by_m)} manifolds, "
            f"n = {min(r['n'] for r in xs)}..{max(r['n'] for r in xs)}, "
            f"cusps {dict(sorted(Counter(r['cusps'] for r in xs).items()))}")

        # Cross-tabulation and the two sanity checks.
        tab = Counter((r["strict"], r["solution"]) for r in xs)
        s["crosstab"] = {f"{'strict' if k[0] else 'no strict'} / {k[1]}": v
                         for k, v in sorted(tab.items(), key=str)}
        out("strict angle structure x SnapPea solution:")
        for k, v in s["crosstab"].items():
            out(f"  {k:<32}{v:>7}")
        s["geometric_without_strict"] = tab[(False, "Geometric")]
        s["lp_disagrees_with_enumeration"] = sum(r["strict"] != r["strict_lp"] for r in xs)
        out(f"sanity: geometric but no strict angle structure: {s['geometric_without_strict']} "
            f"(must be 0); LP vs enumeration disagreements: "
            f"{s['lp_disagrees_with_enumeration']}")

        # By size.
        out(f"{'n':>3}{'tris':>7}{'geometric':>11}{'strict,nongeo':>15}{'no strict':>11}"
            f"{'taut':>7}{'mean vertices':>15}")
        s["by_n"] = {}
        for n in sorted({r["n"] for r in xs}):
            ys = [r for r in xs if r["n"] == n]
            row = {"tris": len(ys),
                   "geometric": sum(r["solution"] == "Geometric" for r in ys),
                   "strict_nongeometric": sum(r["strict"] and r["solution"] != "Geometric"
                                              for r in ys),
                   "no_strict": sum(not r["strict"] for r in ys),
                   "taut": sum(r["taut"] for r in ys),
                   "mean_angle_vertices": sum(r["angle_vertices"] for r in ys) / len(ys)}
            s["by_n"][str(n)] = row
            out(f"{n:>3}{row['tris']:>7}{row['geometric']:>11}{row['strict_nongeometric']:>15}"
                f"{row['no_strict']:>11}{row['taut']:>7}{row['mean_angle_vertices']:>15.1f}")

        # Per manifold: a geometric triangulation exists?  Volumes agree?
        no_geo = [m for m, v in by_m.items() if not any(r["solution"] == "Geometric" for r in v)]
        first_not_geo = [m for m, v in by_m.items()
                         if not any(r["solution"] == "Geometric" and r["label"].endswith("#1")
                                    for r in v)]
        spread = {m: max(r["volume"] for r in v) - min(r["volume"] for r in v)
                  for m, v in by_m.items() if len(v) > 1}
        s["manifolds_without_geometric_triangulation"] = no_geo
        s["manifolds_whose_first_triangulation_is_not_geometric"] = len(first_not_geo)
        s["max_volume_spread_within_manifold"] = max(spread.values()) if spread else 0
        out(f"manifolds with no geometric census triangulation: {len(no_geo)}; "
            f"whose #1 triangulation is not geometric: {len(first_not_geo)}")
        out(f"volume spread across triangulations of one manifold (all solution types): "
            f"max {s['max_volume_spread_within_manifold']:.2e}")

        # Census order: within a prefix, names are sorted by volume.
        vol = {m: next(r["volume"] for r in v if r["solution"] == "Geometric")
               for m, v in by_m.items() if m not in no_geo}
        prefix = defaultdict(list)
        for m in vol:
            prefix[by_m[m][0]["prefix"]].append((by_m[m][0]["index"], vol[m], m))
        inversions = []
        for p, items in prefix.items():
            items.sort()
            inversions += [(a[2], b[2], a[1] - b[1]) for a, b in zip(items, items[1:])
                           if a[1] > b[1] + 1e-9]
        s["prefixes"] = {p: len(v) for p, v in sorted(prefix.items())}
        s["volume_order_inversions"] = inversions
        out(f"census order (prefixes {s['prefixes']}): volume decreases between consecutive "
            f"names {len(inversions)} times {inversions[:5]}")

        # The bound vol <= n * v_tet, and who attains it.
        ratio = {r["label"]: r["volume"] / (r["n"] * V_TET) for r in xs
                 if r["solution"] == "Geometric"}
        attain = sorted(k for k, v in ratio.items() if v > 1 - 1e-9)
        s["max_volume_ratio"] = max(ratio.values())
        s["attains_bound"] = attain
        out(f"volume / (n * v_tet): max {s['max_volume_ratio']:.12f}; attained by {attain}")
        s["volume_points"] = [[r["n"], r["volume"]] for r in xs
                              if r["solution"] == "Geometric" and r["label"].endswith("#1")]

        for r in xs:
            if r["solution"] != "Geometric":
                others = [o["label"] for o in by_m[r["manifold"]] if o["solution"] == "Geometric"]
                nongeo_rows.append((census, r["label"], r["n"], r["strict"], r["taut"],
                                    r["solution"], r["volume"], r.get("min_imag_shape"),
                                    others[0] if others else ""))
        s["secs_mean_ms"] = {k: 1000 * sum(r["secs"][k] for r in xs) / len(xs)
                             for k in xs[0]["secs"]}

    # --- Closed census.
    closed = [r for r in recs if r["kind"] == "closed"]
    framing = {r["label"]: r for r in recs if r["kind"] == "framing"}
    c = summary["closed-hyp"] = {}
    out(f"\n=== closed-hyp: {len(closed)} triangulations "
        f"(n = {min(r['n'] for r in closed)}..{max(r['n'] for r in closed)})")
    sol = Counter(r["closed"]["solution"] for r in closed)
    right = Counter(r["closed"]["solution"] for r in closed
                    if abs(r["closed"]["volume"] - r["label_volume"]) < TOL)
    c["closed_triangulation"] = {k: {"count": v, "volume_matches_label": right[k]}
                                 for k, v in sol.items()}
    out("SnapPea on the closed triangulation itself, first construction "
        "(solution: count, volume = label):")
    for k, v in c["closed_triangulation"].items():
        out(f"  {k:<14}{v['count']:>6}{v['volume_matches_label']:>8}")

    # The closed triangulation is converted by SnapPea into a filling of a cusped
    # manifold; that conversion is randomised, so each was sampled k times.
    k = closed[0]["closed_trials"]["n"]
    hist = Counter(r["closed_trials"]["volume_correct"] for r in closed)
    nondegenerate_iff_correct = all(
        r["closed_trials"]["volume_correct"] == sum(
            v for s_, v in r["closed_trials"]["solutions"].items() if s_ != "Degenerate")
        for r in closed)
    c["trials"] = {"k": k, "histogram": {str(i): hist[i] for i in range(k + 1)},
                   "p_correct_per_attempt": sum(r["closed_trials"]["volume_correct"]
                                                for r in closed) / (k * len(closed)),
                   "always": hist[k], "never": hist[0],
                   "nondegenerate_iff_volume_correct": nondegenerate_iff_correct}
    by_size = defaultdict(list)
    for r in closed:
        by_size[r["n"]].append(r["closed_trials"]["volume_correct"] / k)
    c["trials"]["p_by_n"] = {str(n): [len(v), sum(v) / len(v)] for n, v in sorted(by_size.items())}
    out(f"over {k} independent constructions per triangulation: P(volume correct) = "
        f"{c['trials']['p_correct_per_attempt']:.3f}; correct every time {hist[k]}, never "
        f"{hist[0]}, sometimes {len(closed) - hist[k] - hist[0]}; non-degenerate <=> correct "
        f"volume: {nondegenerate_iff_correct}")
    out("  P(correct) by n: " + ", ".join(f"{n}: {v[1]:.2f} ({v[0]})"
                                          for n, v in c["trials"]["p_by_n"].items()))

    filled = [r for r in closed if r["filled"]]
    c["no_base_in_cusped_census"] = sorted({r["filling"] for r in closed if not r["filled"]})
    groups = defaultdict(list)
    for r in filled:
        groups[r["filling"].split("(")[0]].append(r)

    def match(f, v):
        return abs(f["volume"] - v) < TOL

    conv = {}
    for base, rs in groups.items():
        same = all(match(r["filled"], r["label_volume"]) for r in rs)
        mirror = all(match(r["filled_mirror"], r["label_volume"]) for r in rs)
        if same and mirror:
            conv[base] = "either"
        elif same:
            conv[base] = "as labelled"
        elif mirror:
            conv[base] = "mirror (-p, q)"
        elif base in framing and framing[base]["matrices"]:
            conv[base] = "other basis change"
        else:
            conv[base] = "unexplained"
    c["base_conventions"] = dict(Counter(conv.values()))
    c["other_basis_change"] = {b: framing[b]["matrices"] for b in conv
                               if conv[b] == "other basis change"}
    c["fillings_reproduced"] = sum(1 for r in filled if conv[r["filling"].split("(")[0]]
                                   != "unexplained")
    out(f"Dehn fillings re-done from the cusped census: {len(filled)} "
        f"({len(c['no_base_in_cusped_census'])} labels name a cusped manifold missing from "
        f"Regina's cusped census: {c['no_base_in_cusped_census'][:6]} ...)")
    out(f"  {len(groups)} base manifolds; labelled volumes reproduced with slopes "
        f"{c['base_conventions']}")
    for b, ms in c["other_basis_change"].items():
        out(f"  {b}: {len(groups[b])} filling(s), basis changes (a,b,c,d) that fit: {ms[:4]}")
    out(f"  fillings whose labelled volume is reproduced: {c['fillings_reproduced']} of "
        f"{len(filled)}")
    path = Counter(r["filled"]["solution"] for r in filled)
    c["fill_solution_types"] = dict(path)

    with open(run_dir / "nongeometric.tsv", "w") as fh:
        fh.write("census\tlabel\tn\tstrict\ttaut\tsolution\tvolume\tmin_imag_shape\t"
                 "geometric_triangulation_of_same_manifold\n")
        for row in nongeo_rows:
            fh.write("\t".join("" if x is None else str(x) for x in row) + "\n")
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (run_dir / "report.txt").write_text("\n".join(out.lines) + "\n")
    if args.export:
        args.export.mkdir(parents=True, exist_ok=True)
        for f in ("summary.json", "report.txt", "nongeometric.tsv"):
            shutil.copy(run_dir / f, args.export / f)
        print(f"\nexported to {args.export}")


if __name__ == "__main__":
    main()

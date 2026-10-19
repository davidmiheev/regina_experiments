#!/usr/bin/env python3
"""Summarise an E01 run: how many census manifolds does each invariant separate?

Usage: analyze.py [RUN_DIR] [--export DIR]

RUN_DIR defaults to the latest run. Writes summary.json and survivors.tsv into
RUN_DIR, and copies both (plus the printed report) to DIR when --export is set.
"""

import argparse
import json
import math
import re
import shutil
from collections import defaultdict
from pathlib import Path

RESULTS = Path(__file__).resolve().parents[2] / "results" / "e01_closed_census_invariants"
LENS = re.compile(r"^L\((\d+),(\d+)\)$")


class Report:
    def __init__(self):
        self.lines = []

    def __call__(self, *parts):
        line = " ".join(str(p) for p in parts)
        print(line)
        self.lines.append(line)


def lens_relation(a: str, b: str) -> str | None:
    """For lens spaces L(p,q), L(p,q') say whether they are homeomorphic
    (q' = ±q^{±1} mod p), homotopy equivalent (qq' = ±n² mod p), or neither."""
    ma, mb = LENS.match(a), LENS.match(b)
    if not (ma and mb) or ma[1] != mb[1]:
        return None
    p, q, q2 = int(ma[1]), int(ma[2]), int(mb[2])
    if q2 % p in {q % p, -q % p, pow(q, -1, p), -pow(q, -1, p) % p}:
        return "homeomorphic"
    squares = {n * n % p for n in range(p)}
    if (q * q2) % p in squares or (-q * q2) % p in squares:
        return "homotopy-equivalent"
    return "not homotopy-equivalent"


def partition(mfds, key):
    classes = defaultdict(list)
    for r in mfds:
        classes[key(r)].append(r["manifold"])
    return classes


def stats(mfds, key):
    classes = partition(mfds, key)
    return {"classes": len(classes),
            "separated": sum(1 for v in classes.values() if len(v) == 1),
            "largest": max(len(v) for v in classes.values())}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", nargs="?", type=Path)
    ap.add_argument("--export", type=Path, help="copy summary files to this directory")
    args = ap.parse_args()
    run_dir = args.run_dir or max(p for p in RESULTS.iterdir() if p.is_dir())
    meta = json.loads((run_dir / "meta.json").read_text())
    recs = [json.loads(line) for line in open(run_dir / "records.jsonl")]
    out = Report()

    reps = {r["manifold"]: r for r in recs if r["rep"]}
    mfds = list(reps.values())
    levels = sorted(set.intersection(*(set(map(int, r["tv"])) for r in mfds)))
    odd_levels = [r for r in levels if r % 2]

    out(f"run: {run_dir}  (Regina {meta['regina']}, git {meta['git']}, "
        f"{meta.get('wall_seconds', '?')} s)")
    out(f"{len(recs)} triangulations, {len(mfds)} distinct manifolds, "
        f"sizes {min(r['size'] for r in recs)}..{max(r['size'] for r in recs)}, "
        f"TV levels r = {levels[0]}..{levels[-1]}")

    # --- Sanity 1: invariants are topological, so every triangulation of a
    # manifold must agree with its representative.
    bad = [r["label"] for r in recs if not r["rep"] and (
        r["h1"] != reps[r["manifold"]]["h1"]
        or any(v != reps[r["manifold"]]["tv"][k] for k, v in r["tv"].items()))]
    checked = sum(1 for r in recs if not r["rep"])
    out(f"\nsanity: {checked} non-representative triangulations re-checked "
        f"(H1, exact TV_r for r <= {meta['params'].get('check_r')}); disagreements: "
        f"{len(bad)} {bad[:5]}")

    # --- Sanity 2: census names of lens spaces must be pairwise non-homeomorphic.
    lens = [m for m in reps if LENS.match(m)]
    dup = [(a, b) for i, a in enumerate(lens) for b in lens[i + 1:]
           if lens_relation(a, b) == "homeomorphic"]
    out(f"sanity: {len(lens)} lens spaces in census; homeomorphic duplicate names: {dup}")

    # --- Parity: for odd r, is the r-th-root (even) TV just a relabelling of the
    # 2r-th-root (odd) TV?  Compare the multisets of values over all roots.
    parity_mismatch = defaultdict(list)
    for r in mfds:
        for lv in odd_levels:
            vals = r["tv_roots"][str(lv)]
            odd = sorted(v for w, v in vals.items() if int(w) % 2)
            even = sorted(v for w, v in vals.items() if int(w) % 2 == 0)
            if any(not math.isclose(a, b, abs_tol=1e-9) for a, b in zip(odd, even)):
                parity_mismatch[lv].append(r["manifold"])
    out("parity: manifolds whose even-root TV_r values differ (as a multiset) from the "
        "odd-root ones: " + ", ".join(f"r={lv}: {len(parity_mismatch[lv])}" for lv in odd_levels))

    # --- Separation tables.
    def root1(lv):
        return lambda r: round(r["tv_roots"][str(lv)]["1"], 9)

    def allroots(lv):
        return lambda r: r["tv"][str(lv)]["odd"]

    def both(lv):
        return lambda r: (r["tv"][str(lv)]["odd"], r["tv"][str(lv)].get("even"))

    def combo(feature, upto, with_h1=True):
        lvs = [lv for lv in levels if lv <= upto]
        return lambda r: ((r["h1"],) if with_h1 else ()) + tuple(feature(lv)(r) for lv in lvs)

    # TV_r at root w means q0 = exp(i pi w / r), w coprime to r (as in
    # turaevViroApprox). "all odd w" = the exact value for parity=True, i.e. one
    # Galois orbit; "all w" adds parity=False (even w), which only exists for odd r.
    hdr = f"{'invariant':<34}{'classes':>9}{'separated':>11}{'largest':>9}"
    summary = {"triangulations": len(recs), "manifolds": len(mfds), "levels": levels,
               "consistency_failures": bad, "lens_duplicates": dup,
               "parity_mismatch": {str(k): len(v) for k, v in parity_mismatch.items()},
               "single": {}, "cumulative": {}}

    out(f"\nsingle invariants (of {len(mfds)} manifolds)\n{hdr}")
    rows = [("H1", lambda r: r["h1"]),
            # Unrecognised groups are lumped into one class, so this is a lower bound.
            ("pi1 recognised name", lambda r: r["pi1_name"] or "?")]
    for lv in levels:
        rows += [(f"TV_{lv} w=1", root1(lv)), (f"TV_{lv} all odd w", allroots(lv))]
        if lv % 2:
            rows.append((f"TV_{lv} all w", both(lv)))
    for name, key in rows:
        s = stats(mfds, key)
        summary["single"][name] = s
        out(f"{name:<34}{s['classes']:>9}{s['separated']:>11}{s['largest']:>9}")

    out(f"\ncumulative: H1 + TV_3..TV_R   (classes / separated)\n"
        f"{'R':<6}{'w=1':>22}{'all odd w':>22}{'all w':>22}")
    for lv in levels:
        cells = []
        for label, feat in (("root1", root1), ("all", allroots), ("both", both)):
            s = stats(mfds, combo(feat, lv))
            summary["cumulative"].setdefault(label, {})[str(lv)] = s
            cells.append(f"{s['classes']} / {s['separated']}")
        out(f"{lv:<6}" + "".join(f"{c:>22}" for c in cells))

    full = combo(both, levels[-1])
    full_classes = stats(mfds, full)["classes"]
    out("\ndrop-one: classes of H1 + TV_3..TV_R (all w) without TV_r "
        f"(full set: {full_classes})")
    drops = {}
    for lv in levels:
        others = [x for x in levels if x != lv]
        key = (lambda o: lambda r: (r["h1"],) + tuple(both(x)(r) for x in o))(others)
        drops[lv] = stats(mfds, key)["classes"]
    out("  " + ", ".join(f"-TV_{lv}: {n}" for lv, n in drops.items()))
    summary["drop_one"] = {str(k): v for k, v in drops.items()}
    needed = [lv for lv, n in drops.items() if n < full_classes]
    out(f"  levels that are not implied by the others: {needed}")

    # --- Survivors of everything.
    groups = sorted((g for g in partition(mfds, full).values() if len(g) > 1),
                    key=lambda g: (-len(g), g))
    pair_kinds = defaultdict(int)
    non_lens = []
    for g in groups:
        if all(LENS.match(m) for m in g):
            for i, a in enumerate(g):
                for b in g[i + 1:]:
                    pair_kinds[lens_relation(a, b)] += 1
        else:
            non_lens.append(g)
    out(f"\nsurvivors: {len(groups)} groups ({sum(map(len, groups))} manifolds) not separated "
        f"by H1 + TV_3..TV_{levels[-1]} at all roots w")
    out(f"  all-lens-space groups: {len(groups) - len(non_lens)}; "
        f"lens pairs by relation: {dict(pair_kinds)}")
    out(f"  groups containing a non-lens-space manifold: {len(non_lens)}")
    for g in non_lens[:25]:
        out("    " + " | ".join(f"{m} [pi1: {reps[m]['pi1_name'] or '?'}]" for m in g))
    if len(non_lens) > 25:
        out(f"    ... {len(non_lens) - 25} more in survivors.tsv")
    summary["survivors"] = {"groups": len(groups), "lens_pairs": dict(pair_kinds),
                            "non_lens_groups": len(non_lens)}

    with open(run_dir / "survivors.tsv", "w") as fh:
        fh.write("group\tsize\tmanifold\th1\tpi1_name\tlens_relation_to_first\n")
        for i, g in enumerate(groups):
            for m in g:
                rel = lens_relation(g[0], m) if m != g[0] else ""
                fh.write(f"{i}\t{reps[m]['size']}\t{m}\t{reps[m]['h1']}\t"
                         f"{reps[m]['pi1_name'] or ''}\t{rel or ''}\n")

    # --- Cost.
    out("\nmean seconds per invariant on representatives, by size")
    sizes = sorted({r["size"] for r in mfds})
    keys = ["h1", "pi1"] + [f"tv{lv}" for lv in levels]
    out(f"{'size':<6}{'n':>6}" + "".join(f"{k:>9}" for k in keys))
    summary["secs"] = {}
    for n in sizes:
        rs = [r for r in mfds if r["size"] == n]
        means = {k: sum(r["secs"][k] for r in rs) / len(rs) for k in keys}
        summary["secs"][str(n)] = means
        out(f"{n:<6}{len(rs):>6}" + "".join(f"{means[k]:>9.4f}" for k in keys))

    summary["run"] = {"dir": str(run_dir), **{k: meta.get(k) for k in
                      ("regina", "git", "params", "wall_seconds", "started")}}
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (run_dir / "report.txt").write_text("\n".join(out.lines) + "\n")
    if args.export:
        args.export.mkdir(parents=True, exist_ok=True)
        for f in ("summary.json", "survivors.tsv", "report.txt"):
            shutil.copy(run_dir / f, args.export / f)
        print(f"\nexported to {args.export}")


if __name__ == "__main__":
    main()

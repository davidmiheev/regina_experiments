#!/usr/bin/env python3
"""E03 - scramble, then simplify: when does greedy simplification fail?

All Regina work goes through mtengine (`rexp.engine`): pachner_walk, simplify_triangulations,
triangulation_invariants.

Part A (scramble). Manifolds: S3 plus up to --per-class minimal census triangulations from
each geometric class of the closed orientable census (lens spaces, Seifert fibred spaces,
graph manifolds, torus bundles, hyperbolic), chosen with a fixed seed. Each is scrambled with
k random 2-3 moves (k in --moves), either alone (mix44 = 0) or each followed by a random 4-4
move (mix44 = 1), for --seeds seeds. Then:
  * --trials independent greedy simplify() calls (randomised) -> sizes;
  * if the best is still above the census size n0, simplifyExhaustive at heights
    1..--max-height until n0 is reached;
  * the final triangulation is looked up in the census (must be the same manifold).

Part B (natural hard cases). E02's 1,494 non-minimal triangulations that one simplify()
call could not reduce (data/e02/hard_nonminimal.tsv), re-run through the same tool with the
same target sizes, to check the tool reproduces E02's heights.

Part C (recognition). 3-sphere recognition (triangulation_invariants, recognise=True) on
scrambled 3-spheres, with timings.
"""

import argparse
import csv
import os
import random
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _bootstrap  # noqa: E402,F401

from rexp import Run, iter_census  # noqa: E402
from rexp.engine import mte, value  # noqa: E402

EXPERIMENT = "e03_scramble_simplify"
ROOT = Path(__file__).resolve().parents[2]


def geometry_class(name: str) -> str:
    if name in ("S3",):
        return "S3"
    if name.startswith("L(") or name in ("RP3",):
        return "lens"
    if name.startswith("Hyp"):
        return "hyperbolic"
    if name.startswith("T x I"):
        return "torus bundle"
    if name.startswith("SFS") and re.search(r" U(/m)? ", name):
        return "graph"
    if name.startswith("SFS"):
        return "Seifert"
    return "other"


def choose_manifolds(per_class: int, seed: int) -> list[dict]:
    first = {}
    for label, tri in iter_census("closed-or"):
        name = label.split(" : #")[0]
        first.setdefault(name, {"manifold": name, "n0": tri.size(), "isosig": tri.isoSig(),
                                "class": geometry_class(name)})
    by_class = {}
    for m in first.values():
        by_class.setdefault(m["class"], []).append(m)
    rng = random.Random(seed)
    chosen = list(by_class.get("S3", []))
    for cls in ("lens", "Seifert", "graph", "torus bundle", "hyperbolic"):
        pool = sorted(by_class.get(cls, []), key=lambda m: m["manifold"])
        chosen += sorted(rng.sample(pool, min(per_class, len(pool))), key=lambda m: m["n0"])
    return chosen


def part_a(job: tuple) -> list[dict]:
    m, k, mix44, seeds, trials, max_height = job
    walks = value(mte.pachner_walk(m["isosig"], moves=k, seeds=seeds, mix44=mix44))
    res = mte.simplify_triangulations([w["isosig"] for w in walks], trials=trials,
                                      max_height=max_height, target_size=m["n0"], lookup=True)
    out = []
    for w, r in zip(walks, value(res)):
        names = [n.split(" : #")[0] for n in r.get("census", [])]
        out.append({"part": "A", "manifold": m["manifold"], "class": m["class"], "n0": m["n0"],
                    "moves": k, "mix44": mix44, "seed": w["seed"], "scrambled_size": w["size"],
                    "scrambled_isosig": w["isosig"], "greedy_sizes": r["greedy_sizes"],
                    "greedy_best": r["greedy_best"], "greedy_secs": r["greedy_secs"],
                    "exhaustive": r["exhaustive"], "final_size": r["final_size"],
                    "final_census": names, "same_manifold": m["manifold"] in names,
                    "batch_seconds": res["provenance"]["seconds"]})
    return out


def part_b(job: tuple) -> list[dict]:
    rows, trials, max_height = job
    out = []
    for row in rows:
        r = value(mte.simplify_triangulations([row["isosig"]], trials=trials,
                                              max_height=max_height,
                                              target_size=int(row["reduced_size"])))[0]
        out.append({"part": "B", "isosig": row["isosig"], "n": int(row["n"]),
                    "e02_height": int(row["height"]), "target": int(row["reduced_size"]),
                    "greedy_sizes": r["greedy_sizes"], "greedy_best": r["greedy_best"],
                    "exhaustive": r["exhaustive"], "final_size": r["final_size"]})
    return out


def part_c(job: tuple) -> dict:
    sig, k, seed = job
    res = mte.triangulation_invariants(sig, recognise=True)
    v = value(res)
    return {"part": "C", "moves": k, "seed": seed, "size": v["size"],
            "sphere": v["recognition"]["sphere"], "seconds": res["provenance"]["seconds"]}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--per-class", type=int, default=10)
    ap.add_argument("--moves", type=int, nargs="+", default=[5, 10, 20, 40, 80])
    ap.add_argument("--mix44", type=int, nargs="+", default=[0, 1])
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--trials", type=int, default=5)
    ap.add_argument("--max-height", type=int, default=2)
    ap.add_argument("--hard-max-height", type=int, default=3)
    ap.add_argument("--sphere-moves", type=int, nargs="+", default=[10, 20, 40, 80, 160])
    ap.add_argument("--choice-seed", type=int, default=0)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--resume", type=Path, metavar="RUN_DIR")
    args = ap.parse_args()
    params = {k: v for k, v in vars(args).items() if k != "resume"}

    manifolds = choose_manifolds(args.per_class, args.choice_seed)
    seeds = list(range(args.seeds))
    jobs_a = [(m, k, mix, seeds, args.trials, args.max_height)
              for m in manifolds for k in args.moves for mix in args.mix44]
    hard = list(csv.DictReader(open(ROOT / "data/e02/hard_nonminimal.tsv"), delimiter="\t"))
    jobs_b = [(hard[i:i + 25], args.trials, args.hard_max_height)
              for i in range(0, len(hard), 25)]
    s3 = next(m for m in manifolds if m["manifold"] == "S3")
    print(f"A: {len(manifolds)} manifolds x {len(args.moves)} k x {len(args.mix44)} mix x "
          f"{args.seeds} seeds; B: {len(hard)} hard triangulations; C: "
          f"{len(args.sphere_moves)} k x {args.seeds} seeds", file=sys.stderr)

    with Run(EXPERIMENT, params=params, resume=args.resume) as run, \
            ThreadPoolExecutor(max_workers=args.workers) as pool:
        done = {(r["part"], r.get("manifold"), r.get("moves"), r.get("mix44"), r.get("seed"),
                 r.get("isosig")) for r in run.existing}
        if not any(r["part"] == "M" for r in run.existing):
            for m in manifolds:
                run.record(part="M", **m)
        todo = [j for j in jobs_a if ("A", j[0]["manifold"], j[1], j[2], 0, None) not in done]
        for i, recs in enumerate(pool.map(part_a, todo), 1):
            for r in recs:
                run.record(**r)
            if i % 50 == 0:
                print(f"  A {i}/{len(todo)}", file=sys.stderr)
        todo = [j for j in jobs_b if ("B", None, None, None, None, j[0][0]["isosig"]) not in done]
        for recs in pool.map(part_b, todo):
            for r in recs:
                run.record(**r)
        walks = []
        for k in args.sphere_moves:
            for w in value(mte.pachner_walk(s3["isosig"], moves=k, seeds=seeds)):
                walks.append((w["isosig"], k, w["seed"]))
        todo = [j for j in walks if ("C", None, j[1], None, j[2], None) not in done]
        for r in pool.map(part_c, todo):
            run.record(**r)


if __name__ == "__main__":
    main()

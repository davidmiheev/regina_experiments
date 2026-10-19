#!/usr/bin/env python3
"""E01 - invariant sweep over the closed orientable census, all Turaev-Viro roots.

For every census triangulation record H1, Regina's simplified pi1 presentation
(+ recognised name) and, for r = 3..--r-max, the *exact* Turaev-Viro invariant
TV_r as an element of the cyclotomic field. For odd r both parities are
computed (q0 a primitive 2r-th or r-th root of unity).

The exact value determines TV_r at every admissible root of unity at once
(different roots are Galois conjugates), so equality of exact values is
equality at all roots. We also store the numerical value at each root, up to
complex conjugation, so analyze.py can compare "root 1 only" against "all roots".

Expensive TV levels (r > --check-r) are computed only on the first triangulation
of each manifold (`rep`); the cheap ones run on every triangulation so
analyze.py can check that they agree within each manifold.

Run analyze.py afterwards.
"""

import argparse
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _bootstrap  # noqa: E402,F401

import regina  # noqa: E402
from rexp import Run, iter_census  # noqa: E402

EXPERIMENT = "e01_closed_census_invariants"


def roots(r: int, parity: bool) -> list[int]:
    """Admissible whichRoot values w in (0, r) for TV_r, one per conjugate pair.

    w and 2r - w give complex-conjugate q0, hence the same (real) invariant.
    parity=True <-> odd w; parity=False (odd r only) <-> even w.
    """
    return [w for w in range(1, r) if math.gcd(w, r) == 1 and w % 2 == (1 if parity else 0)]


def evaluate(exact: regina.Cyclotomic, w: int, parity: bool) -> float:
    # For parity=False the value lives in the cyclotomic field of order r, where
    # q0 = exp(2*pi*i*w/2r) = exp(2*pi*i*(w/2)/r). (Regina's turaevViroApprox
    # docs say evaluate(w); empirically it is evaluate(w/2) - see README.)
    z = exact.evaluate(w if parity else w // 2)
    return round(z.real, 12)


def compute(job: tuple) -> dict:
    label, isosig, rep, r_max, check_r = job
    tri = regina.Triangulation3.fromIsoSig(isosig)
    rec = {"label": label, "manifold": label.split(" : #")[0], "size": tri.size(),
           "isosig": isosig, "rep": rep, "secs": {}}

    t0 = time.perf_counter()
    rec["h1"] = str(tri.homology())
    rec["secs"]["h1"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    pi1 = tri.fundamentalGroup()
    rec["pi1_gens"] = pi1.countGenerators()
    rec["pi1_rels"] = pi1.countRelations()
    rec["pi1_name"] = pi1.recogniseGroup() or None
    rec["secs"]["pi1"] = time.perf_counter() - t0

    # tv[r][parity] = exact value as a string; tv_roots[r][w] = real value at root w.
    rec["tv"], rec["tv_roots"] = {}, {}
    for r in range(3, (r_max if rep else check_r) + 1):
        t0 = time.perf_counter()
        exact, at_root = {}, {}
        for parity in ((True, False) if r % 2 else (True,)):
            v = tri.turaevViro(r, parity)
            exact["odd" if parity else "even"] = str(v)
            for w in roots(r, parity):
                at_root[str(w)] = evaluate(v, w, parity)
        rec["tv"][str(r)] = exact
        rec["tv_roots"][str(r)] = at_root
        rec["secs"][f"tv{r}"] = time.perf_counter() - t0
    return rec


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--census", default="closed-or")
    ap.add_argument("--max-size", type=int, default=None, help="default: whole census")
    ap.add_argument("--limit", type=int, default=None, help="stop after N triangulations")
    ap.add_argument("--r-max", type=int, default=10, help="largest TV level r (default 10)")
    ap.add_argument("--check-r", type=int, default=6,
                    help="TV levels <= this are also computed on non-representative "
                         "triangulations, for the consistency check (default 6)")
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--resume", type=Path, metavar="RUN_DIR",
                    help="finish an interrupted run (same parameters) in place")
    args = ap.parse_args()
    args.check_r = min(args.check_r, args.r_max)
    params = {k: v for k, v in vars(args).items() if k != "resume"}

    seen = set()
    jobs = []
    for label, tri in iter_census(args.census, max_size=args.max_size, limit=args.limit):
        manifold = label.split(" : #")[0]
        jobs.append((label, tri.isoSig(), manifold not in seen, args.r_max, args.check_r))
        seen.add(manifold)

    with Run(EXPERIMENT, params=params, resume=args.resume) as run, \
            ProcessPoolExecutor(max_workers=args.workers) as pool:
        done = {r["label"] for r in run.existing}
        todo = [j for j in jobs if j[0] not in done]
        print(f"{len(jobs)} triangulations of {len(seen)} manifolds, r = 3..{args.r_max}; "
              f"{len(todo)} to compute with {args.workers} workers", file=sys.stderr)
        for i, rec in enumerate(pool.map(compute, todo, chunksize=4), 1):
            run.record(**rec)
            if i % 1000 == 0:
                print(f"  {i}/{len(todo)}", file=sys.stderr)


if __name__ == "__main__":
    main()

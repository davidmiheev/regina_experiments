#!/usr/bin/env python3
"""E01 - invariant sweep over the closed orientable census.

For every minimal triangulation with <= --max-size tetrahedra record
H1, the (Regina-simplified) pi1 presentation (+ recognised name), Turaev-Viro
approximations TV_r for r in --tv, and per-invariant timings.

Run analyze.py afterwards to measure how well each invariant (and
combination) separates the distinct manifolds in the census.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _bootstrap  # noqa: E402,F401

from rexp import Run, iter_census, timed  # noqa: E402

EXPERIMENT = "e01_closed_census_invariants"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--census", default="closed-or")
    ap.add_argument("--max-size", type=int, default=6)
    ap.add_argument("--limit", type=int, default=None, help="stop after N triangulations")
    ap.add_argument("--tv", type=int, nargs="*", default=[3, 4, 5, 6, 7],
                    help="Turaev-Viro levels r (approximate, root 1)")
    args = ap.parse_args()

    with Run(EXPERIMENT, params=vars(args)) as run:
        for label, tri in iter_census(args.census, max_size=args.max_size, limit=args.limit):
            rec = {"label": label, "manifold": label.split(" : #")[0],
                   "size": tri.size(), "isosig": tri.isoSig(), "secs": {}}

            h1, rec["secs"]["h1"] = timed(tri.homology)
            rec["h1"] = str(h1)

            pi1, rec["secs"]["pi1"] = timed(tri.fundamentalGroup)
            rec["pi1_gens"] = pi1.countGenerators()
            rec["pi1_rels"] = pi1.countRelations()
            rec["pi1_name"] = pi1.recogniseGroup() or None

            rec["tv"] = {}
            for r in args.tv:
                val, rec["secs"][f"tv{r}"] = timed(tri.turaevViroApprox, r)
                rec["tv"][str(r)] = round(val, 10)

            run.record(**rec)


if __name__ == "__main__":
    main()

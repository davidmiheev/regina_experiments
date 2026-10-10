#!/usr/bin/env python3
"""EXX - <one-line title>.

Copy this directory to experiments/eXX_<slug>/ and fill in README.md.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _bootstrap  # noqa: E402,F401

from rexp import Run, iter_census, timed  # noqa: E402

EXPERIMENT = Path(__file__).resolve().parent.name


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--census", default="closed-or")
    ap.add_argument("--max-size", type=int, default=4)
    args = ap.parse_args()

    with Run(EXPERIMENT, params=vars(args)) as run:
        for label, tri in iter_census(args.census, max_size=args.max_size):
            value, secs = timed(tri.homology)
            run.record(label=label, size=tri.size(), value=str(value), secs=secs)


if __name__ == "__main__":
    main()

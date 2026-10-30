#!/usr/bin/env python3
"""E06 - hyperbolic censuses: angle structures vs SnapPea's geometry.

cusped-hyp-or / cusped-hyp-nor (ideal triangulations, <= 7 tetrahedra here):
  * hasStrictAngleStructure()          - linear programming;
  * AngleStructures(t)                 - all vertex angle structures, and
    spansStrict() / spansTaut()        - whether strict / taut ones exist;
  * SnapPeaTriangulation(t)            - solution type, volume (+ precision),
                                         smallest imaginary part of a shape.
closed-hyp (Hodgson-Weeks census; label = "<volume> : <cusped>(p, q)"):
  * SnapPea solution type and volume of the closed triangulation, sampled
    --closed-trials times because SnapPea's treatment of closed
    triangulations is randomised;
  * the Dehn filling named in the label, applied with fill(p, q) to the first
    census triangulation of the cusped manifold, and its volume; and the same
    with (-p, q), i.e. as if Regina's triangulation were SnapPy's mirror image.
"""

import argparse
import itertools
import json
import os
import re
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _bootstrap  # noqa: E402,F401

import regina  # noqa: E402
from rexp import Run, iter_census  # noqa: E402

EXPERIMENT = "e06_hyperbolic_angle_structures"
FILLING = re.compile(r"^([a-z]+)(\d+)((?:\(-?\d+, ?-?\d+\))+)$")


def snappea(tri) -> dict:
    s = regina.SnapPeaTriangulation(tri)
    if s.isNull():
        return {"solution": "null"}
    vol, digits = s.volumeWithPrecision()
    out = {"solution": s.solutionType().name, "volume": vol, "precision": digits}
    try:
        out["min_imag_shape"] = s.minImaginaryShape()
    except Exception:  # not defined for every solution type
        pass
    return out


def cusped(job: tuple) -> dict:
    census, label, sig = job
    tri = regina.Triangulation3.fromIsoSig(sig)
    name = label.split(" : ")[0]
    m = re.match(r"([a-z]+)(\d+)$", name)
    rec = {"kind": "cusped", "census": census, "label": label, "manifold": name,
           "prefix": m[1], "index": int(m[2]), "n": tri.size(),
           "orientable": tri.isOrientable(), "cusps": tri.countBoundaryComponents(),
           "secs": {}}
    t0 = time.perf_counter()
    rec["strict_lp"] = regina.Triangulation3(tri).hasStrictAngleStructure()
    rec["secs"]["lp"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    angles = regina.AngleStructures(tri)
    rec["angle_vertices"] = angles.size()
    rec["strict"] = angles.spansStrict()
    rec["taut"] = angles.spansTaut()
    rec["secs"]["angles"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    rec.update(snappea(tri))
    rec["secs"]["snappea"] = time.perf_counter() - t0
    return rec


def fill(base_sig: str, slopes: list) -> dict:
    # A fresh SnapPea triangulation per filling: SnapPea starts each solve from
    # the previous solution, so refilling one object makes results path-dependent.
    s = regina.SnapPeaTriangulation(regina.Triangulation3.fromIsoSig(base_sig))
    ok = all(s.fill(p, q, i) for i, (p, q) in enumerate(slopes))
    vol, digits = s.volumeWithPrecision()
    return {"ok": ok, "slopes": slopes, "solution": s.solutionType().name,
            "volume": vol, "precision": digits}


def closed(job: tuple) -> dict:
    label, sig, base_sig, closed_trials = job
    vol_text, filling = label.split(" : ")
    rec = {"kind": "closed", "census": "closed-hyp", "label": label, "filling": filling,
           "label_volume": float(vol_text), "label_digits": len(vol_text.split(".")[1]),
           "n": None, "secs": {}}
    tri = regina.Triangulation3.fromIsoSig(sig)
    rec["n"] = tri.size()
    # SnapPea's handling of a closed triangulation is randomised (the outcome
    # varies between constructions), so sample it independently several times.
    t0 = time.perf_counter()
    trials = [snappea(tri) for _ in range(closed_trials)]
    rec["secs"]["closed"] = (time.perf_counter() - t0) / closed_trials
    rec["closed"] = trials[0]
    rec["closed_trials"] = {
        "n": closed_trials,
        "solutions": dict(Counter(t["solution"] for t in trials)),
        "volume_correct": sum(abs(t["volume"] - rec["label_volume"]) < 1e-8 for t in trials),
        "first_correct": next((i + 1 for i, t in enumerate(trials)
                               if abs(t["volume"] - rec["label_volume"]) < 1e-8), None)}
    m = FILLING.match(filling.replace(" ", ""))
    if base_sig and m:
        slopes = [(int(p), int(q)) for p, q in re.findall(r"\((-?\d+),(-?\d+)\)", m[3])]
        t0 = time.perf_counter()
        rec["filled"] = fill(base_sig, slopes)
        # Regina's census triangulation may be the mirror image of SnapPy's
        # manifold of the same name, which reverses each slope: (p, q) -> (-p, q).
        rec["filled_mirror"] = fill(base_sig, [(-p, q) for p, q in slopes])
        rec["secs"]["filled"] = time.perf_counter() - t0
    else:
        rec["filled"] = rec["filled_mirror"] = None
    return rec


def framing(job: tuple) -> dict:
    """Find every change of peripheral basis (p, q) -> (a p + b q, c p + d q),
    |entries| <= 3 and ad - bc = +-1, that reproduces all labelled volumes."""
    base_name, base_sig, fillings = job
    mats = [m for m in itertools.product(range(-3, 4), repeat=4)
            if abs(m[0] * m[3] - m[1] * m[2]) == 1]
    good = []
    for a, b, c, d in mats:
        if all(abs(fill(base_sig, [(a * p + b * q, c * p + d * q)])["volume"] - vol) < 1e-8
               for (p, q), vol in fillings):
            good.append([a, b, c, d])
    return {"kind": "framing", "census": "closed-hyp", "label": base_name,
            "fillings": len(fillings), "matrices": good}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=None, help="per census, for testing")
    ap.add_argument("--closed-trials", type=int, default=20,
                    help="independent SnapPea constructions per closed triangulation")
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--resume", type=Path, metavar="RUN_DIR")
    args = ap.parse_args()
    params = {"limit": args.limit, "closed_trials": args.closed_trials, "workers": args.workers}

    jobs_c, base = [], {}
    for census in ("cusped-hyp-or", "cusped-hyp-nor"):
        for label, tri in iter_census(census, limit=args.limit):
            jobs_c.append((census, label, tri.isoSig()))
            # Base manifolds for the closed census's Dehn fillings. Names are
            # disjoint between the two cusped censuses; the closed census also
            # contains a few non-orientable fillings of non-orientable bases.
            if label.endswith(" : #1"):
                base[label.split(" : ")[0]] = tri.isoSig()
    jobs_h = []
    for label, tri in iter_census("closed-hyp", limit=args.limit):
        m = FILLING.match(label.split(" : ")[1].replace(" ", ""))
        jobs_h.append((label, tri.isoSig(), base.get(m[1] + m[2]) if m else None,
                       args.closed_trials))
    print(f"{len(jobs_c)} cusped and {len(jobs_h)} closed triangulations", file=sys.stderr)

    with Run(EXPERIMENT, params=params, resume=args.resume) as run, \
            ProcessPoolExecutor(max_workers=args.workers) as pool:
        done = {(r["census"], r["label"]) for r in run.existing}
        todo_c = [j for j in jobs_c if (j[0], j[1]) not in done]
        todo_h = [j for j in jobs_h if ("closed-hyp", j[0]) not in done]
        for rec in pool.map(cusped, todo_c, chunksize=16):
            run.record(**rec)
        for rec in pool.map(closed, todo_h, chunksize=8):
            run.record(**rec)

        # Bases whose labelled volumes match neither (p, q) nor (-p, q): search
        # for the change of peripheral basis instead.
        recs = run.existing + [json.loads(line) for line in open(run.dir / "records.jsonl")
                               ][len(run.existing):]
        groups = {}
        for r in recs:
            if r["kind"] == "closed" and r["filled"] and len(r["filled"]["slopes"]) == 1:
                groups.setdefault(r["filling"].split("(")[0], []).append(r)
        close = lambda f, v: abs(f["volume"] - v) < 1e-8  # noqa: E731
        todo_f = [(name, base[name], [(tuple(r["filled"]["slopes"][0]), r["label_volume"])
                                      for r in rs])
                  for name, rs in sorted(groups.items())
                  if not all(close(r["filled"], r["label_volume"]) for r in rs)
                  and not all(close(r["filled_mirror"], r["label_volume"]) for r in rs)
                  and ("closed-hyp", name) not in done]
        for rec in pool.map(framing, todo_f):
            run.record(**rec)


if __name__ == "__main__":
    main()

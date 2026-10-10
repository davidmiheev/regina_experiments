#!/usr/bin/env python3
"""E00 - smoke test: does each part of Regina we rely on give known answers?

Exits non-zero if any check fails. Runs in a few seconds.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _bootstrap  # noqa: E402,F401

import regina  # noqa: E402
from rexp import timed  # noqa: E402

E3, E4, EL = regina.Example3, regina.Example4, regina.ExampleLink


def checks():
    # (name, thunk, predicate on result)
    yield "H1(L(7,2)) = Z_7", lambda: str(E3.lens(7, 2).homology()), lambda r: r == "Z_7"
    yield "H1(Poincare) = 0", lambda: str(E3.poincare().homology()), lambda r: r == "0"
    yield "S3 recognised", lambda: E3.threeSphere().isSphere(), lambda r: r is True
    yield "Poincare is not S3", lambda: E3.poincare().isSphere(), lambda r: r is False
    yield "RP3 # RP3 has 2 summands", lambda: len(E3.rp3rp3().summands()), lambda r: r == 2
    yield "census lookup: figure-eight = m004", \
        lambda: [h.name() for h in regina.Census.lookup(E3.figureEight())], \
        lambda r: any(n.startswith("m004") for n in r)
    yield "vol(figure-eight) ~ 2.029883", \
        lambda: regina.SnapPeaTriangulation(E3.figureEight()).volume(), \
        lambda r: abs(r - 2.0298832128) < 1e-8
    yield "vol(Weeks) ~ 0.942707", \
        lambda: regina.SnapPeaTriangulation(E3.weeks()).volume(), \
        lambda r: abs(r - 0.9427073628) < 1e-8
    yield "fig-8 has strict angle structure", \
        lambda: regina.AngleStructures(E3.figureEight()).spansStrict(), lambda r: r is True
    yield "fig-8: 4 vertex quad normal surfaces", \
        lambda: regina.NormalSurfaces(E3.figureEight(), regina.NormalCoords.Quad).size(), \
        lambda r: r == 4
    yield "TV_5 distinguishes S3 from L(5,1)", \
        lambda: (str(E3.threeSphere().turaevViro(5)), str(E3.lens(5, 1).turaevViro(5))), \
        lambda r: r[0] != r[1]
    yield "Jones(right trefoil)", lambda: str(EL.trefoilRight().jones()), \
        lambda r: r == "-x^8 + x^6 + x^2"   # Regina uses x = sqrt(t)
    yield "fig-8 knot complement = m004", \
        lambda: [h.name() for h in regina.Census.lookup(EL.figureEight().complement())], \
        lambda r: any(n.startswith("m004") for n in r)
    yield "chi(CP2) = 3", lambda: E4.cp2().eulerCharManifold(), lambda r: r == 3
    yield "K3 intersection form: rank 22, sig -16, even", \
        lambda: (lambda f: (f.rank(), f.signature(), f.even()))(E4.k3().intersectionForm()), \
        lambda r: r == (22, -16, True)


def main() -> int:
    print(f"Regina {regina.versionString()}  (Python {sys.version.split()[0]})")
    failed = 0
    for name, thunk, ok in checks():
        try:
            result, secs = timed(thunk)
            passed = ok(result)
        except Exception as exc:  # report and keep going
            result, secs, passed = f"{type(exc).__name__}: {exc}", 0.0, False
        failed += not passed
        print(f"  [{'PASS' if passed else 'FAIL'}] {name:<45} {secs*1000:8.1f} ms  {result}")
    print("OK" if not failed else f"{failed} check(s) FAILED")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

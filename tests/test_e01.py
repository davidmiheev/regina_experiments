import importlib.util
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import regina  # noqa: E402


def _load(name):
    path = ROOT / "experiments/e01_closed_census_invariants" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"e01_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


run = _load("run")
analyze = _load("analyze")


class RootsTest(unittest.TestCase):
    def test_roots_cover_every_admissible_root_up_to_conjugation(self):
        for r in range(3, 13):
            ws = run.roots(r, True) + (run.roots(r, False) if r % 2 else [])
            expected = [w for w in range(1, 2 * r) if math.gcd(w, r) == 1]
            if r % 2 == 0:  # q0 must be a primitive 2r-th root: odd w only
                expected = [w for w in expected if w % 2]
            self.assertEqual(sorted({min(w, 2 * r - w) for w in expected}), sorted(ws))

    def test_exact_evaluation_matches_turaev_viro_approx(self):
        tri = regina.Example3.poincare()
        for r in (4, 5, 6, 7):
            for parity in ((True, False) if r % 2 else (True,)):
                exact = tri.turaevViro(r, parity)
                for w in run.roots(r, parity):
                    self.assertAlmostEqual(run.evaluate(exact, w, parity),
                                           tri.turaevViroApprox(r, w), places=8,
                                           msg=f"r={r} w={w}")

    def test_compute_record(self):
        rec = run.compute(("L(7,2) : #1", regina.Example3.lens(7, 2).isoSig(), True, 5, 4))
        self.assertEqual(rec["h1"], "Z_7")
        self.assertEqual(sorted(rec["tv"]), ["3", "4", "5"])
        self.assertEqual(sorted(rec["tv"]["5"]), ["even", "odd"])


class LensTest(unittest.TestCase):
    def test_lens_relation(self):
        self.assertEqual(analyze.lens_relation("L(7,2)", "L(7,4)"), "homeomorphic")  # 2*4 = 1
        self.assertEqual(analyze.lens_relation("L(7,1)", "L(7,2)"), "homotopy-equivalent")
        self.assertEqual(analyze.lens_relation("L(5,1)", "L(5,2)"), "not homotopy-equivalent")
        self.assertIsNone(analyze.lens_relation("L(5,1)", "L(7,1)"))
        self.assertIsNone(analyze.lens_relation("S3", "L(7,1)"))


if __name__ == "__main__":
    unittest.main()

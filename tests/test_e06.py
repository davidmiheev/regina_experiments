import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import regina  # noqa: E402

path = ROOT / "experiments/e06_hyperbolic_angle_structures/run.py"
spec = importlib.util.spec_from_file_location("e06_run", path)
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)


class E06Test(unittest.TestCase):
    def test_cusped_record_figure_eight(self):
        sig = regina.Example3.figureEight().isoSig()
        rec = run.cusped(("cusped-hyp-or", "m004 : #1", sig))
        self.assertTrue(rec["strict"] and rec["strict_lp"] and rec["taut"])
        self.assertEqual(rec["solution"], "Geometric")
        self.assertAlmostEqual(rec["volume"], 2.0298832128, places=9)
        self.assertEqual((rec["prefix"], rec["index"], rec["cusps"]), ("m", 4, 1))

    def test_fill_weeks_from_m003(self):
        # The Weeks manifold is m003(-3, 1) in the Hodgson-Weeks census, and
        # Regina's m003 needs no mirroring for it.
        m003 = next(t for label, t in run.iter_census("cusped-hyp-or")
                    if label == "m003 : #1")
        f = run.fill(m003.isoSig(), [(-3, 1)])
        self.assertEqual(f["solution"], "Geometric")
        self.assertAlmostEqual(f["volume"], 0.9427073627769, places=9)

    def test_filling_label_parser(self):
        m = run.FILLING.match("m003(-3,1)")
        self.assertEqual((m[1], m[2], m[3]), ("m", "003", "(-3,1)"))


if __name__ == "__main__":
    unittest.main()

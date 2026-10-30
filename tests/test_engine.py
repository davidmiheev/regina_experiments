import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

try:
    from rexp.engine import engine_version, mte, value
except ImportError:  # submodule not checked out (e.g. CI without access to mtengine)
    mte = None


@unittest.skipIf(mte is None, "engine/ submodule not available")
class EngineTest(unittest.TestCase):
    def test_regina_backend_reachable(self):
        self.assertTrue(mte.versions()["regina"].startswith("Regina "))
        self.assertIn("@", engine_version())

    def test_census_lookup_through_engine(self):
        names = [h["name"] for h in value(mte.census_lookup("cPcbbbiht"))]
        self.assertIn("m004 : #1", names)

    def test_scramble_and_simplify(self):
        walk = value(mte.pachner_walk("fvPQcdecedekrsnrs", moves=6, seeds=[0]))[0]
        r = value(mte.simplify_triangulations([walk["isosig"]], trials=3, max_height=1,
                                              target_size=5, lookup=True))[0]
        self.assertEqual((walk["size"], r["final_size"]), (11, 5))
        self.assertTrue(any(n.startswith("SFS [S2: (2,1) (3,1) (5,-4)]") for n in r["census"]))


if __name__ == "__main__":
    unittest.main()

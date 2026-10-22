import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def _load(name):
    path = ROOT / "experiments/e02_tricensus_regeneration" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"e02_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


run = _load("run")


class GenerateTest(unittest.TestCase):
    def test_chunked_generation_matches_direct(self):
        with tempfile.TemporaryDirectory() as d:
            direct, chunked = Path(d, "direct"), Path(d, "chunked")
            direct.mkdir()
            chunked.mkdir()
            a = run.generate(6, 2, direct)
            b = run.generate(6, 2, chunked, chunk=10)
            self.assertEqual(a["triangulations"], b["triangulations"])
            self.assertEqual(a["pairings"], b["pairings"])
            sigs = lambda p: sorted((p / "n6.sigs").read_text().split())
            self.assertEqual(sigs(direct), sigs(chunked))
            # Cached: a second call returns the stored info without rerunning.
            self.assertEqual(run.generate(6, 2, chunked, chunk=10), json.loads(
                (chunked / "n6.json").read_text()))

    def test_classify(self):
        # A census triangulation, and a 2-tetrahedron triangulation that is not minimal.
        with tempfile.TemporaryDirectory() as d:
            run.generate(2, 1, Path(d))
            sigs = (Path(d) / "n2.sigs").read_text().split()
        statuses = {run.classify((2, s, 2))["status"] for s in sigs}
        self.assertIn("census", statuses)
        self.assertTrue(statuses <= {"census", "simplify"})


if __name__ == "__main__":
    unittest.main()

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import regina  # noqa: E402
from rexp import CENSUSES, Run, iter_census, timed  # noqa: E402


class CensusTest(unittest.TestCase):
    def test_every_census_file_opens(self):
        for name in CENSUSES:
            with self.subTest(census=name):
                label, obj = next(iter_census(name))
                self.assertTrue(label)
                self.assertGreater(obj.size(), 0)

    def test_size_filter_and_limit(self):
        items = list(iter_census("closed-or", max_size=2))
        self.assertTrue(items)
        self.assertTrue(all(t.size() <= 2 for _, t in items))
        self.assertEqual(len(list(iter_census("closed-or", limit=3))), 3)

    def test_closed_census_is_closed_orientable(self):
        for _, tri in iter_census("closed-or", max_size=3):
            self.assertTrue(tri.isClosed() and tri.isOrientable() and tri.isValid())

    def test_unknown_census(self):
        with self.assertRaises(ValueError):
            next(iter_census("nope"))


class RunTest(unittest.TestCase):
    def test_writes_meta_and_records(self):
        with tempfile.TemporaryDirectory() as d:
            with Run("unit", params={"x": 1}, results_dir=Path(d)) as run:
                h, secs = timed(regina.Example3.lens(5, 2).homology)
                run.record(h1=str(h), secs=secs)
            meta = json.loads((run.dir / "meta.json").read_text())
            self.assertEqual(meta["status"], "ok")
            self.assertEqual(meta["records"], 1)
            self.assertEqual(meta["regina"], regina.versionString())
            rec = json.loads((run.dir / "records.jsonl").read_text())
            self.assertEqual(rec["h1"], "Z_5")


    def test_resume_appends_and_drops_truncated_line(self):
        with tempfile.TemporaryDirectory() as d:
            with Run("unit", params={"x": 1, "workers": 2}, results_dir=Path(d)) as run:
                run.record(label="a")
                run.record(label="b")
            with open(run.dir / "records.jsonl", "a") as fh:
                fh.write('{"label": "c", "cut')          # simulate a kill mid-write
            with Run("unit", params={"x": 1, "workers": 8}, resume=run.dir) as again:
                self.assertEqual([r["label"] for r in again.existing], ["a", "b"])
                again.record(label="c")
            labels = [json.loads(l)["label"] for l in open(run.dir / "records.jsonl")]
            self.assertEqual(labels, ["a", "b", "c"])
            meta = json.loads((run.dir / "meta.json").read_text())
            self.assertEqual(meta["records"], 3)
            self.assertEqual(meta["resumes"][0]["records_before"], 2)
            with self.assertRaises(ValueError):
                Run("unit", params={"x": 2}, resume=run.dir)


class SmokeTest(unittest.TestCase):
    def test_smoke_experiment_passes(self):
        proc = subprocess.run([sys.executable, str(ROOT / "experiments/e00_smoke/run.py")],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""E02 - regenerate the closed orientable census with tricensus and compare.

For n = 1..--max-n:
  1. Generate: `tricensus -t n -i -f -o -M -s` (closed, orientable, ignoring
     obviously non-minimal / non-prime triangulations) -> isomorphism
     signatures. Cached in RUN_DIR/tricensus/ so an interrupted run resumes.
  2. Classify every generated triangulation:
       census       - its isoSig is in the shipped closed orientable census;
       simplify     - simplify() reduces it (certified non-minimal);
       S3 / nonprime- 3-sphere (non-minimal for n > 1) or connected sum;
       exhaustive:h - simplifyExhaustive(h) reduces it, smallest h <= --max-height;
       unresolved   - none of the above (would be a census discrepancy).
  3. Record census triangulations of size n that tricensus did NOT produce.

Expected outcome: census(n) is a subset of tricensus(n), and everything else is
certified non-minimal or non-prime.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _bootstrap  # noqa: E402,F401

import regina  # noqa: E402
from rexp import Run, iter_census  # noqa: E402

EXPERIMENT = "e02_tricensus_regeneration"
CENSUS_DB = "Closed census (orientable)"


def census_name(sig: str) -> str | None:
    hits = [h for h in regina.Census.lookup(sig) if h.db().desc() == CENSUS_DB]
    return hits[0].name() if hits else None


def generate(n: int, threads: int, outdir: Path, chunk: int | None = None) -> dict:
    """Run tricensus for n tetrahedra (or reuse a finished earlier run).

    With ``chunk`` set, first list the face pairings (`tricensus -p`), then
    process them in chunks of that many pairings (`tricensus -P`), each a
    single-threaded job cached on disk, so a killed run only repeats the
    chunks in flight.
    """
    sigs, log, done = (outdir / f"n{n}.{ext}" for ext in ("sigs", "log", "json"))
    if done.exists():
        return json.loads(done.read_text())
    if chunk:
        info = generate_chunked(n, threads, outdir, chunk)
    else:
        cmd = ["tricensus", "-t", str(n), "-i", "-f", "-o", "-M", "-s",
               f"--threads={threads}", str(sigs)]
        t0 = time.perf_counter()
        with open(log, "w") as fh:
            subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT, check=True)
        secs = time.perf_counter() - t0
        text = log.read_text()
        # tricensus logs each face pairing it processes as "a:b c:d ... | ...".
        pairings = sum(1 for line in text.splitlines() if re.match(r"^\d+:\d+", line))
        total = re.search(r"Total triangulations: (\d+)", text)
        info = {"n": n, "cmd": " ".join(cmd[:-1]), "secs": secs, "pairings": pairings,
                "triangulations": int(total[1]) if total else None, "threads": threads}
    done.write_text(json.dumps(info, indent=2) + "\n")
    return info


def _run_chunk(job: tuple) -> float:
    pairs, out, log, mark = job
    t0 = time.perf_counter()
    with open(pairs) as fin, open(log, "w") as fh:
        # Boundary options are implied by the pairings and rejected with -P.
        subprocess.run(["tricensus", "-P", "-f", "-o", "-M", "-s", str(out)],
                       stdin=fin, stdout=fh, stderr=subprocess.STDOUT, check=True)
    secs = time.perf_counter() - t0
    mark.write_text(json.dumps({"secs": secs}) + "\n")
    return secs


def generate_chunked(n: int, threads: int, outdir: Path, chunk: int) -> dict:
    work = outdir / f"n{n}.chunks"
    work.mkdir(exist_ok=True)
    pairs = work / "pairings.txt"
    pairs_done = work / "pairings.json"
    if not pairs_done.exists():
        t0 = time.perf_counter()
        subprocess.run(["tricensus", "-t", str(n), "-i", "-p", str(pairs)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, check=True)
        pairs_done.write_text(json.dumps({"secs": time.perf_counter() - t0}) + "\n")
    lines = pairs.read_text().splitlines()
    jobs = []
    for i in range(0, len(lines), chunk):
        stem = work / f"c{i // chunk:04d}"
        mark = stem.with_suffix(".json")
        if not mark.exists():
            stem.with_suffix(".pairs").write_text("\n".join(lines[i:i + chunk]) + "\n")
            jobs.append((stem.with_suffix(".pairs"), stem.with_suffix(".sigs"),
                         stem.with_suffix(".log"), mark))
    nchunks = -(-len(lines) // chunk)
    print(f"n={n}: {len(lines)} face pairings in {nchunks} chunks, "
          f"{len(jobs)} still to run", file=sys.stderr)
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=threads) as pool:
        for k, _ in enumerate(pool.map(_run_chunk, jobs), 1):
            if k % 10 == 0:
                print(f"  n={n}: chunk {k}/{len(jobs)}", file=sys.stderr)
    with open(outdir / f"n{n}.sigs", "w") as out:
        for i in range(nchunks):
            out.write((work / f"c{i:04d}.sigs").read_text())
    chunk_secs = sum(json.loads((work / f"c{i:04d}.json").read_text())["secs"]
                     for i in range(nchunks))
    total = sum(1 for _ in open(outdir / f"n{n}.sigs"))
    pair_secs = json.loads(pairs_done.read_text())["secs"]
    return {"n": n, "cmd": "tricensus -t n -i -p | split | tricensus -P -f -o -M -s",
            "pairings": len(lines), "triangulations": total, "threads": threads,
            "chunks": nchunks, "chunk_size": chunk,
            # One thread per chunk: the sum is thread-seconds. Dividing by the
            # thread count gives a wall-clock equivalent comparable with the
            # unchunked sizes (which ran with --threads).
            "thread_secs": pair_secs + chunk_secs,
            "secs": pair_secs + chunk_secs / threads,
            "wall_this_session": time.perf_counter() - t0}


def classify(job: tuple) -> dict:
    n, sig, max_height = job
    rec = {"kind": "generated", "n": n, "isosig": sig, "secs": {}}
    t0 = time.perf_counter()
    name = census_name(sig)
    rec["secs"]["lookup"] = time.perf_counter() - t0
    if name:
        rec.update(status="census", census_name=name)
        return rec

    tri = regina.Triangulation3.fromIsoSig(sig)
    t0 = time.perf_counter()
    small = regina.Triangulation3(tri)
    small.simplify()
    rec["secs"]["simplify"] = time.perf_counter() - t0
    if small.size() < n:
        rec.update(status="simplify")
    elif tri.isSphere():
        rec.update(status="S3")
    elif len(tri.summands()) >= 2:
        rec.update(status="nonprime")
    else:
        rec["status"] = "unresolved"
        for h in range(1, max_height + 1):
            t0 = time.perf_counter()
            small = regina.Triangulation3(tri)
            small.simplifyExhaustive(h)
            rec["secs"][f"exhaustive{h}"] = time.perf_counter() - t0
            if small.size() < n:
                rec["status"] = f"exhaustive:{h}"
                break

    # Which census manifold is it?  Simplify the reduced triangulation further
    # and look it up; most land on a minimal census triangulation.
    if rec["status"] != "unresolved":
        small.simplify()
        rec["reduced_size"] = small.size()
        rec["reduced_name"] = census_name(small.isoSig())
    return rec


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--max-n", type=int, default=9)
    ap.add_argument("--max-height", type=int, default=3,
                    help="largest simplifyExhaustive height to try (default 3)")
    ap.add_argument("--threads", type=int, default=os.cpu_count(),
                    help="threads for tricensus and classification workers")
    ap.add_argument("--chunk-from", type=int, default=10,
                    help="generate sizes >= this in resumable chunks (default 10)")
    ap.add_argument("--chunk", type=int, default=500, help="face pairings per chunk")
    ap.add_argument("--resume", type=Path, metavar="RUN_DIR")
    args = ap.parse_args()
    params = {"max_n": args.max_n, "max_height": args.max_height, "workers": args.threads}

    census = {}
    for _, tri in iter_census("closed-or", max_size=args.max_n):
        census.setdefault(tri.size(), set()).add(tri.isoSig())

    with Run(EXPERIMENT, params=params, resume=args.resume) as run, \
            ProcessPoolExecutor(max_workers=args.threads) as pool:
        outdir = run.dir / "tricensus"
        outdir.mkdir(exist_ok=True)
        done = {(r["kind"], r["n"], r.get("isosig")) for r in run.existing}
        for n in range(1, args.max_n + 1):
            info = generate(n, args.threads, outdir,
                            args.chunk if n >= args.chunk_from else None)
            if ("generation", n, None) not in done:
                run.record(kind="generation", **info)
            sigs = [s.strip() for s in open(outdir / f"n{n}.sigs") if s.strip()]
            print(f"n={n}: {len(sigs)} triangulations in {info['secs']:.1f} s; "
                  f"census has {len(census.get(n, ()))}", file=sys.stderr)
            todo = [(n, s, args.max_height) for s in sigs
                    if ("generated", n, s) not in done]
            for rec in pool.map(classify, todo, chunksize=16):
                run.record(**rec)
            for sig in sorted(census.get(n, set()) - set(sigs)):
                if ("missing", n, sig) not in done:
                    run.record(kind="missing", n=n, isosig=sig, census_name=census_name(sig))


if __name__ == "__main__":
    main()

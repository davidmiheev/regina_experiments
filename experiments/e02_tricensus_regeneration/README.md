# E02 — Regenerate the closed census with `tricensus` ✅

**Full writeup:** [writeup.md](writeup.md) · [writeup.pdf](writeup.pdf)

**Question.** Does Regina's own generator, run from scratch, reproduce the
shipped closed orientable census? That is: is every census triangulation
generated, and is every other generated triangulation provably non-minimal
or non-prime?

**Method.**
- `run.py` runs `tricensus -t n -i -f -o -M -s` for each n. The flags mean
  closed, orientable, and ignore obviously non-minimal or non-prime
  triangulations. Generation output is cached in the run directory.
- Each generated triangulation is classified as one of: in the census (by
  isoSig lookup); reduced by `simplify()`; a 3-sphere; non-prime; reduced by
  `simplifyExhaustive(h)` for h ≤ 3; or unresolved.
- Census triangulations that `tricensus` never produced are recorded as
  missing.
- `retry.py` (E02b) reruns the randomised `simplify()` many times on every
  non-minimal triangulation, to measure how reliable a single call is.

**Sanity checks.** For every n, missing = 0 and unresolved = 0.

**Run.**
```sh
make e02 ARGS="--max-n 10"   # n = 10: 10.8 thread-hours, chunked and resumable
make e02-retry ARGS=results/e02_tricensus_regeneration/<run>
make e02-export ARGS=results/e02_tricensus_regeneration/<run>
make writeups
```

**Results** (Regina 7.4.1, 2026-10-22):
- The census is reproduced exactly for n ≤ 10. `tricensus` generated
  66,439 triangulations, including all 14,720 census triangulations (0
  missing). The other 51,719 are each certified non-minimal or non-prime
  (0 unresolved).
- One `simplify()` call settles 97.1% of the non-minimal triangulations.
  The other 1,494 need `simplifyExhaustive` at height 1 (567), 2 (926)
  or 3 (1). There are also two 3-spheres and two copies of
  L(5,1) # L(5,1).
- The `simplify()` reliability test (50 calls each) shows:
  - one call fails with probability 2.7% at n = 10;
  - triangulations that need height ≥ 2 are never reduced;
  - `simplifyToLocalMinimum()` reduces nothing, because the `tricensus -M`
    filter already removes what it would catch.
- Generation grows about 25× per tetrahedron. At n = 10, 3 of 97 chunks
  took 62% of the thread time.
- Hard benchmark set for E03: `data/e02/hard_nonminimal.tsv`.

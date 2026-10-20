# E02 — Regenerate the closed census with `tricensus` 🟡

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
make e02 ARGS="--max-n 10"                     # n = 10 takes ~1.5 h on 4 threads
make e02-retry ARGS=results/e02_tricensus_regeneration/<run>
make e02-export ARGS=results/e02_tricensus_regeneration/<run>
make writeups
```

**Results.** In progress. Up to n = 8 the census is reproduced exactly: all
1,445 census triangulations are generated, and the other 1,756 are all
certified non-minimal.

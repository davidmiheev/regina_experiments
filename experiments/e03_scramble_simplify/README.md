# E03 — Scramble, then simplify ✅

**Full writeup:** [writeup.md](writeup.md) · [writeup.pdf](writeup.pdf)

**Question.** How often does Regina's greedy `simplify()` fail to undo random
Pachner moves, and what does it take to recover?

**Method** (all through mtengine: `pachner_walk`, `simplify_triangulations`,
`triangulation_invariants`):
- **A.** 51 census manifolds (S³ plus 10 per geometric class), scrambled with
  k ∈ {5…160} random 2-3 moves and 0, 1 or 4 random 4-4 moves per step, 10 seeds
  each (9,180 scrambles). Each gets 5 greedy calls, then exhaustive search
  until the census size n0 is reached.
- **B.** E02's 1,494 hard non-minimal triangulations.
- **C.** 3-sphere recognition on scrambled 3-spheres.

**Results** (Regina 7.4.1, mtengine 768bbaa, 2026-10-30, 4 min on 4 cores):
- **Everything comes back.** All 9,180 scrambles returned to n0 as the same
  manifold; exhaustive search needed at most height 2.
- **Single calls do fail.** One `simplify()` call fails 2.3% of the time and
  the best of 5 fails 0.9%. Random 4-4 mixing triples the failure rate; walk
  length stops mattering beyond about 40 moves.
- **Difficulty depends on the manifold.** Lens, graph and hyperbolic manifolds
  are sometimes hard; torus bundles and S³ never were. Hyperbolic failures go
  away with retries, while lens, Seifert and graph manifolds sometimes need
  exhaustive search.
- **E02 is reproduced exactly** through mtengine, and all 50 scrambled
  3-spheres were recognised in under 0.6 s.

**Run.** `make engine && make e03 ARGS="--moves 5 10 20 40 80 160 --mix44 0 1 4" && make e03-export ARGS=results/e03_scramble_simplify/<run> && make writeups`

# E01 — Turaev–Viro invariants on the closed orientable census ✅

**Full writeup:** [writeup.md](writeup.md) · [writeup.pdf](writeup.pdf)

**Question.** Among the 4,979 manifolds in Regina's closed orientable census
(≤ 10 tetrahedra), how many do H₁ and the Turaev–Viro invariants TV_r
(r ≤ 10, at all roots of unity) tell apart, and which groups survive?

**Method.** `run.py` computes, for each of the 14,720 triangulations: H₁,
π₁, and the exact TV_r for r = 3..6 (both parities for odd r). For one
triangulation per manifold it also computes r = 7..10. Each exact value is
evaluated at every root w. `analyze.py` checks consistency and compares one
root against all roots. It also reports drop-one tables, survivor groups
classified by lens-space homotopy type, and cost. `figures.py` draws the
charts from `data/e01/summary.json`.

**Results** (Regina 7.4.1, 2026-10-19, 8.1 CPU-hours):
- All triangulations of each manifold agree (9,741 rechecked), and the
  census lens-space names are pairwise distinct.
- Roots of the same parity are Galois conjugates, so they add nothing beyond
  w = 1; the data confirm it. The second parity at odd r does add
  information: H₁ + TV₃..₁₀ identifies 4,052 manifolds uniquely vs 4,006 at
  w = 1 alone (4,304 vs 4,273 classes).
- The parities differ only when H₁(M; Z₂) ≠ 0 (1,187 of 2,904 such
  manifolds; none of the other 2,075).
- 927 manifolds in 252 groups survive. 229 groups are only lens spaces,
  including 577 pairs that are not homotopy equivalent. 8 groups mix lens
  spaces with Seifert fibred spaces whose π₁ is infinite.
- Recommended set: H₁ + TV₄..₉, both parities (4,294 classes). TV₃ is
  redundant, and TV₁₀ adds 10 classes at the highest cost (median 1.0 s,
  maximum 182 s per manifold).

**Run.**
```sh
make e01 ARGS="--r-max 10"      # add --resume RUN_DIR to finish an interrupted run
make e01-export ARGS="results/e01_closed_census_invariants/<run>"
make writeups
```

**Next.** Understand exactly when the parities differ. Add invariants that
separate lens spaces (the linking form, torsion). Try TV₁₁ and TV₁₂ on the
survivors only.

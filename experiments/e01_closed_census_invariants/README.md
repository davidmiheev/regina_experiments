# E01 — How much do cheap invariants separate the closed census?

**Question.** Among the distinct closed orientable prime 3-manifolds in Regina's
census, how many are told apart by H₁, by Turaev–Viro invariants TV_r, and by
their combination — and which pairs survive everything?

**Why.** Calibrates which invariants are worth computing in later sweeps, and
exercises the whole pipeline (census iteration → invariants → JSONL → analysis).

**Method.** `run.py` iterates the `closed-or` census up to `--max-size`
tetrahedra and records H₁, Regina's simplified π₁ presentation (plus
`recogniseGroup()`), and `turaevViroApprox(r)` for r ∈ {3..7} at root 1.
`analyze.py` groups manifolds by each invariant.

**Sanity checks.** `analyze.py` verifies that all triangulations of the same
manifold give identical invariants. For lens spaces, L(p,q) ≅ L(p,q') iff
q' ≡ ±q^{±1} (mod p), so lens-space clashes can be checked against the
classification (and confirm the census names are pairwise distinct).

**Run.**
```sh
make e01 ARGS="--max-size 9" && make e01-analyze
```

**Preliminary results** (Regina 7.4.1, 2026-10-10, ≤ 9 tetrahedra, ~5 s):
4476 triangulations, 1901 manifolds. H₁ alone gives 272 classes; H₁ + TV_{3..7}
(root 1) gives 1384 classes, with 255 groups still unseparated. The largest
unseparated groups are lens spaces with the same p, e.g.
L(61,8) | L(61,9) | L(61,11) | ….

**Next.**
- Add the other roots (`whichRoot` coprime to 2r) and larger r; measure the gain.
- Run the full census (≤ 11 tetrahedra).
- For non-lens survivors, try π₁ (finite-quotient / abelian-cover counts) and,
  for hyperbolic ones, volume.

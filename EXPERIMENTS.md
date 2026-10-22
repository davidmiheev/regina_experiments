# Experiment roadmap

Ordered by what to start with: cheap experiments with known answers come
first, because they test both Regina and our tooling before we trust either on
open questions. Each experiment gets a directory under `experiments/` (copy
`_template/`). Its `README.md` holds the question, method, sanity checks and
results.

Status: ✅ done · 🟡 started · ⬜ not started

| ID  | Experiment | Status | Effort | Depends on |
|-----|------------|--------|--------|------------|
| E00 | Smoke test of every feature we rely on | ✅ | — | — |
| E01 | How well cheap invariants separate the closed census | ✅ | S | E00 |
| E02 | Regenerate the census with `tricensus` and diff it against the shipped data | ✅ | S | E00 |
| E03 | Scramble, then simplify: when does greedy simplification fail? | ⬜ | M | E00, E02 |
| E04 | Pachner-graph connectivity between minimal triangulations | ⬜ | M | E02 |
| E05 | Normal-surface statistics across the census | ⬜ | M | E01 |
| E06 | Cusped hyperbolic census: angle structures vs geometry | ⬜ | S | E00 |
| E07 | Knot census: how well polynomials and complements separate knots | ⬜ | S | E00 |
| E08 | Hard unknot diagrams: simplification vs recognition | ⬜ | M | E07 |
| E09 | 4-manifolds: small census, invariants, simplification | ⬜ | M | E02 |
| E10 | How Turaev–Viro runtime scales with treewidth | ⬜ | M | E01 |

**Suggested next:** E06 (quick, and it validates the tooling). Then E03 and E07, the first two that study algorithm
behaviour rather than reproduce known data.

---

## Tier 1: calibration (known answers, fast)

### E01 · How well cheap invariants separate the closed census ✅
*How many distinct closed orientable census manifolds can H₁ and TV_r tell
apart, and which groups survive all of them?*
- **Done:** the full ≤ 10-tetrahedron census (4,979 manifolds), with exact
  TV_r for r ≤ 10 at all roots. Writeup:
  `experiments/e01_closed_census_invariants/writeup.pdf`.
- **Headline:** H₁ + TV₃..₁₀ identifies 4,052 of 4,979 manifolds uniquely.
  Roots of the same parity add nothing (Galois conjugates). The second
  parity adds 46 manifolds, and differs from the first only when
  H₁(M; Z₂) ≠ 0. 252 groups survive: mostly lens spaces, including 577
  pairs that are not homotopy equivalent.
- **Follow-ups:** characterise when the parities differ; add lens-space
  invariants (the linking form, torsion); compute TV₁₁₊ on the survivors
  only.

### E02 · Regenerate the census with `tricensus` ✅
*Can we reproduce Regina's closed orientable census from scratch?*
- **Done** for n ≤ 10. Writeup:
  `experiments/e02_tricensus_regeneration/writeup.pdf`.
- **Headline:** the census is reproduced exactly (14,720 of 14,720). All
  51,719 other generated triangulations are certified non-minimal or
  non-prime. A single `simplify()` call fails on 2.7% of non-minimal
  10-tetrahedron triangulations, and on every one that needs exhaustive
  height ≥ 2.
- **Follow-ups:** cost-aware ordering of face pairings; bounded, ideal and
  4-D censuses with the same pipeline. The hard set
  (`data/e02/hard_nonminimal.tsv`) feeds E03.

### E06 · Cusped hyperbolic census: angle structures vs geometry ⬜
*For every triangulation in the cusped census (≤ 9 tetrahedra), does it admit a
strict angle structure, and does SnapPea find a geometric solution?*
- **Method:** call `AngleStructures(t).spansStrict()`, `spansTaut()` and
  `SnapPeaTriangulation(t).solutionType()` and `.volume()`.
  Cross-tabulate the results.
- **Sanity:** volumes must match the census names (m003 ≈ 2.0299, m004 ≈ 2.0299).
  Every closed-hyp label starts with its volume, so we can check those too.
- **Interesting output:** census triangulations that are geometric but have no
  strict angle structure, or the other way round. Also the distribution of
  volume against tetrahedra.

### E07 · Knot census: polynomials vs complements ⬜
*Over Regina's knot census (~60k prime knots and links), how many collisions
do Jones, HOMFLY-PT and Alexander have? Which collisions does the complement's
volume or census lookup resolve?*
- **Method:** call `Link.jones()`, `homfly()` and `alexander()` (knots only).
  Then call `complement()` and `SnapPeaTriangulation.volume()`. Group by each
  invariant, as `analyze.py` does in E01.
- **Sanity:** the mutant pair Kinoshita–Terasaka and Conway
  (`ExampleLink.kinoshitaTerasaka()` and `conway()`) must collide on HOMFLY-PT
  and on volume, since mutation preserves both. Record which Regina-native
  invariant, if any, separates them. No non-trivial knot in the table should have a trivial
  Jones polynomial.
- **Watch:** cost of HOMFLY as crossings grow. Regina chooses the algorithm via
  treewidth, so record `alg` and timings.

---

## Tier 2: algorithm behaviour (the actual experiments)

### E03 · Scramble, then simplify ⬜
*If we start from a minimal triangulation and apply k random Pachner moves,
how often does `simplify()` return to minimal size? When it fails, how much
height does `simplifyExhaustive(h)` need?*
- **Method:** for census manifolds (S³, lens spaces, Poincaré, Weeks, …),
  do k ∈ {10, 50, 200, 1000} random `pachner()` 2-3 moves and some 1-4 moves.
  Then run `simplify()` and record the final size, then escalate through
  `simplifyExhaustive(height=1..4)`. Also time `isSphere()` and `summands()`
  on the scrambled S³ and connected sums.
- **Output:** success rate against (k, manifold). Keep the "stuck"
  triangulations as a benchmark set in `data/`.
- **Why:** gives us hard instances and tests how robust the recognition
  pipelines are.

### E04 · Pachner-graph connectivity ⬜
*For each census manifold, are all its minimal triangulations connected by
2-3/3-2 moves that never go above n+1 (or n+2) tetrahedra?*
- **Method:** call `retriangulate(height, threads, action)` from one minimal
  triangulation and collect the isoSigs reached. Find the smallest height at
  which all census triangulations of that manifold appear.
- **Sanity:** this should agree with Burton's experiments on the Pachner
  graph of small closed census triangulations, where very little extra
  height was needed.
- **Output:** a per-manifold table of the height needed, flagging every
  manifold that needs more than +2.

### E05 · Normal-surface statistics ⬜
*How do the vertex and fundamental normal-surface counts grow across the
census in quad, standard and almost-normal (QuadOct) coordinates? How does
enumeration time scale?*
- **Method:** call `NormalSurfaces(t, NormalCoords.Quad / Standard / QuadOct,
  NormalList.Vertex | Fundamental)`, then `isZeroEfficient()`, `isHaken()`,
  and the counts of embedded spheres, tori and Klein bottles.
- **Sanity:** every census manifold with b₁ > 0 must be Haken. Spherical space
  forms (finite π₁) must not be Haken.
- **Output:** count distributions, the outliers, and timing curves for
  choosing coordinates in later algorithms.

### E08 · Hard unknot diagrams ⬜
*On diagrams of the unknot that are hard to simplify, how does
`Link.simplify()` compare with `simplifyExhaustive(h)` and with recognising
the solid torus via `complement().isSolidTorus()`?*
- **Inputs:** `ExampleLink.monster()`, `gordian()`, `cubicalUnknot()`, plus
  random diagrams made by applying many "up" moves (`r1`, `r2`, `r3`) to the
  unknot.
- **Output:** success rate and runtime against crossing number, and which
  diagrams beat greedy simplification.

### E10 · Turaev–Viro runtime vs treewidth ⬜
*How does the runtime of exact and approximate TV_r scale with r and with the
treewidth of the dual graph (Regina uses tree decompositions)?*
- **Method:** for census and scrambled (E03) triangulations, record
  `TreeDecomposition(t).width()` and the time for `turaevViro(r)` and
  `turaevViroApprox(r)`, across `Algorithm` choices.
- **Output:** fitted cost models, so we can budget large TV sweeps in E01.

---

## Tier 3: 4-manifolds and beyond

### E09 · Small 4-manifold census ⬜
*Reproduce a census of closed 4-manifold triangulations with few pentachora,
and study invariants and simplification there.*
- **Method:** run `tricensus --dim4 -t n -i -s` for n ≤ 4 (check the cost
  first). For each result record validity, orientability, χ, H₁, H₂ and the
  intersection form. Run `simplify()` and `simplifyUpDown()`.
- **Sanity:** the `Example4` menagerie (S⁴, CP², S²×S², K3 with rank 22,
  signature −16 and even form, Cappell–Shaneson) must give the known
  invariants. E00 already checks CP² and K3.
- **Why:** 4-D simplification has no termination guarantees, so its empirical
  behaviour is the interesting part.

### Later ideas (not yet scoped)
- Virtual knots (`virtual` census): how well the arrow polynomial, affine
  index and odd writhe separate them.
- Dehn fillings: walk the closed-hyp census labels (e.g. `m003(-3,1)`), refill
  with `SnapPeaTriangulation.fill()`, and check volumes and homology.
- Crushing and 0-efficiency: how many steps the crushing algorithm takes on
  scrambled connected sums from E03.

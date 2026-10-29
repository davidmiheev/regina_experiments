# E06 — Angle structures and geometry in the hyperbolic censuses ✅

**Full writeup:** [writeup.md](writeup.md) · [writeup.pdf](writeup.pdf)

**Question.** For every triangulation in Regina's cusped hyperbolic
censuses: does it admit a strict or taut angle structure, and does SnapPea
find a geometric solution? Do the closed hyperbolic census's volumes
reproduce, both directly and as the Dehn fillings named in its labels?

**Method.** `run.py` runs, on each cusped triangulation,
`hasStrictAngleStructure()` (LP), `AngleStructures` enumeration
(`spansStrict` / `spansTaut`), and SnapPea's solution type and volume.
Closed triangulations get 20 independent SnapPea constructions plus the
labelled Dehn filling, computed both as given and mirrored. A basis-change
search runs for the bases that fit neither convention. `analyze.py`
cross-tabulates and checks volumes; `figures.py` draws the charts.

**Results** (Regina 7.4.1, 2026-10-29, 37 s on 4 cores):
- **No triangulation is geometric without a strict angle structure**, as
  theory requires. LP and enumeration agree on all 13,853 triangulations.
- **97.8% are geometric, and every manifold's `#1` triangulation is.** Of
  the rest, 266 have a strict angle structure but no geometric solution, and
  34 have no strict angle structure. They are almost all one-cusped.
- **Volumes check out:** they are invariant across triangulations (to
  1.7e-14), in census order, and within the bound n·v_tet, with equality
  exactly for triangulations made of regular ideal tetrahedra.
- **SnapPea on a closed triangulation is random.** One attempt gives the
  correct volume 58% of the time, and 36% of triangulations never succeed
  in 20 attempts. A non-degenerate solution always has the correct volume.
- **The labelled Dehn fillings reproduce all 3,018 volumes**, once each
  base's orientation convention is applied: 278 bases need (p,q) → (−p,q),
  and 4 need another basis change.

**Run.** `make e06 && make e06-export ARGS=results/e06_hyperbolic_angle_structures/<run> && make writeups`

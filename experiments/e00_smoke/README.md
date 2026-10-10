# E00 — Smoke test

Known-answer checks for every Regina feature the later experiments rely on:
homology, π₁, 3-sphere recognition, connected-sum decomposition, census lookup,
SnapPea volumes, angle structures, normal surfaces, Turaev–Viro, link
polynomials and knot complements, and 4-manifold invariants (χ, intersection form).

```sh
make smoke
```

Exit status is non-zero if any check fails. CI runs it on every push.

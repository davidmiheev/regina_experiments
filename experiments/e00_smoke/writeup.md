---
title: "E00 — Smoke test"
subtitle: "Known-answer checks of every Regina feature the later experiments rely on"
author: "regina_experiments"
date: "2026-10-19"
---

## Summary

All 15 checks pass with Regina 7.4.1 (the official Ubuntu 24.04 package) under
Python 3.12.3. The whole suite runs in under a second. CI runs it on every push,
as part of `make test`.

## Purpose

Later experiments compute invariants in bulk and compare them across thousands
of triangulations. Before trusting those numbers, we check that each part of
Regina we depend on returns the right answer on a few inputs whose answer is
known independently. These checks also catch an environment problem early,
e.g. a Python interpreter that cannot import the `regina` module.

There are two kinds of check:

* **Mathematical facts.** The expected value comes from the literature and is
  independent of Regina.
* **Regression pins.** The expected value is Regina's own output, recorded so
  that an upgrade that changes it is noticed. These are marked *(pin)* below.

## Checks

| # | Check | Expected | Why it is right |
|--|------------------------|--------------|------------------------|
| 1 | $H_1(L(7,2))$ | $\mathbb{Z}_7$ | $\pi_1(L(p,q)) = \mathbb{Z}_p$ |
| 2 | $H_1$ of the Poincaré homology sphere | $0$ | homology sphere |
| 3 | `isSphere()` on a 3-sphere triangulation | true | — |
| 4 | `isSphere()` on the Poincaré sphere | false | $\lvert\pi_1\rvert = 120$ |
| 5 | summands of $\mathbb{RP}^3 \# \mathbb{RP}^3$ | 2 | prime decomposition |
| 6 | census lookup of the figure-eight complement | `m004` | SnapPea cusped census |
| 7 | volume of the figure-eight complement | $2.0298832128\ldots$ | two regular ideal tetrahedra, $6\,\Lambda(\pi/3)$ |
| 8 | volume of the Weeks manifold | $0.9427073627\ldots$ | smallest closed hyperbolic 3-manifold (Gabai–Meyerhoff–Milley) |
| 9 | figure-eight complement has a strict angle structure | true | all angles $\pi/3$ |
| 10 | vertex normal surfaces of the figure-eight complement (quad coords) | 4 | *(pin)* |
| 11 | $TV_5(S^3) \ne TV_5(L(5,1))$ | distinct | *(pin; the values are Regina's normalisation)* |
| 12 | Jones polynomial of the right-handed trefoil | $-x^8 + x^6 + x^2$ | $x = \sqrt{t}$, i.e. $t + t^3 - t^4$; sources differ by the mirror $t \mapsto t^{-1}$ |
| 13 | complement of the figure-eight knot (from a diagram) | `m004` | as check 6, via `Link.complement()` |
| 14 | $\chi(\mathbb{CP}^2)$ | 3 | $1 + 1 + 1$ |
| 15 | intersection form of K3 | rank 22, signature $-16$, even | $2(-E_8) \oplus 3H$ |

The volumes in checks 7–8 must match to $10^{-8}$. Every other check is an
exact comparison.

## Results

Output of the run on 2026-10-19 (git `b62487a`, 4-core cloud container):

```
Regina 7.4.1  (Python 3.12.3)
  [PASS] H1(L(7,2)) = Z_7                                   0.2 ms  Z_7
  [PASS] H1(Poincare) = 0                                   0.1 ms  0
  [PASS] S3 recognised                                      0.1 ms  True
  [PASS] Poincare is not S3                                12.1 ms  False
  [PASS] RP3 # RP3 has 2 summands                           0.6 ms  2
  [PASS] census lookup: figure-eight = m004                 2.1 ms  ['m004 : #1', 'L104001']
  [PASS] vol(figure-eight) ~ 2.029883                       0.1 ms  2.029883212819307
  [PASS] vol(Weeks) ~ 0.942707                              0.2 ms  0.9427073627769281
  [PASS] fig-8 has strict angle structure                   0.1 ms  True
  [PASS] fig-8: 4 vertex quad normal surfaces               0.1 ms  4
  [PASS] TV_5 distinguishes S3 from L(5,1)                  1.1 ms  ('1/10 x^3 - 1/10 x^2 + 1/5', '1/2')
  [PASS] Jones(right trefoil)                               0.1 ms  -x^8 + x^6 + x^2
  [PASS] fig-8 knot complement = m004                       1.9 ms  ['m004 : #1', 'L104001']
  [PASS] chi(CP2) = 3                                       0.2 ms  3
  [PASS] K3 intersection form: rank 22, sig -16, even     143.0 ms  (22, -16, True)
OK
```

The census lookup in checks 6 and 13 returns two hits, `m004` from the cusped
hyperbolic census and `L104001` from the link census. Both name the
figure-eight knot complement.

## Environment notes

* The apt package builds `regina` for the distribution's system Python (3.12
  on Ubuntu 24.04). In this container `python3` was 3.13 and could not import
  it. `scripts/find-python.sh` finds a working interpreter, and the Makefile
  uses it.
* Regina's `jones()` returns a Laurent polynomial in $x = \sqrt{t}$ (check 12).
  Keep this in mind when comparing with tables written in $t$.

## Reproduce

```sh
scripts/install-regina-ubuntu.sh
make smoke        # or: make test (unit tests + smoke)
```

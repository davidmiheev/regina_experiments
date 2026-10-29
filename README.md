# regina_experiments

Computational experiments in low-dimensional topology with
[Regina](https://regina-normal.github.io), driven from its Python bindings.

The roadmap is in **[EXPERIMENTS.md](EXPERIMENTS.md)**. Each finished
experiment has a writeup in Markdown and PDF:

| | writeup |
|---|---|
| E00 smoke test | [md](experiments/e00_smoke/writeup.md) · [pdf](experiments/e00_smoke/writeup.pdf) |
| E01 Turaev–Viro invariants on the closed census | [md](experiments/e01_closed_census_invariants/writeup.md) · [pdf](experiments/e01_closed_census_invariants/writeup.pdf) |
| E02 Regenerating the closed census with tricensus | [md](experiments/e02_tricensus_regeneration/writeup.md) · [pdf](experiments/e02_tricensus_regeneration/writeup.pdf) |
| E06 Angle structures and geometry in the hyperbolic censuses | [md](experiments/e06_hyperbolic_angle_structures/writeup.md) · [pdf](experiments/e06_hyperbolic_angle_structures/writeup.pdf) |

## Setup (Ubuntu 24.04 / 25.04 / 25.10)

```sh
make install     # = scripts/install-regina-ubuntu.sh (uses sudo when not root)
make env         # shows the Python interpreter and Regina version in use
make test        # unit tests + E00 smoke test
```

The install script follows the
[official instructions](https://regina-normal.github.io/install/ubuntu.html).
It installs `debian-keyring`, adds `regina-<codename>.sources` under
`/etc/apt/sources.list.d/`, and runs `apt-get install regina-normal`. Pass
`--with-doc` or `--with-dev` to add the docs or the C++ headers.

**Python version caveat.** The apt package builds its `regina` module for the
distro's system Python (3.12 on noble), under `/usr/lib/python3/dist-packages`.
If `python3` points somewhere else (pyenv, update-alternatives, conda), then
`import regina` fails. `scripts/find-python.sh` finds an interpreter that
works, and the Makefile uses it automatically. To use a venv, create it from
that interpreter with `--system-site-packages`. Regina also ships
`regina-python`, a wrapper that pre-imports the module.

## Layout

```
EXPERIMENTS.md            roadmap: what we run, in what order, and why
experiments/
  _template/              copy to start a new experiment (run.py + README.md)
  e00_smoke/              known-answer checks of every Regina feature we use
  e01_closed_census_invariants/   run.py, analyze.py, figures.py, writeup.{md,pdf}
  e02_tricensus_regeneration/     run.py, retry.py, analyze.py, figures.py, writeup.{md,pdf}
  e06_hyperbolic_angle_structures/ run.py, analyze.py, figures.py, writeup.{md,pdf}
src/rexp/                 shared helpers (on PYTHONPATH via the Makefile)
  census.py               iter_census("closed-or" | "cusped-hyp-or" | "knots" | ...)
  runlog.py               Run(...) context manager and timed()
tests/                    unittest suite for rexp + smoke
scripts/                  install, interpreter discovery, writeup build
docs/writeup.css          print stylesheet for the PDF writeups
data/                     curated outputs worth committing (e.g. data/e01/)
results/                  run outputs (git-ignored)
```

Each run writes `results/<experiment>/<UTC timestamp>/` containing:
- `meta.json`: Regina version, git sha, parameters, wall time and status.
- `records.jsonl`: one JSON object per triangulation or link.

Results are reproducible from code, so they are not committed. Copy curated
tables into `data/` when they are worth keeping.

## Writeups

```sh
make install-writeup-deps   # pandoc + matplotlib (Chromium must already be present)
make writeups               # experiments/*/writeup.md -> writeup.pdf
```

`scripts/build-writeup.sh` uses pandoc to turn the Markdown into HTML (math
as MathML, figures embedded). Headless Chromium then prints the HTML to A4
PDF.

## Bundled census data

`iter_census()` reads the census files that ship with `regina-normal`, from
`/usr/share/regina-normal/examples`:

| name | contents | objects |
|------|----------|--------:|
| `closed-or` | closed orientable prime minimal, ≤ 10 tet (4,979 manifolds) | 14,720 |
| `closed-nor` | closed non-orientable P²-irreducible minimal | 4,672 |
| `closed-hyp` | Hodgson–Weeks closed hyperbolic (3,000 orientable + 18 non-orientable) | 3,018 |
| `cusped-hyp-or` | cusped hyperbolic orientable, ≤ 7 tet (4,815 manifolds) | 9,596 |
| `cusped-hyp-nor` | cusped hyperbolic non-orientable, ≤ 7 tet (1,259 manifolds) | 4,257 |
| `knots` | prime knots and links | 59,937 |
| `virtual` | virtual knots (Green) | 92,798 |

## Cloud sessions

`.claude/settings.json` has a SessionStart hook that runs the install script
in Claude Code cloud sessions. The script exits immediately if Regina is
already installed. CI (`.github/workflows/ci.yml`) installs Regina on
`ubuntu-24.04` and runs `make test`.

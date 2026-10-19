# Notes for Claude

- Run Python through `make` targets or `$(scripts/find-python.sh)`: the apt
  `regina` module only imports under the distro's system Python (3.12 on noble),
  and the default `python3` may be a different version.
- Experiments live in `experiments/eXX_<slug>/` (copy `_template/`); log every run
  with `rexp.Run` so `meta.json` records Regina version, git sha and params.
- Keep `EXPERIMENTS.md` status markers and each experiment's README "Results"
  section up to date when a run finishes.
- Every experiment with results gets `writeup.md` plus the rendered
  `writeup.pdf` (`make writeups`; needs pandoc, matplotlib and Chromium). Put
  figures in `experiments/<exp>/figures/`. Draw them from curated data in
  `data/<exp>/`, not from `results/`, which is git-ignored.
- Long runs: use `rexp.Run(..., resume=run_dir)` / `--resume`, so a killed
  run can be finished instead of restarted.
- `make test` must pass before pushing.

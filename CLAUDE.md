# Notes for Claude

- Run Python through `make` targets or `$(scripts/find-python.sh)`: the apt
  `regina` module only imports under the distro's system Python (3.12 on noble),
  and the default `python3` may be a different version.
- Experiments live in `experiments/eXX_<slug>/` (copy `_template/`); log every run
  with `rexp.Run` so `meta.json` records Regina version, git sha and params.
- Keep `EXPERIMENTS.md` status markers and each experiment's README "Results"
  section up to date when a run finishes.
- `make test` must pass before pushing.

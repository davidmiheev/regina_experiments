# EXX — <title>

**Question.** What do we want to know, stated so the answer is yes/no or a number.

**Why.** What it unblocks or what would be surprising.

**Method.** Inputs (census / generator, size range), Regina calls, parameters.

**Ground truth / sanity checks.** Known results the output must reproduce.

**Run.**
```sh
make env
PYTHONPATH=src python3 experiments/eXX_<slug>/run.py --max-size 6
```

**Results.** Date, run directory, git sha (from `meta.json`), headline numbers.

**Next.**

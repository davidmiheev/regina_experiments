# Common entry points. `make help` lists them.
PY := $(shell scripts/find-python.sh 2>/dev/null || echo python3)
export PYTHONPATH := $(CURDIR)/src
ARGS ?=

.PHONY: help install engine install-writeup-deps env smoke test e01 e01-analyze e01-export e02 e02-retry e02-export e06 e06-export writeups clean-results

help:
	@echo "make install       install Regina from the official Ubuntu apt repo (needs sudo)"
	@echo "make engine        set up the mtengine submodule and its venv (MCP server in .mcp.json)"
	@echo "make install-writeup-deps  pandoc + matplotlib for figures and PDFs"
	@echo "make env           show which Python/Regina will be used"
	@echo "make smoke         E00: quick known-answer checks of the Regina features we use"
	@echo "make test          unit tests for the rexp helper package + smoke"
	@echo "make e01 ARGS=...  E01: closed-census invariant sweep (e.g. ARGS='--max-size 8')"
	@echo "make e01-analyze   summarise the latest E01 run"
	@echo "make e01-export    copy the latest E01 summary to data/e01 and redraw its figures"
	@echo "make e02 ARGS=...  E02: regenerate the closed census with tricensus (ARGS='--max-n 10')"
	@echo "make e02-retry ARGS=RUN_DIR  E02b: simplify() reliability on E02's non-minimal triangulations"
	@echo "make e02-export ARGS=RUN_DIR copy the E02 summary to data/e02 and redraw its figures"
	@echo "make e06           E06: angle structures vs SnapPea on the hyperbolic censuses"
	@echo "make e06-export ARGS=RUN_DIR copy the E06 summary to data/e06 and redraw its figures"
	@echo "make writeups      render experiments/*/writeup.md to writeup.pdf"
	@echo "make clean-results delete everything under results/"

install:
	scripts/install-regina-ubuntu.sh

engine:
	git submodule update --init engine
	cd engine && python3 -m venv .venv && .venv/bin/pip install -q -e .
	engine/.venv/bin/mte versions

install-writeup-deps:
	scripts/install-writeup-deps.sh

env:
	@echo "python: $(PY)"
	@$(PY) -c 'import sys, regina; print("python", sys.version.split()[0]); print("regina", regina.versionString())'

smoke:
	$(PY) experiments/e00_smoke/run.py

test:
	$(PY) -m unittest discover -s tests -v

e01:
	$(PY) experiments/e01_closed_census_invariants/run.py $(ARGS)

e01-analyze:
	$(PY) experiments/e01_closed_census_invariants/analyze.py $(ARGS)

e01-export:
	$(PY) experiments/e01_closed_census_invariants/analyze.py $(ARGS) --export data/e01
	$(PY) experiments/e01_closed_census_invariants/figures.py

e02:
	$(PY) experiments/e02_tricensus_regeneration/run.py $(ARGS)

e02-retry:
	$(PY) experiments/e02_tricensus_regeneration/retry.py --trials 50 $(ARGS)

e02-export:
	$(PY) experiments/e02_tricensus_regeneration/analyze.py $(ARGS) --export data/e02
	$(PY) experiments/e02_tricensus_regeneration/figures.py

e06:
	$(PY) experiments/e06_hyperbolic_angle_structures/run.py $(ARGS)

e06-export:
	$(PY) experiments/e06_hyperbolic_angle_structures/analyze.py $(ARGS) --export data/e06
	$(PY) experiments/e06_hyperbolic_angle_structures/figures.py

writeups:
	scripts/build-writeup.sh $(dir $(wildcard experiments/e*/writeup.md))

clean-results:
	find results -mindepth 1 ! -name .gitkeep -exec rm -rf {} +

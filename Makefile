# Common entry points. `make help` lists them.
PY := $(shell scripts/find-python.sh 2>/dev/null || echo python3)
export PYTHONPATH := $(CURDIR)/src
ARGS ?=

.PHONY: help install install-writeup-deps env smoke test e01 e01-analyze e01-export writeups clean-results

help:
	@echo "make install       install Regina from the official Ubuntu apt repo (needs sudo)"
	@echo "make install-writeup-deps  pandoc + matplotlib for figures and PDFs"
	@echo "make env           show which Python/Regina will be used"
	@echo "make smoke         E00: quick known-answer checks of the Regina features we use"
	@echo "make test          unit tests for the rexp helper package + smoke"
	@echo "make e01 ARGS=...  E01: closed-census invariant sweep (e.g. ARGS='--max-size 8')"
	@echo "make e01-analyze   summarise the latest E01 run"
	@echo "make e01-export    copy the latest E01 summary to data/e01 and redraw its figures"
	@echo "make writeups      render experiments/*/writeup.md to writeup.pdf"
	@echo "make clean-results delete everything under results/"

install:
	scripts/install-regina-ubuntu.sh

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

writeups:
	scripts/build-writeup.sh $(dir $(wildcard experiments/e*/writeup.md))

clean-results:
	find results -mindepth 1 ! -name .gitkeep -exec rm -rf {} +

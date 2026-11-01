# Run inside the iic-osic container, e.g.
#   docker exec -w /foss/projects/synchronous-buck-converter- iic-osic bash -lc 'make all'
PY ?= python3
RTL = rtl/therm2bin.v rtl/buck_ctrl_top.v

.PHONY: all env model test-model lint formal tb tb-quick phase2 docs
all: model test-model lint formal tb phase2 docs

env:
	scripts/env_check.sh | tee results/env_check.txt

# ---- Phase 1: models
model:
	MPLBACKEND=Agg $(PY) -m model.phase1

test-model:
	$(PY) -m pytest model/tests -q

# ---- Phase 2: controller RTL
lint:
	mkdir -p results/phase2
	verilator --lint-only -Wall $(RTL) --top-module buck_ctrl_top 2>&1 | tee results/phase2/lint.txt

formal:
	cd formal && sby -f buck_ctrl.sby

tb:
	$(MAKE) -C tb

tb-quick:
	$(MAKE) -C tb QUICK=1

phase2:
	$(PY) scripts/collect_phase2.py

docs:
	$(PY) scripts/update_docs.py

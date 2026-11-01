# Run inside the iic-osic container, e.g.
#   docker exec -w /foss/projects/synchronous-buck-converter- iic-osic bash -lc 'make model'
PY ?= python3

.PHONY: all env model test-model docs
all: model test-model docs

env:
	scripts/env_check.sh | tee results/env_check.txt

model:
	MPLBACKEND=Agg $(PY) -m model.phase1

test-model:
	$(PY) -m pytest model/tests -q

docs:
	$(PY) scripts/update_docs.py

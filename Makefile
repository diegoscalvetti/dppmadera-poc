PY ?= python3
export PYTHONPATH := src

.PHONY: install data openapi test serve replay clean

install:
	$(PY) -m pip install -e ".[dev]"

data:            ## regenerate the synthetic dataset (seeded, reproducible)
	$(PY) -m dppmadera.generator

openapi:         ## export the OpenAPI 3 spec to docs/openapi.json
	$(PY) scripts/export_openapi.py

test:
	$(PY) -m pytest -q

serve:           ## run all services locally on http://127.0.0.1:8000 (docs at /docs)
	$(PY) -m uvicorn dppmadera.app:app --reload

replay:          ## end-to-end replay, then T1-T11, results table and figures
	$(PY) scripts/replay.py
	$(PY) -m pytest -q --junitxml=results/junit.xml
	$(PY) scripts/results_table.py
	$(PY) scripts/figures.py

clean:
	rm -rf var results .pytest_cache

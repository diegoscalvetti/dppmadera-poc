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

replay:          ## end-to-end replay, results and figures (milestone PR 2)
	$(PY) scripts/replay.py

clean:
	rm -rf var results .pytest_cache

PY ?= python3
export PYTHONPATH := src

.PHONY: install data openapi test serve demo replay site clean

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

demo:            ## replay the building into a running server and open the assembly-state view
	DPPMADERA_PRELOAD=1 $(PY) -m uvicorn dppmadera.app:app

replay:          ## end-to-end replay, then T1-T11, results table and figures
	$(PY) scripts/replay.py
	$(PY) -m pytest -q --junitxml=results/junit.xml
	$(PY) scripts/results_table.py
	$(PY) scripts/figures.py

site:            ## rebuild the static website parts generated from the PoC (site/twin, site/figures)
	$(PY) scripts/build_site_twin.py
	cp docs/figures/architecture.png docs/figures/assembly_state.png docs/figures/assembly_state_view.png site/figures/

clean:
	rm -rf var results .pytest_cache

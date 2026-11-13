"""Mounts the domain routers in one local process. Each router keeps its own store."""

from fastapi import FastAPI

from . import __version__
import os

from .services import conflicts, dbl, dpp, dtw, epm, federation, resolver, view

app = FastAPI(
    title="DPP Madera PoC",
    version=__version__,
    description="Federated DPP, EPM, DBL and minimal DTw for one synthetic CLT building. Synthetic data only.",
)
for module in (dpp, epm, dbl, resolver, dtw, federation, conflicts, view):
    app.include_router(module.router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok", "version": __version__}


@app.on_event("startup")
def _preload() -> None:
    """With DPPMADERA_PRELOAD=1 (make demo), replay the synthetic building into this process at start-up."""
    if os.environ.get("DPPMADERA_PRELOAD") == "1":
        from .replay import load, run

        run()
        bid = load()["ground_truth"]["building_id"]
        print(f"\nAssembly-state view: http://127.0.0.1:8000/view?building_id={bid}\nAPI docs: http://127.0.0.1:8000/docs\n")

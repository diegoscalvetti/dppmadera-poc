"""Mounts the domain routers in one local process. Each router keeps its own store."""

from fastapi import FastAPI

from . import __version__
from .services import conflicts, dbl, dpp, dtw, epm, federation, resolver

app = FastAPI(
    title="DPP Madera PoC",
    version=__version__,
    description="Federated DPP, EPM, DBL and minimal DTw for one synthetic CLT building. Synthetic data only.",
)
for module in (dpp, epm, dbl, resolver, dtw, federation, conflicts):
    app.include_router(module.router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok", "version": __version__}

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import routes_files, routes_graph, routes_validation
from .graph.neo4j_client import close_driver, ensure_constraints

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api-gateway")

app = FastAPI(title="SCL Explorer API Gateway", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_files.router)
app.include_router(routes_validation.router)
app.include_router(routes_graph.router)


@app.on_event("startup")
def on_startup() -> None:
    try:
        ensure_constraints()
    except Exception as exc:  # pragma: no cover - startup resilience, logged not raised
        logger.warning("Neo4j not reachable at startup, constraints not applied yet: %s", exc)


@app.on_event("shutdown")
def on_shutdown() -> None:
    close_driver()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

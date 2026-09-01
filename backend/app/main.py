"""Magi FastAPI application."""

from fastapi import FastAPI

from app.api.v1.router import router
from app.divination import engines as _engines  # noqa: F401

app = FastAPI(title="Magi API")
app.include_router(router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}

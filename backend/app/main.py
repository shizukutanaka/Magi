"""Magi FastAPI application."""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import router
from app.divination import engines as _engines  # noqa: F401

app = FastAPI(title="Magi API")
app.include_router(router, prefix="/api/v1")


def mount_frontend(application: FastAPI) -> None:
    static_dir = Path(os.getenv("MAGI_STATIC_DIR") or Path(__file__).resolve().parents[2] / "frontend")
    if static_dir.is_dir():
        application.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")


@app.get("/health")
def health():
    return {"status": "ok"}


mount_frontend(app)

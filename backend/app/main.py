"""Magi FastAPI application."""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
from starlette.types import Scope

from app.api.v1.router import router
from app.divination import engines as _engines  # noqa: F401

app = FastAPI(title="Magi API")
app.include_router(router, prefix="/api/v1")


class NoCacheStaticFiles(StaticFiles):
    """ETag/Last-Modified での再検証を必ず行わせる静的配信。"""

    def file_response(
        self,
        full_path: str | os.PathLike[str],
        stat_result: os.stat_result,
        scope: Scope,
        status_code: int = 200,
    ) -> Response:
        response = super().file_response(full_path, stat_result, scope, status_code)
        response.headers["Cache-Control"] = "no-cache"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response


def mount_frontend(application: FastAPI) -> None:
    static_dir = Path(os.getenv("MAGI_STATIC_DIR") or Path(__file__).resolve().parents[2] / "frontend")
    if static_dir.is_dir():
        application.mount("/", NoCacheStaticFiles(directory=static_dir, html=True), name="frontend")


@app.get("/health")
def health():
    return {"status": "ok"}


mount_frontend(app)

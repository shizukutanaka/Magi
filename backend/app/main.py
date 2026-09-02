"""Magi FastAPI application."""

import os
from collections.abc import Awaitable, Callable
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
from starlette.types import Scope

from app.api.v1.router import router
from app.divination import engines as _engines  # noqa: F401

CONTENT_SECURITY_POLICY = (
    "default-src 'self'; base-uri 'none'; object-src 'none'; "
    "frame-ancestors 'none'; form-action 'self'; img-src 'self' data:; "
    "script-src 'self'; style-src 'self'; connect-src 'self'"
)
SECURITY_HEADERS: dict[str, str] = {
    "Content-Security-Policy": CONTENT_SECURITY_POLICY,
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
}

app = FastAPI(title="Magi API", docs_url=None, redoc_url=None)
app.include_router(router, prefix="/api/v1")


@app.middleware("http")
async def add_security_headers(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    response = await call_next(request)
    for name, value in SECURITY_HEADERS.items():
        response.headers.setdefault(name, value)
    return response


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
        return response


def mount_frontend(application: FastAPI) -> None:
    static_dir = Path(os.getenv("MAGI_STATIC_DIR") or Path(__file__).resolve().parents[2] / "frontend")
    if static_dir.is_dir():
        application.mount("/", NoCacheStaticFiles(directory=static_dir, html=True), name="frontend")


@app.get("/health")
def health():
    return {"status": "ok"}


mount_frontend(app)

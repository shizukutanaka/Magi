"""Magi FastAPI application."""

import logging
import os
from collections.abc import Awaitable, Callable
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
from starlette.types import Scope

from app.api.v1.router import router
from app.core.config import (
    ConfigError,
    get_rate_limit_per_minute,
    get_trust_proxy_headers,
    validate_environment,
)
from app.divination import engines as _engines  # noqa: F401

logger = logging.getLogger(__name__)
DEFAULT_STATIC_DIR = Path(__file__).resolve().parents[2] / "frontend"

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
    configured_dir = os.getenv("MAGI_STATIC_DIR")
    configured_dir = configured_dir.strip() if configured_dir is not None else None
    if configured_dir:
        static_dir = Path(configured_dir).expanduser().resolve()
        if not static_dir.is_dir():
            raise ConfigError(f"MAGI_STATIC_DIR で指定されたディレクトリが存在しません: {static_dir}")
        will_mount = True
    else:
        static_dir = DEFAULT_STATIC_DIR
        will_mount = static_dir.is_dir()

    logger.info(
        "Magi configuration: rate_limit_per_minute=%d, trust_proxy_headers=%s, static_dir=%s (%s)",
        get_rate_limit_per_minute(),
        get_trust_proxy_headers(),
        static_dir,
        "mounted" if will_mount else "api-only",
    )
    if not will_mount:
        logger.warning(
            "フロントエンドディレクトリ %s が見つからないため、API-onlyで起動します",
            static_dir,
        )
        return

    application.mount("/", NoCacheStaticFiles(directory=static_dir, html=True), name="frontend")


@app.get("/health")
def health():
    return {"status": "ok"}


validate_environment()
mount_frontend(app)

"""Small in-memory fixed-window rate limiter for abuse prevention."""

import math
import time
from collections.abc import Callable
from threading import Lock

from fastapi import HTTPException, Request

from app.core.config import get_rate_limit_per_minute


class RateLimitExceeded(Exception):  # noqa: N818
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"rate limit exceeded; retry after {retry_after} seconds")


class RateLimiter:
    def __init__(self, limit: int, window_seconds: int, clock: Callable[[], float] = time.monotonic):
        self.limit = limit
        self.window_seconds = window_seconds
        self.clock = clock
        self._windows: dict[str, tuple[float, int]] = {}
        self._lock = Lock()

    def check(self, key: str) -> None:
        if self.limit <= 0:
            return
        now = self.clock()
        with self._lock:
            expired = [
                stored_key
                for stored_key, (started_at, _) in self._windows.items()
                if now - started_at >= self.window_seconds
            ]
            for stored_key in expired:
                del self._windows[stored_key]

            started_at, count = self._windows.get(key, (now, 0))
            if now - started_at >= self.window_seconds:
                started_at, count = now, 0
            if count >= self.limit:
                retry_after = max(1, math.ceil(self.window_seconds - (now - started_at)))
                raise RateLimitExceeded(retry_after=retry_after)
            self._windows[key] = (started_at, count + 1)


rate_limiter = RateLimiter(limit=get_rate_limit_per_minute(), window_seconds=60)


def rate_limit(request: Request) -> None:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        client_key = forwarded_for.split(",", 1)[0].strip()
    else:
        client_key = request.client.host if request.client else "unknown"
    try:
        rate_limiter.check(client_key)
    except RateLimitExceeded as exc:
        raise HTTPException(
            status_code=429,
            detail="リクエスト数の上限に達しました。しばらく待ってから再試行してください。",
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc

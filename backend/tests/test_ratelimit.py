import pytest

from app.core.ratelimit import RateLimiter, RateLimitExceeded


def test_requests_up_to_limit_are_allowed():
    now = [0.0]
    limiter = RateLimiter(limit=2, window_seconds=60, clock=lambda: now[0])
    limiter.check("192.0.2.1")
    limiter.check("192.0.2.1")


def test_exceeding_limit_reports_retry_after():
    now = [0.0]
    limiter = RateLimiter(limit=2, window_seconds=60, clock=lambda: now[0])
    limiter.check("192.0.2.1")
    limiter.check("192.0.2.1")
    with pytest.raises(RateLimitExceeded) as exc_info:
        limiter.check("192.0.2.1")
    assert exc_info.value.retry_after == 60


def test_window_expiration_restores_access():
    now = [0.0]
    limiter = RateLimiter(limit=1, window_seconds=60, clock=lambda: now[0])
    limiter.check("192.0.2.1")
    now[0] = 60.0
    limiter.check("192.0.2.1")


def test_different_keys_have_independent_windows():
    limiter = RateLimiter(limit=1, window_seconds=60, clock=lambda: 0.0)
    limiter.check("192.0.2.1")
    limiter.check("192.0.2.2")

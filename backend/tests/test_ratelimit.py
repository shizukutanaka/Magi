import pytest
from fastapi.testclient import TestClient

import app.core.ratelimit as ratelimit_module
from app.core.ratelimit import RateLimiter, RateLimitExceeded
from app.i18n import t
from app.main import app

client = TestClient(app)
PAYLOAD = {"engine_id": "tarot", "input": {"target_date": "2026-01-01"}}


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


@pytest.fixture
def single_request_limit(monkeypatch):
    monkeypatch.setattr(
        ratelimit_module,
        "rate_limiter",
        RateLimiter(limit=1, window_seconds=60, clock=lambda: 0),
    )


def test_forwarded_for_is_ignored_by_default(monkeypatch, single_request_limit):
    monkeypatch.delenv("MAGI_TRUST_PROXY", raising=False)
    first = client.post("/api/v1/readings", json=PAYLOAD, headers={"X-Forwarded-For": "198.51.100.1"})
    second = client.post("/api/v1/readings", json=PAYLOAD, headers={"X-Forwarded-For": "198.51.100.2"})
    assert first.status_code == 200
    assert second.status_code == 429


def test_forwarded_for_is_used_when_proxies_are_trusted(monkeypatch, single_request_limit):
    monkeypatch.setenv("MAGI_TRUST_PROXY", "1")
    first = client.post("/api/v1/readings", json=PAYLOAD, headers={"X-Forwarded-For": "198.51.100.1"})
    second = client.post("/api/v1/readings", json=PAYLOAD, headers={"X-Forwarded-For": "198.51.100.2"})
    assert first.status_code == second.status_code == 200


def test_rate_limited_detail_is_localized(monkeypatch, single_request_limit):
    monkeypatch.delenv("MAGI_TRUST_PROXY", raising=False)
    assert client.post("/api/v1/readings", json=PAYLOAD).status_code == 200
    japanese = client.post("/api/v1/readings", json=PAYLOAD)
    english = client.post("/api/v1/readings", json=PAYLOAD, headers={"Accept-Language": "en"})
    assert japanese.status_code == english.status_code == 429
    assert japanese.json()["detail"] == t("ja", "error.rate_limited")
    assert english.json()["detail"] == t("en", "error.rate_limited")
    assert japanese.headers["Retry-After"] == english.headers["Retry-After"] == "60"

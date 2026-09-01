from fastapi.testclient import TestClient

from app.core.ratelimit import RateLimiter
from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_systems_are_all_unconditionally_available():
    response = client.get("/api/v1/systems")
    assert response.status_code == 200
    systems = response.json()
    assert len(systems) == 8
    assert {item["id"] for item in systems} == {
        "tarot",
        "iching",
        "runes",
        "omikuji",
        "astrology",
        "numerology",
        "bazi",
        "mayan",
    }
    assert all(set(item) == {"id", "name", "tradition", "required_fields"} for item in systems)


def test_reading_success():
    response = client.post("/api/v1/readings", json={"engine_id": "tarot", "input": {"target_date": "2026-01-01"}})
    assert response.status_code == 200
    assert response.json()["engine_id"] == "tarot"


def test_celtic_cross_is_available():
    response = client.post(
        "/api/v1/readings",
        json={
            "engine_id": "tarot",
            "input": {"target_date": "2026-01-01", "options": {"spread": "celtic-cross"}},
        },
    )
    assert response.status_code == 200
    assert len(response.json()["drawn"]) == 10


def test_unknown_spread_is_unprocessable():
    response = client.post(
        "/api/v1/readings",
        json={
            "engine_id": "tarot",
            "input": {"target_date": "2026-01-01", "options": {"spread": "unknown"}},
        },
    )
    assert response.status_code == 422


def test_reading_unknown_engine():
    response = client.post("/api/v1/readings", json={"engine_id": "unknown", "input": {"target_date": "2026-01-01"}})
    assert response.status_code == 404


def test_reading_required_input_missing():
    response = client.post(
        "/api/v1/readings",
        json={"engine_id": "astrology", "input": {"target_date": "2026-01-01"}},
    )
    assert response.status_code == 422


def test_daily_returns_three_distinct_traditions():
    response = client.post("/api/v1/readings/daily", json={"target_date": "2026-01-01", "subject_key": "daily"})
    assert response.status_code == 200
    readings = response.json()["readings"]
    assert len(readings) == 3
    assert len({reading["tradition"] for reading in readings}) == 3
    assert "upgrade_required" not in response.json()


def test_rate_limit_returns_429_and_retry_after(monkeypatch):
    import app.core.ratelimit as ratelimit_module

    monkeypatch.setattr(ratelimit_module, "rate_limiter", RateLimiter(limit=1, window_seconds=60, clock=lambda: 0))
    payload = {"engine_id": "tarot", "input": {"target_date": "2026-01-01"}}
    assert client.post("/api/v1/readings", json=payload).status_code == 200
    response = client.post("/api/v1/readings", json=payload)
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"

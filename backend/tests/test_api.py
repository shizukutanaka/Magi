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
    assert len(systems) == 9
    assert {item["id"] for item in systems} == {
        "tarot",
        "iching",
        "runes",
        "omikuji",
        "astrology",
        "numerology",
        "bazi",
        "mayan",
        "geomancy",
    }
    assert all(set(item) == {"id", "name", "tradition", "required_fields"} for item in systems)


def test_reading_success():
    response = client.post("/api/v1/readings", json={"engine_id": "tarot", "input": {"target_date": "2026-01-01"}})
    assert response.status_code == 200
    assert response.json()["engine_id"] == "tarot"


def test_implicit_and_explicit_default_tarot_spread_match():
    base = {"engine_id": "tarot", "input": {"target_date": "2026-01-01"}, "subject_key": "same"}
    implicit = client.post("/api/v1/readings", json=base)
    explicit = client.post(
        "/api/v1/readings",
        json={
            **base,
            "input": {"target_date": "2026-01-01", "options": {"spread": "three-card"}},
        },
    )
    assert implicit.status_code == explicit.status_code == 200
    assert implicit.json()["seed"] == explicit.json()["seed"]
    assert implicit.json()["drawn"] == explicit.json()["drawn"]


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


def test_daily_readings_match_single_readings():
    payload = {
        "target_date": "2026-01-01",
        "question": "今日の問い",
        "birth_date": "1990-01-02",
        "full_name": "山田太郎",
        "subject_key": "repro",
    }
    daily = client.post("/api/v1/readings/daily", json=payload)
    assert daily.status_code == 200
    input_data = {
        "target_date": payload["target_date"],
        "question": payload["question"],
        "birth_date": payload["birth_date"],
        "full_name": payload["full_name"],
        "options": {},
    }
    for reading in daily.json()["readings"]:
        single_input = {**input_data}
        if reading["engine_id"] == "tarot":
            single_input["options"] = {"spread": "three-card"}
        single = client.post(
            "/api/v1/readings",
            json={"engine_id": reading["engine_id"], "input": single_input, "subject_key": payload["subject_key"]},
        )
        assert single.status_code == 200
        assert single.json()["seed"] == reading["seed"]
        assert single.json()["drawn"] == reading["drawn"]


def test_rate_limit_returns_429_and_retry_after(monkeypatch):
    import app.core.ratelimit as ratelimit_module

    monkeypatch.setattr(ratelimit_module, "rate_limiter", RateLimiter(limit=1, window_seconds=60, clock=lambda: 0))
    payload = {"engine_id": "tarot", "input": {"target_date": "2026-01-01"}}
    assert client.post("/api/v1/readings", json=payload).status_code == 200
    response = client.post("/api/v1/readings", json=payload)
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"

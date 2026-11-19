import pytest
from fastapi.testclient import TestClient

from app.core.ratelimit import RateLimiter
from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_systems_lists_only_tarot():
    response = client.get("/api/v1/systems")
    assert response.status_code == 200
    systems = response.json()
    assert [item["id"] for item in systems] == ["tarot"]
    assert all(set(item) == {"id", "name", "tradition", "required_fields", "interpretation_langs"} for item in systems)


def test_reading_success():
    response = client.post("/api/v1/readings", json={"engine_id": "tarot", "input": {"target_date": "2026-01-01"}})
    assert response.status_code == 200
    assert response.json()["engine_id"] == "tarot"


@pytest.mark.parametrize(
    ("path", "payload"),
    [
        ("/api/v1/readings", {"engine_id": "tarot", "input": {"target_date": "2026-01-01"}}),
    ],
)
def test_empty_subject_key_is_rejected_but_omitted_subject_key_is_valid(path, payload):
    empty = client.post(path, json={**payload, "subject_key": ""})
    omitted = client.post(path, json=payload)

    assert empty.status_code == 422
    assert omitted.status_code == 200


def test_removed_birth_time_is_ignored():
    response = client.post(
        "/api/v1/readings",
        json={
            "engine_id": "tarot",
            "input": {"target_date": "2026-01-01", "birth_time": "12:34"},
        },
    )
    assert response.status_code == 200


def test_oversized_question_is_rejected():
    response = client.post(
        "/api/v1/readings",
        json={
            "engine_id": "tarot",
            "input": {"target_date": "2026-01-01", "question": "あ" * 201},
        },
    )
    assert response.status_code == 422


def test_oversized_subject_key_is_rejected():
    response = client.post(
        "/api/v1/readings",
        json={
            "engine_id": "tarot",
            "input": {"target_date": "2026-01-01"},
            "subject_key": "a" * 65,
        },
    )
    assert response.status_code == 422


def test_systems_can_be_localized():
    query_response = client.get("/api/v1/systems?lang=en")
    header_response = client.get("/api/v1/systems", headers={"Accept-Language": "en"})
    for response in (query_response, header_response):
        assert response.status_code == 200
        tarot = next(system for system in response.json() if system["id"] == "tarot")
        assert tarot["name"] == "Tarot"
        assert tarot["interpretation_langs"] == ["ja", "en"]
        assert "Accept-Language" in response.headers.get("vary", "")


def test_reading_can_be_localized_without_changing_seed():
    payload = {"engine_id": "tarot", "input": {"target_date": "2026-01-01"}, "subject_key": "lang"}
    japanese = client.post("/api/v1/readings", json={**payload, "lang": "ja"})
    english = client.post("/api/v1/readings", json={**payload, "lang": "en"})
    assert japanese.status_code == english.status_code == 200
    assert japanese.json()["seed"] == english.json()["seed"]
    assert [
        (symbol["key"], symbol["reversed"]) for symbol in japanese.json()["drawn"]
    ] == [
        (symbol["key"], symbol["reversed"]) for symbol in english.json()["drawn"]
    ]
    assert english.json()["engine_name"] == "Tarot"
    assert english.json()["lang"] == "en"


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


@pytest.mark.parametrize("engine_id", ["iching", "runes", "omikuji", "astrology", "numerology", "bazi", "mayan", "geomancy"])
def test_removed_engines_are_unknown(engine_id):
    response = client.post("/api/v1/readings", json={"engine_id": engine_id, "input": {"target_date": "2026-01-01"}})
    assert response.status_code == 404


def test_daily_endpoint_is_removed():
    assert client.post("/api/v1/readings/daily", json={"target_date": "2026-01-01"}).status_code in {404, 405}


def test_reading_required_input_missing(monkeypatch):
    from app.divination.registry import get_engine

    monkeypatch.setattr(get_engine("tarot"), "required_fields", frozenset({"birth_date"}))
    response = client.post(
        "/api/v1/readings",
        json={"engine_id": "tarot", "input": {"target_date": "2026-01-01"}},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == {"missing_fields": ["birth_date"]}


def test_rate_limit_returns_429_and_retry_after(monkeypatch):
    import app.core.ratelimit as ratelimit_module

    monkeypatch.setattr(ratelimit_module, "rate_limiter", RateLimiter(limit=1, window_seconds=60, clock=lambda: 0))
    payload = {"engine_id": "tarot", "input": {"target_date": "2026-01-01"}}
    assert client.post("/api/v1/readings", json=payload).status_code == 200
    response = client.post("/api/v1/readings", json=payload)
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"

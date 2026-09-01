from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_systems():
    response = client.get("/api/v1/systems")
    assert response.status_code == 200
    systems = response.json()
    assert len(systems) == 8
    assert sum(item["available"] for item in systems) == 3


def test_reading_success():
    response = client.post("/api/v1/readings", json={"engine_id": "tarot", "input": {"target_date": "2026-01-01"}})
    assert response.status_code == 200
    assert response.json()["engine_id"] == "tarot"


def test_reading_payment_required():
    response = client.post(
        "/api/v1/readings", json={"engine_id": "astrology", "input": {"target_date": "2026-01-01"}}
    )
    assert response.status_code == 402


def test_reading_unknown_engine():
    response = client.post("/api/v1/readings", json={"engine_id": "unknown", "input": {"target_date": "2026-01-01"}})
    assert response.status_code == 404


def test_reading_required_input_missing():
    response = client.post(
        "/api/v1/readings",
        json={"engine_id": "astrology", "input": {"target_date": "2026-01-01"}},
        headers={"X-Magi-Tier": "plus"},
    )
    assert response.status_code == 422


def test_daily_free_returns_one_and_requires_upgrade():
    response = client.post("/api/v1/readings/daily", json={"target_date": "2026-01-01", "subject_key": "daily"})
    assert response.status_code == 200
    assert len(response.json()["readings"]) == 1
    assert response.json()["upgrade_required"] is True


def test_daily_plus_returns_three_distinct_traditions():
    response = client.post(
        "/api/v1/readings/daily",
        json={"target_date": "2026-01-01", "subject_key": "daily"},
        headers={"X-Magi-Tier": "plus"},
    )
    assert response.status_code == 200
    readings = response.json()["readings"]
    assert len(readings) == 3
    assert len({reading["tradition"] for reading in readings}) == 3
    assert response.json()["upgrade_required"] is False

"""Tarot output must stay byte-identical to the pre-specialization release.

The fixture was generated from main@e7a00a7 (nine-engine Magi) before the
non-tarot engines were removed. Every case compares a SHA-256 of the
canonical reading JSON (generated_at excluded); a subset also stores the
full reading so a regression shows a readable diff.
"""

import contextlib
import hashlib
import io
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core import ratelimit as ratelimit_module
from app.core.ratelimit import RateLimiter
from app.divination.base import DivinationInput
from app.divination.service import cast_reading
from app.main import app
from app.verify import main as verify_main

GOLDEN = json.loads((Path(__file__).parent / "fixtures" / "tarot_golden.json").read_text(encoding="utf-8"))


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(ratelimit_module, "rate_limiter", RateLimiter(limit=10_000, window_seconds=60))
    return TestClient(app)


def _canonical(payload: dict) -> str:
    payload = dict(payload)
    payload.pop("generated_at", None)
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(payload: dict) -> str:
    return hashlib.sha256(_canonical(payload).encode()).hexdigest()


def _verify_stdout(argv: list[str]) -> str:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        assert verify_main(argv) == 0
    return out.getvalue()


def test_golden_fixture_covers_both_spreads_and_languages():
    cases = GOLDEN["cases"]
    assert len(cases) == 576
    assert {case["lang"] for case in cases} == {"ja", "en"}
    assert {case["input"]["options"].get("spread") for case in cases} == {None, "three-card", "celtic-cross"}
    assert sum("reading" in case for case in cases) == 24


@pytest.mark.parametrize("case", GOLDEN["cases"], ids=lambda case: case["digest"][:12])
def test_service_reading_matches_pre_change_output(case):
    reading = cast_reading("tarot", DivinationInput(**case["input"]), case["subject_key"], case["lang"])
    payload = reading.model_dump(mode="json")
    if "reading" in case:
        payload.pop("generated_at")
        assert payload == case["reading"]
    assert _digest(payload) == case["digest"]


def test_api_reading_matches_pre_change_output(client):
    for case in GOLDEN["cases"][::8]:
        response = client.post(
            "/api/v1/readings",
            json={"engine_id": "tarot", "input": case["input"], "subject_key": case["subject_key"], "lang": case["lang"]},
        )
        assert response.status_code == 200
        assert _digest(response.json()) == case["digest"]


@pytest.mark.parametrize("item", GOLDEN["share_urls"], ids=lambda item: item["digest"][:12])
def test_share_urls_reproduce_pre_change_reading(item):
    fragment_url = item["url"]
    query_url = fragment_url.replace("/#", "/?")
    assert _digest(json.loads(_verify_stdout([fragment_url, "--json"]))) == item["digest"]
    assert _digest(json.loads(_verify_stdout([query_url, "--json"]))) == item["digest"]


def test_verify_human_output_is_unchanged():
    expected = GOLDEN["verify_human_output"]
    assert _verify_stdout([expected["url"]]) == expected["stdout"]


@pytest.mark.parametrize("lang", ["ja", "en"])
def test_unknown_spread_error_is_unchanged(client, lang):
    response = client.post(
        "/api/v1/readings",
        json={"engine_id": "tarot", "input": {"target_date": "2026-01-01", "options": {"spread": "unknown"}}, "lang": lang},
    )
    assert {"status": response.status_code, "body": response.json()} == GOLDEN["unknown_spread"][lang]


@pytest.mark.parametrize("lang", ["ja", "en"])
def test_systems_tarot_entry_is_unchanged(client, lang):
    response = client.get(f"/api/v1/systems?lang={lang}")
    assert response.json() == [GOLDEN["systems_tarot"][lang]]

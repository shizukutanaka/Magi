import json
from urllib.parse import urlencode

from fastapi.testclient import TestClient

from app.main import app
from app.verify import main

client = TestClient(app)


def share_url(**params: str) -> str:
    return f"https://example.test/?{urlencode(params)}"


def fragment_share_url(**params: str) -> str:
    return f"http://localhost:8000/#{urlencode(params)}"


def test_cli_fragment_reading_matches_query(capsys):
    params = {"engine": "tarot", "date": "2026-01-01", "s": "fragment-reading"}
    assert main([share_url(**params), "--json"]) == 0
    query_result = json.loads(capsys.readouterr().out)
    assert main([fragment_share_url(**params), "--json"]) == 0
    fragment_result = json.loads(capsys.readouterr().out)
    assert fragment_result["seed"] == query_result["seed"]
    assert fragment_result["drawn"] == query_result["drawn"]


def test_cli_single_reading_matches_api(capsys):
    url = share_url(engine="tarot", date="2026-01-01", q="今日の問い", s="verify-single")
    exit_code = main([url, "--json"])
    cli = json.loads(capsys.readouterr().out)
    api = client.post(
        "/api/v1/readings",
        json={
            "engine_id": "tarot",
            "input": {"target_date": "2026-01-01", "question": "今日の問い"},
            "subject_key": "verify-single",
        },
    )
    assert exit_code == 0
    assert api.status_code == 200
    assert cli["seed"] == api.json()["seed"]
    assert cli["drawn"] == api.json()["drawn"]


def test_cli_daily_matches_api(capsys):
    url = share_url(
        daily="1",
        date="2026-01-01",
        q="今日の問い",
        birth="1990-01-02",
        name="山田太郎",
        s="verify-daily",
    )
    exit_code = main([url, "--json"])
    cli = json.loads(capsys.readouterr().out)
    api = client.post(
        "/api/v1/readings/daily",
        json={
            "target_date": "2026-01-01",
            "question": "今日の問い",
            "birth_date": "1990-01-02",
            "full_name": "山田太郎",
            "subject_key": "verify-daily",
        },
    )
    assert exit_code == 0
    assert api.status_code == 200
    assert [reading["seed"] for reading in cli["readings"]] == [
        reading["seed"] for reading in api.json()["readings"]
    ]
    assert [reading["drawn"] for reading in cli["readings"]] == [
        reading["drawn"] for reading in api.json()["readings"]
    ]
    assert cli["overview"] == api.json()["overview"]


def test_cli_default_and_explicit_tarot_spread_match(capsys):
    implicit_url = share_url(engine="tarot", date="2026-01-01", s="verify-spread")
    assert main([implicit_url, "--json"]) == 0
    implicit = json.loads(capsys.readouterr().out)
    explicit_url = share_url(
        engine="tarot",
        date="2026-01-01",
        spread="three-card",
        s="verify-spread",
    )
    assert main([explicit_url, "--json"]) == 0
    explicit = json.loads(capsys.readouterr().out)
    assert implicit["seed"] == explicit["seed"]


def test_cli_language_does_not_change_seed(capsys):
    url = share_url(engine="tarot", date="2026-01-01", s="verify-language")
    assert main([url, "--json"]) == 0
    japanese = json.loads(capsys.readouterr().out)
    assert main([url, "--lang", "en", "--json"]) == 0
    english = json.loads(capsys.readouterr().out)
    assert japanese["seed"] == english["seed"]
    assert english["engine_name"] == "Tarot"


def test_cli_language_flag_overrides_share_url(capsys):
    url = share_url(engine="tarot", date="2026-01-01", lang="ja", s="verify-language-order")
    assert main([url, "--lang", "en", "--json"]) == 0
    english = json.loads(capsys.readouterr().out)
    assert english["lang"] == "en"
    assert english["engine_name"] == "Tarot"


def test_cli_language_query_parameter(capsys):
    url = share_url(engine="tarot", date="2026-01-01", lang="en", s="verify-language-query")
    assert main([url, "--json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["lang"] == "en"


def test_cli_expect_seed_exit_codes(capsys):
    url = share_url(engine="tarot", date="2026-01-01", s="verify-expect")
    assert main([url, "--json"]) == 0
    expected = json.loads(capsys.readouterr().out)["seed"]
    assert main([url, "--expect-seed", expected]) == 0
    assert "一致" in capsys.readouterr().out
    assert main([url, "--expect-seed", "0" * 64]) == 1
    assert "不一致" in capsys.readouterr().out


def test_cli_missing_required_field_is_japanese_error(capsys):
    exit_code = main([share_url(engine="numerology", date="2026-01-01")])
    captured = capsys.readouterr()
    assert exit_code == 2
    assert "必須入力が不足しています" in captured.err
    assert "Traceback" not in captured.err


def test_cli_unknown_engine_is_error(capsys):
    exit_code = main([share_url(engine="unknown", date="2026-01-01")])
    captured = capsys.readouterr()
    assert exit_code == 2
    assert "未知の流派" in captured.err
    assert "Traceback" not in captured.err

import pytest

from app.core.config import (
    FALSE_VALUES,
    TRUE_VALUES,
    ConfigError,
    get_rate_limit_per_minute,
    get_trust_proxy_headers,
    validate_environment,
)


def test_unset_environment_uses_defaults(monkeypatch):
    monkeypatch.delenv("MAGI_RATE_LIMIT_PER_MINUTE", raising=False)
    monkeypatch.delenv("MAGI_TRUST_PROXY", raising=False)
    assert get_rate_limit_per_minute() == 60
    assert get_trust_proxy_headers() is False


@pytest.mark.parametrize("value", ["", "   "])
def test_blank_environment_uses_defaults(monkeypatch, value):
    monkeypatch.setenv("MAGI_RATE_LIMIT_PER_MINUTE", value)
    assert get_rate_limit_per_minute() == 60
    monkeypatch.setenv("MAGI_TRUST_PROXY", value)
    assert get_trust_proxy_headers() is False


@pytest.mark.parametrize(("value", "expected"), [("0", 0), ("-5", -5), ("100", 100)])
def test_rate_limit_accepts_integer_values(monkeypatch, value, expected):
    monkeypatch.setenv("MAGI_RATE_LIMIT_PER_MINUTE", value)
    assert get_rate_limit_per_minute() == expected


def test_rate_limit_rejects_non_integer(monkeypatch):
    monkeypatch.setenv("MAGI_RATE_LIMIT_PER_MINUTE", "1O0")
    with pytest.raises(ConfigError, match="MAGI_RATE_LIMIT_PER_MINUTE"):
        get_rate_limit_per_minute()


@pytest.mark.parametrize("value", TRUE_VALUES)
def test_true_proxy_values(monkeypatch, value):
    monkeypatch.setenv("MAGI_TRUST_PROXY", value)
    assert get_trust_proxy_headers() is True


@pytest.mark.parametrize("value", FALSE_VALUES)
def test_false_proxy_values(monkeypatch, value):
    monkeypatch.setenv("MAGI_TRUST_PROXY", value)
    assert get_trust_proxy_headers() is False


@pytest.mark.parametrize(("value", "expected"), [(" True ", True), (" FaLsE ", False)])
def test_proxy_values_are_trimmed_and_case_insensitive(monkeypatch, value, expected):
    monkeypatch.setenv("MAGI_TRUST_PROXY", value)
    assert get_trust_proxy_headers() is expected


def test_proxy_rejects_unknown_value(monkeypatch):
    monkeypatch.setenv("MAGI_TRUST_PROXY", "maybe")
    with pytest.raises(ConfigError, match="MAGI_TRUST_PROXY"):
        get_trust_proxy_headers()


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("MAGI_RATE_LIMIT_PER_MINUTE", "1O0"),
        ("MAGI_TRUST_PROXY", "maybe"),
    ],
)
def test_validate_environment_rejects_invalid_values(monkeypatch, name, value):
    monkeypatch.delenv("MAGI_RATE_LIMIT_PER_MINUTE", raising=False)
    monkeypatch.delenv("MAGI_TRUST_PROXY", raising=False)
    monkeypatch.setenv(name, value)
    with pytest.raises(ConfigError, match=name):
        validate_environment()

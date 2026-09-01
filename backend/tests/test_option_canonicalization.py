from datetime import date

import pytest

from app.divination.base import DivinationInput
from app.divination.service import UnknownSpreadError, cast_reading, daily_reading

TARGET_DATE = date(2026, 9, 1)
SUBJECT_KEY = "demo"


def _input(options: dict[str, str]) -> DivinationInput:
    return DivinationInput(target_date=TARGET_DATE, birth_date=date(1990, 4, 5), full_name="山田太郎", options=options)


def _signature(reading):
    return reading.seed, [symbol.key for symbol in reading.drawn]


def test_unknown_option_keys_do_not_change_iching():
    baseline = cast_reading("iching", _input({}), SUBJECT_KEY)
    assert _signature(cast_reading("iching", _input({"foo": "bar"}), SUBJECT_KEY)) == _signature(baseline)


def test_iching_ignores_tarot_spread():
    baseline = cast_reading("iching", _input({}), SUBJECT_KEY)
    assert _signature(cast_reading("iching", _input({"spread": "celtic-cross"}), SUBJECT_KEY)) == _signature(baseline)


def test_tarot_keeps_spread_and_drops_unknown_keys():
    baseline = cast_reading("tarot", _input({"spread": "celtic-cross"}), SUBJECT_KEY)
    extra = cast_reading("tarot", _input({"spread": "celtic-cross", "foo": "bar"}), SUBJECT_KEY)
    assert _signature(extra) == _signature(baseline)
    assert len(extra.drawn) == 10


def test_tarot_still_rejects_unknown_spread():
    with pytest.raises(UnknownSpreadError):
        cast_reading("tarot", _input({"spread": "nope"}), SUBJECT_KEY)


def test_daily_reading_ignores_unknown_option_keys():
    baseline = daily_reading(_input({}), SUBJECT_KEY)
    extra = daily_reading(_input({"spread": "celtic-cross", "foo": "bar"}), SUBJECT_KEY)
    assert [_signature(reading) for reading in extra["readings"]] == [
        _signature(reading) for reading in baseline["readings"]
    ]

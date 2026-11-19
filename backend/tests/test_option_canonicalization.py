from datetime import date

import pytest

from app.divination.base import DivinationInput
from app.divination.service import UnknownSpreadError, cast_reading

TARGET_DATE = date(2026, 9, 1)
SUBJECT_KEY = "demo"


def _input(options: dict[str, str]) -> DivinationInput:
    return DivinationInput(target_date=TARGET_DATE, birth_date=date(1990, 4, 5), full_name="山田太郎", options=options)


def _signature(reading):
    return reading.seed, [symbol.key for symbol in reading.drawn]


def test_tarot_keeps_spread_and_drops_unknown_keys():
    baseline = cast_reading("tarot", _input({"spread": "celtic-cross"}), SUBJECT_KEY)
    extra = cast_reading("tarot", _input({"spread": "celtic-cross", "foo": "bar"}), SUBJECT_KEY)
    assert _signature(extra) == _signature(baseline)
    assert len(extra.drawn) == 10


def test_tarot_still_rejects_unknown_spread():
    with pytest.raises(UnknownSpreadError):
        cast_reading("tarot", _input({"spread": "nope"}), SUBJECT_KEY)


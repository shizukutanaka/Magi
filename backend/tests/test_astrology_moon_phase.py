from datetime import date, timedelta

import pytest

from app.divination.base import DivinationInput
from app.divination.data.astrology import MOON_PHASES
from app.divination.service import cast_reading


@pytest.mark.parametrize(
    ("target_date", "expected"),
    [
        (date(2025, 1, 13), "満月"),
        (date(2026, 3, 3), "満月"),
        (date(2025, 1, 29), "新月"),
        (date(2026, 8, 28), "満月"),
        (date(2026, 9, 1), "十八夜"),
    ],
)
def test_moon_phase_uses_centered_bins(target_date, expected):
    reading = cast_reading(
        "astrology",
        DivinationInput(target_date=target_date, birth_date=date(1990, 1, 1)),
        "astrology-test",
        "ja",
    )
    assert reading.drawn[1].key == expected


def test_moon_phase_index_stays_in_range_for_one_cycle():
    epoch = date(2000, 1, 6)
    for offset in range(30):
        target_date = epoch + timedelta(days=offset)
        reading = cast_reading(
            "astrology",
            DivinationInput(target_date=target_date, birth_date=date(1990, 1, 1)),
            "astrology-test",
            "ja",
        )
        assert MOON_PHASES.index(reading.drawn[1].key) in range(8)

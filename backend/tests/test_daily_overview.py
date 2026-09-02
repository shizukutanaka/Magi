import re
from datetime import date

from app.divination.base import DivinationInput
from app.divination.service import daily_reading

CJK = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")


def _mixed_input():
    return DivinationInput(
        target_date=date(2026, 1, 1),
        birth_date=date(1990, 1, 2),
        full_name="Taro Yamada",
    )


def test_daily_overview_pairs_each_tradition_with_its_leading_symbol():
    inp = _mixed_input()
    result = daily_reading(inp, "geomancy-tarot-mayan", "ja")
    readings = result["readings"]

    assert [reading.engine_id for reading in readings] == ["tarot", "geomancy", "mayan"]
    assert len({len(reading.drawn) for reading in readings}) > 1
    assert all(
        f"{reading.engine_name}の{reading.drawn[0].name}" in result["overview"]
        for reading in readings
    )
    assert "共通" not in result["overview"]


def test_daily_overview_is_english_and_uses_each_leading_symbol():
    inp = _mixed_input()
    result = daily_reading(inp, "geomancy-tarot-mayan", "en")
    readings = result["readings"]

    assert all(
        f"{reading.drawn[0].name} in {reading.engine_name}" in result["overview"]
        for reading in readings
    )
    assert "shared" not in result["overview"]
    assert not CJK.search(result["overview"])

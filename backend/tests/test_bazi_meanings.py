import re
from datetime import date

from app.divination.base import DivinationInput
from app.divination.data.bazi import (
    BRANCH_MEANINGS,
    BRANCHES,
    DAY_BRANCH_MEANINGS,
    DAY_STEM_MEANINGS,
    STEM_MEANINGS,
    STEMS,
)
from app.divination.data.en import TEXTS as EN_TEXTS
from app.divination.service import cast_reading

CJK = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")


def _input(birth_date: date) -> DivinationInput:
    return DivinationInput(target_date=date(2026, 9, 1), birth_date=birth_date)


def test_bazi_meaning_sets_are_complete_and_unique():
    japanese_sets = (
        STEM_MEANINGS,
        BRANCH_MEANINGS,
        DAY_STEM_MEANINGS,
        DAY_BRANCH_MEANINGS,
    )
    assert [len(values) for values in japanese_sets] == [10, 12, 10, 12]
    assert all(len(set(values)) == len(values) for values in japanese_sets)
    assert all(all(value for value in values) for values in japanese_sets)

    english = EN_TEXTS["bazi"]
    english_sets = (
        tuple(english[f"stem.{index}.meaning"] for index in range(len(STEMS))),
        tuple(english[f"branch.{index}.meaning"] for index in range(len(BRANCHES))),
        tuple(english[f"day_stem.{index}.meaning"] for index in range(len(STEMS))),
        tuple(english[f"day_branch.{index}.meaning"] for index in range(len(BRANCHES))),
    )
    assert [len(values) for values in english_sets] == [10, 12, 10, 12]
    assert all(len(set(values)) == len(values) for values in english_sets)
    assert all(all(values) for values in english_sets)
    assert all(not CJK.search(value) for values in english_sets for value in values)


def test_same_year_and_day_pillar_have_distinct_interpretations():
    japanese = cast_reading("bazi", _input(date(1990, 5, 5)), "bazi-ja", "ja")
    english = cast_reading("bazi", _input(date(1990, 5, 5)), "bazi-en", "en")

    assert japanese.drawn[0].name == japanese.drawn[1].name == "庚午"
    assert japanese.sections[0].body != japanese.sections[1].body
    assert english.sections[0].body != english.sections[1].body
    assert all(not CJK.search(section.body) for section in english.sections)


def test_bazi_pillar_interpretations_vary_across_birth_dates():
    readings = [
        cast_reading(
            "bazi",
            _input(date(year, 1, 1)),
            f"variation-{year}",
        )
        for year in range(1930, 2011)
    ]

    assert len({reading.sections[0].body for reading in readings}) >= 40
    assert len({reading.sections[1].body for reading in readings}) >= 40


def test_bazi_compatibility_explains_harmony_and_clash():
    japanese = cast_reading("bazi", _input(date(1990, 5, 5)), "compatibility-ja", "ja")
    english = cast_reading("bazi", _input(date(1990, 5, 5)), "compatibility-en", "en")

    assert "六合" in japanese.sections[2].body
    assert "冲" in japanese.sections[2].body
    assert "Six Harmony" in english.sections[2].body
    assert "Clash" in english.sections[2].body

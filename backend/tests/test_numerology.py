from datetime import date

import pytest

from app.divination.base import DivinationInput
from app.divination.data.numerology import MASTER_NUMBERS, NUMBERS
from app.divination.engines.numerology import _name_number
from app.divination.registry import get_engine
from app.divination.seed import SeededRandom, build_seed
from app.i18n import t


def cast(full_name: str, birth_date: date, lang: str = "ja"):
    inp = DivinationInput(
        target_date=date(2026, 9, 1),
        question="テーマ",
        full_name=full_name,
        birth_date=birth_date,
    )
    return get_engine("numerology").cast(
        inp,
        SeededRandom(build_seed("numerology-test", "numerology", inp)),
        lang,
    )


def test_all_number_meanings_are_distinct_and_nonempty():
    assert list(NUMBERS) == [str(number) for number in (1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 22, 33)]
    assert all(number.key and number.life_path and number.destiny for number in NUMBERS.values())
    assert len({number.life_path for number in NUMBERS.values()}) == len(NUMBERS)
    assert len({number.destiny for number in NUMBERS.values()}) == len(NUMBERS)


def test_life_path_body_depends_on_the_life_path_number():
    first = cast("Ada", date(1990, 1, 1))
    second = cast("Ada", date(1990, 1, 2))
    assert first.drawn[0].key != second.drawn[0].key
    assert first.sections[0].body != second.sections[0].body


@pytest.mark.parametrize("lang", ["ja", "en"])
@pytest.mark.parametrize(
    ("birth_date", "master_number"),
    [
        (date(2000, 1, 8), 11),
        (date(1990, 1, 2), 22),
        (date(1999, 1, 4), 33),
    ],
)
def test_guidance_uses_master_number_text_for_all_master_numbers(
    birth_date, master_number, lang
):
    master = cast("abc", birth_date, lang)
    plain = cast("abc", date(1990, 1, 1), lang)

    assert master.drawn[0].key == str(master_number)
    assert master.sections[3].body == t(lang, "body.numerology.guidance")
    assert plain.sections[3].body == t(lang, "body.numerology.guidance_plain")
    assert master.drawn[0].key in {str(number) for number in MASTER_NUMBERS}


@pytest.mark.parametrize(
    ("lang", "conditional_phrase"),
    [("ja", "持つ場合も"), ("en", "Even with")],
)
def test_master_number_guidance_is_not_conditionally_worded(lang, conditional_phrase):
    reading = cast("abc", date(1990, 1, 2), lang)
    assert conditional_phrase not in reading.sections[3].body


def test_name_number_ignores_punctuation():
    assert _name_number("Anne-Marie O'Neil") == _name_number("AnneMarieONeil")

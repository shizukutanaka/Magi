from datetime import date

from app.divination.base import DivinationInput
from app.divination.data.numerology import MASTER_NUMBERS, NUMBERS
from app.divination.engines.numerology import _name_number
from app.divination.registry import get_engine
from app.divination.seed import SeededRandom, build_seed


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


def test_guidance_distinguishes_master_numbers():
    plain = cast("abc", date(1990, 1, 1))
    master = cast("Taro Yamada", date(1990, 1, 2))
    assert "マスターナンバー" not in plain.sections[3].body
    assert "マスターナンバー" in master.sections[3].body
    assert master.drawn[0].key in {str(number) for number in MASTER_NUMBERS}


def test_name_number_ignores_punctuation():
    assert _name_number("Anne-Marie O'Neil") == _name_number("AnneMarieONeil")

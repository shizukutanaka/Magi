from collections import Counter
from datetime import date

from app.divination.base import DivinationInput
from app.divination.service import select_daily_engines

TARGET_DATE = date(2026, 9, 1)


def _input(*, with_personal_data: bool) -> DivinationInput:
    return DivinationInput(
        target_date=TARGET_DATE,
        birth_date=date(1990, 1, 2) if with_personal_data else None,
        full_name="山田太郎" if with_personal_data else None,
    )


def _engine_ids(inp: DivinationInput, subject_key: str) -> list[str]:
    return [engine.id for engine in select_daily_engines(inp, subject_key)]


def test_daily_selection_is_deterministic_and_date_sensitive():
    inp = _input(with_personal_data=True)
    assert _engine_ids(inp, "subject-0") == _engine_ids(inp, "subject-0")

    other_date_input = inp.model_copy(update={"target_date": date(2026, 9, 2)})
    assert any(
        _engine_ids(inp, f"subject-{index}") != _engine_ids(other_date_input, f"subject-{index}")
        for index in range(100)
    )


def test_daily_selection_uses_three_distinct_cultures_with_or_without_personal_data():
    for inp in (_input(with_personal_data=False), _input(with_personal_data=True)):
        selected = select_daily_engines(inp, "culture-test")
        assert len(selected) == 3
        assert len({engine.culture for engine in selected}) == 3


def test_numerology_is_never_selected_with_other_western_engines():
    inp = _input(with_personal_data=True)
    for index in range(500):
        selected_ids = set(_engine_ids(inp, f"subject-{index}"))
        assert not (
            "numerology" in selected_ids
            and {"tarot", "astrology"} & selected_ids
        )


def test_daily_selection_is_fair_across_culture_areas_with_personal_data():
    inp = _input(with_personal_data=True)
    counts = Counter(
        engine.culture
        for index in range(4000)
        for engine in select_daily_engines(inp, f"subject-{index}")
    )
    shares = {culture: count / 4000 for culture, count in counts.items()}

    assert set(shares) == {"western", "chinese", "nordic", "japanese", "mesoamerican", "afro-european"}
    assert all(0.45 <= share <= 0.55 for share in shares.values())


def test_daily_selection_is_fair_across_culture_areas_without_personal_data():
    inp = _input(with_personal_data=False)
    counts = Counter(
        engine.culture
        for index in range(4000)
        for engine in select_daily_engines(inp, f"subject-{index}")
    )
    shares = {culture: count / 4000 for culture, count in counts.items()}

    assert set(shares) == {"western", "chinese", "nordic", "japanese", "afro-european"}
    assert all(0.55 <= share <= 0.65 for share in shares.values())

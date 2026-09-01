from datetime import date

import pytest

from app.divination.base import DivinationInput
from app.divination.registry import get_engine
from app.divination.seed import SeededRandom, build_seed

ENGINE_IDS = ("tarot", "iching", "runes", "omikuji", "astrology", "numerology", "bazi", "mayan")


def without_generated_at(reading):
    value = reading.model_dump()
    value.pop("generated_at")
    return value


@pytest.mark.parametrize("engine_id", ENGINE_IDS)
def test_cast_is_deterministic(engine_id):
    engine = get_engine(engine_id)
    inp = DivinationInput(
        target_date=date(2026, 2, 3),
        question="今日のテーマ",
        birth_date=date(1990, 4, 5) if "birth_date" in engine.required_fields else None,
        full_name="山田太郎" if "full_name" in engine.required_fields else None,
    )
    seed = build_seed("tester", engine.id, inp)
    first = engine.cast(inp, SeededRandom(seed))
    second = engine.cast(inp, SeededRandom(seed))
    assert without_generated_at(first) == without_generated_at(second)


@pytest.mark.parametrize("engine_id", ENGINE_IDS)
def test_input_change_changes_seed_and_drawn(engine_id):
    engine = get_engine(engine_id)
    inp = DivinationInput(
        target_date=date(2026, 2, 3),
        question="今日のテーマ",
        birth_date=date(1990, 4, 5) if "birth_date" in engine.required_fields else None,
        full_name="山田太郎" if "full_name" in engine.required_fields else None,
    )
    seed = build_seed("tester", engine.id, inp)
    first = engine.cast(inp, SeededRandom(seed))
    changed = inp.model_copy(update={"question": "今日のテーマ!"})
    changed_seed = build_seed("tester", engine.id, changed)
    changed_reading = engine.cast(changed, SeededRandom(changed_seed))
    assert changed_seed != seed
    assert changed_reading.drawn != first.drawn

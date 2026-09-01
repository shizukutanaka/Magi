from datetime import date

import pytest

from app.divination.base import DivinationInput
from app.divination.registry import get_engine
from app.divination.seed import SeededRandom, build_seed

ENGINE_IDS = ("tarot", "iching", "runes", "omikuji", "astrology", "numerology", "bazi", "mayan", "geomancy")


def input_for(engine):
    return DivinationInput(
        target_date=date(2026, 3, 4),
        birth_date=date(1988, 8, 8) if "birth_date" in engine.required_fields else None,
        full_name="山田太郎" if "full_name" in engine.required_fields else None,
    )


@pytest.mark.parametrize("engine_id", ENGINE_IDS)
def test_engine_reading_schema(engine_id):
    engine = get_engine(engine_id)
    inp = input_for(engine)
    reading = engine.cast(inp, SeededRandom(build_seed("shape", engine.id, inp)))
    assert reading.engine_id == engine.id
    assert reading.drawn
    assert reading.score is not None and 0 <= reading.score <= 100
    assert len(reading.sections) >= 3


@pytest.mark.parametrize("engine_id", ENGINE_IDS)
def test_image_hints_are_static_asset_paths(engine_id):
    engine = get_engine(engine_id)
    inp = input_for(engine)
    reading = engine.cast(inp, SeededRandom(build_seed("image", engine.id, inp)))
    assert all(symbol.image_hint == f"{engine.id}/{symbol.key}" for symbol in reading.drawn)


@pytest.mark.parametrize("engine_id", ENGINE_IDS)
def test_required_fields_are_enforced(engine_id):
    engine = get_engine(engine_id)
    if not engine.required_fields:
        pytest.skip("このエンジンに必須入力はない")
    inp = DivinationInput(target_date=date(2026, 3, 4))
    with pytest.raises(ValueError):
        engine.cast(inp, SeededRandom(build_seed("missing", engine.id, inp)))

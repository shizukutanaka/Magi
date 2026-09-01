from datetime import date

from app.divination.base import DivinationInput
from app.divination.data.runes import RUNES
from app.divination.engines.runes import RunesEngine
from app.divination.seed import SeededRandom, build_seed


def test_reversed_lead_rune_uses_reversed_interpretation():
    engine = RunesEngine()
    inp = DivinationInput(target_date=date(2026, 1, 1))
    seed = build_seed("rune-fixed-1", engine.id, inp)
    reading = engine.cast(inp, SeededRandom(seed))
    assert reading.drawn[0].reversed is True
    rune = next(rune for rune in RUNES if rune.key == reading.drawn[0].key)
    assert reading.sections[0].body == rune.reversed_meaning

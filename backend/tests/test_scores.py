from datetime import date

from app.divination.base import DivinationInput
from app.divination.registry import all_engines
from app.divination.service import cast_reading


def test_only_traditionally_ranked_engines_have_scores():
    inp = DivinationInput(
        target_date=date(2026, 9, 1),
        birth_date=date(1990, 1, 2),
        full_name="山田太郎",
    )
    for engine in all_engines():
        reading = cast_reading(engine.id, inp, "score-test")
        assert reading.score is None

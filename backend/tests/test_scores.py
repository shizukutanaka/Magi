from datetime import date

from app.divination.base import DivinationInput
from app.divination.data.omikuji import GRADE_SCORES, GRADES
from app.divination.registry import all_engines
from app.divination.service import cast_reading, daily_reading


def test_only_traditionally_ranked_engines_have_scores():
    inp = DivinationInput(
        target_date=date(2026, 9, 1),
        birth_date=date(1990, 1, 2),
        full_name="山田太郎",
    )
    ranked = {"omikuji", "geomancy"}
    for engine in all_engines():
        reading = cast_reading(engine.id, inp, "score-test")
        assert (reading.score is not None) == (engine.id in ranked)


def test_omikuji_grade_scores_are_fixed_and_ordered():
    readings = {}
    inp = DivinationInput(target_date=date(2026, 9, 1))
    for index in range(500):
        reading = cast_reading("omikuji", inp, f"grade-test-{index}")
        readings[reading.drawn[0].key] = reading.score
        if len(readings) == len(GRADE_SCORES):
            break

    assert set(readings) == set(GRADE_SCORES)
    assert all(readings[key] == score for key, score in GRADE_SCORES.items())
    assert [GRADE_SCORES[row[0]] for row in GRADES] == sorted(
        GRADE_SCORES.values(), reverse=True
    )


def test_daily_reading_without_ranked_engines_has_no_average_score():
    result = daily_reading(
        DivinationInput(target_date=date(2026, 1, 3)),
        "scoreless",
    )
    assert result["readings"]
    assert all(reading.engine_id not in {"omikuji", "geomancy"} for reading in result["readings"])
    assert all(reading.score is None for reading in result["readings"])
    assert result["score"] is None

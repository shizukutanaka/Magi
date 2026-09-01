import re
from datetime import date

import pytest

from app.divination.base import DivinationInput
from app.divination.question import classify_question
from app.divination.registry import get_engine
from app.divination.seed import SeededRandom, build_seed
from app.divination.service import cast_reading
from app.i18n import t

CJK = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")


def test_question_classification_is_deterministic_and_language_independent():
    question = "What is my work direction?"
    assert classify_question(question) == classify_question(question) == "work"


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("転職すべきか迷っています", "work"),
        ("好きな人に告白すべきか", "love"),
        ("健康のために睡眠を見直したい", "health"),
        ("今月の貯金と家計を考えたい", "money"),
        ("今日はどんな日でしょうか", "general"),
    ],
)
def test_question_classification_examples(question, expected):
    assert classify_question(question) == expected


def test_question_focus_is_localized_without_changing_topic():
    question = "好きな人に告白すべきか"
    inp = DivinationInput(target_date=date(2026, 9, 1), question=question)
    japanese = cast_reading("tarot", inp, "question", "ja")
    english = cast_reading("tarot", inp, "question", "en")
    assert classify_question(question) == "love"
    assert japanese.sections[1].title == t("ja", "section.focus", topic="恋愛")
    assert english.sections[1].title == t("en", "section.focus", topic="Love")
    assert "恋愛" in japanese.sections[1].body
    assert "love" in english.sections[1].body
    assert not CJK.search(english.sections[1].title)
    assert not CJK.search(english.sections[1].body)
    assert japanese.seed == english.seed
    assert [
        (symbol.key, symbol.reversed) for symbol in japanese.drawn
    ] == [
        (symbol.key, symbol.reversed) for symbol in english.drawn
    ]


@pytest.mark.parametrize("question", [None, "   "])
def test_empty_question_preserves_existing_sections(question):
    engine = get_engine("tarot")
    inp = DivinationInput(target_date=date(2026, 9, 1), question=question)
    service_reading = cast_reading("tarot", inp, "question", "ja")
    normalized_inp = inp.model_copy(update={"options": {"spread": "three-card"}})
    direct_reading = engine.cast(
        normalized_inp,
        SeededRandom(build_seed("question", engine.id, normalized_inp)),
        "ja",
    )
    assert classify_question(question) is None
    assert service_reading.sections == direct_reading.sections

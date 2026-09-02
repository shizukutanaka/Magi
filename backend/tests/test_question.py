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


def test_question_classification_is_deterministic():
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


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("I want to remove clutter from my room", "general"),
        ("The apparent calm makes me uneasy", "general"),
        ("I retired last year and feel restless", "general"),
        ("I want to investigate a career change", "work"),
        ("I need to investigate this strange feeling", "general"),
        ("Should I move to another city?", "decision"),
        ("moving abroad, should i decide now?", "decision"),
        ("I moved to another city last year", "decision"),
        ("How do I handle a conflict with my colleague?", "relationship"),
        ("My parents disapprove of my plans", "relationship"),
        ("My friends are distant lately", "relationship"),
        ("I feel tired every morning", "health"),
        ("I am sleepless after the change", "health"),
        ("How do I recover from this illness?", "health"),
        ("Should I increase my savings this month?", "decision"),
        ("my investment portfolio", "money"),
        ("投資を始めるべきタイミングですか", "money"),
        ("片思いの相手に告白すべきでしょうか", "love"),
        ("転職すべきか、今の職場に残るべきか", "work"),
        ("最近ずっと疲れが取れません", "health"),
    ],
)
def test_question_keyword_boundaries_and_suffixes(question, expected):
    assert classify_question(question) == expected


@pytest.mark.parametrize(
    "question",
    ["好きな人に告白すべきか", "How can I tell my crush how I feel?"],
)
def test_question_topic_and_focus_index_are_language_independent(question):
    inp = DivinationInput(target_date=date(2026, 9, 1), question=question)
    japanese = cast_reading("tarot", inp, "question", "ja")
    english = cast_reading("tarot", inp, "question", "en")
    assert classify_question(question) == "love"
    assert japanese.sections[1].title == t("ja", "section.focus", topic="恋愛")
    assert english.sections[1].title == t("en", "section.focus", topic="Love")


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

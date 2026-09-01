import re
from datetime import date

from app.divination.base import DivinationInput
from app.divination.question import TOPICS
from app.divination.registry import all_engines
from app.divination.service import cast_reading
from app.i18n import CATALOGS

CJK = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")
ENGINE_IDS = tuple(engine.id for engine in all_engines())


def focus_keys():
    return [f"body.focus.{engine_id}.{topic}" for engine_id in ENGINE_IDS for topic in TOPICS]


def test_engine_specific_focus_catalogs_are_complete_and_filled():
    keys = focus_keys()
    for lang in ("ja", "en"):
        catalog = CATALOGS[lang]
        assert all(key in catalog for key in keys)
        assert all(not re.search(r"{\w+}", catalog[key]) for key in keys)
        assert all(catalog[key] for key in keys)
    assert all(
        f"body.focus.{topic}" not in CATALOGS[lang]
        for lang in ("ja", "en")
        for topic in TOPICS
    )


def test_focus_bodies_are_specific_to_engine_and_topic():
    for topic in TOPICS:
        bodies = {CATALOGS["ja"][f"body.focus.{engine_id}.{topic}"] for engine_id in ENGINE_IDS}
        assert len(bodies) == len(ENGINE_IDS)
    for engine_id in ENGINE_IDS:
        bodies = {CATALOGS["ja"][f"body.focus.{engine_id}.{topic}"] for topic in TOPICS}
        assert len(bodies) == len(TOPICS)


def test_english_focus_bodies_have_no_cjk():
    for key in focus_keys():
        assert not CJK.search(CATALOGS["en"][key])


def test_focus_depends_on_question_topic_and_engine():
    base = {"target_date": date(2026, 9, 1)}
    work = cast_reading(
        "tarot",
        DivinationInput(**base, question="仕事の進め方を考えたい"),
        "focus-work",
        "ja",
    )
    love = cast_reading(
        "tarot",
        DivinationInput(**base, question="好きな人に告白したい"),
        "focus-love",
        "ja",
    )
    tarot = cast_reading(
        "tarot",
        DivinationInput(**base, question="仕事の進め方を考えたい"),
        "focus-engine-tarot",
        "ja",
    )
    runes = cast_reading(
        "runes",
        DivinationInput(**base, question="仕事の進め方を考えたい"),
        "focus-engine-runes",
        "ja",
    )

    assert work.sections[1].body != love.sections[1].body
    assert tarot.sections[1].body != runes.sections[1].body

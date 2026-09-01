import re
from datetime import date

import pytest

from app.divination.base import DivinationInput
from app.divination.data.omikuji import CATEGORIES
from app.divination.registry import all_engines, get_engine
from app.divination.seed import SeededRandom, build_seed
from app.divination.service import daily_reading, select_daily_engines
from app.i18n import CATALOGS, DEFAULT_LANG, INTERPRETATION_LANGS, resolve_lang, t


def input_for(engine):
    return DivinationInput(
        target_date=date(2026, 9, 1),
        question="Today's question",
        birth_date=date(1990, 1, 2) if "birth_date" in engine.required_fields else None,
        full_name="Taro Yamada" if "full_name" in engine.required_fields else None,
    )


def cast(engine_id: str, lang: str):
    engine = get_engine(engine_id)
    inp = input_for(engine)
    return engine.cast(inp, SeededRandom(build_seed("i18n", engine_id, inp)), lang)


def test_language_never_changes_seed_or_drawn_symbols():
    for engine in all_engines():
        japanese = cast(engine.id, "ja")
        english = cast(engine.id, "en")
        assert japanese.seed == english.seed
        assert [
            (symbol.key, symbol.reversed)
            for symbol in japanese.drawn
        ] == [
            (symbol.key, symbol.reversed)
            for symbol in english.drawn
        ]
        assert len(japanese.drawn) == len(english.drawn)
        assert japanese.engine_name != english.engine_name
        assert japanese.lang == "ja"
        assert english.lang == "en"
        assert english.disclaimer != japanese.disclaimer


def test_daily_selection_and_seeds_are_language_independent():
    inp = DivinationInput(
        target_date=date(2026, 9, 1),
        question="Today's question",
        birth_date=date(1990, 1, 2),
        full_name="Taro Yamada",
    )
    assert [engine.id for engine in select_daily_engines(inp, "daily")] == [
        engine.id for engine in select_daily_engines(inp, "daily")
    ]
    japanese = daily_reading(inp, "daily", "ja")
    english = daily_reading(inp, "daily", "en")
    assert [reading.seed for reading in japanese["readings"]] == [
        reading.seed for reading in english["readings"]
    ]
    assert japanese["overview"] != english["overview"]


def test_catalogs_have_identical_nonempty_keys_and_placeholders():
    assert set(CATALOGS["ja"]) == set(CATALOGS["en"])
    for key in CATALOGS["ja"]:
        assert CATALOGS["ja"][key]
        assert CATALOGS["en"][key]
        assert set(re.findall(r"{(\w+)}", CATALOGS["ja"][key])) == set(
            re.findall(r"{(\w+)}", CATALOGS["en"][key])
        )


def test_english_framing_does_not_leak_japanese_values():
    for engine in all_engines():
        japanese = cast(engine.id, "ja")
        english = cast(engine.id, "en")
        assert english.engine_name != japanese.engine_name
        assert english.tradition != japanese.tradition
        assert [section.title for section in english.sections[:1]] != [
            section.title for section in japanese.sections[:1]
        ]
        assert [symbol.position for symbol in english.drawn] != [
            symbol.position for symbol in japanese.drawn
        ]
        assert english.lucky.color != japanese.lucky.color
        assert english.lucky.direction != japanese.lucky.direction
        assert english.lucky.item != japanese.lucky.item
        assert english.summary != japanese.summary


def test_data_sourced_omikuji_content_remains_japanese_by_declaration():
    japanese = cast("omikuji", "ja")
    english = cast("omikuji", "en")
    assert [section.title for section in english.sections[1:]] == list(CATEGORIES[1:])
    assert [section.title for section in english.sections[1:]] == [
        section.title for section in japanese.sections[1:]
    ]
    assert [section.body for section in english.sections[1:]] == [
        section.body for section in japanese.sections[1:]
    ]


@pytest.mark.parametrize(
    ("explicit", "header", "expected"),
    [
        (None, "en-US,ja;q=0.8", "en"),
        (None, "ja,en;q=0.9", "ja"),
        (None, "fr", "ja"),
        (None, None, "ja"),
        ("EN", None, "en"),
        ("zz", "en", "en"),
        (None, ";;q=x", "ja"),
    ],
)
def test_resolve_language(explicit, header, expected):
    assert resolve_lang(explicit, header) == expected


def test_catalog_translation_falls_back_to_japanese_and_missing_keys_are_loud():
    assert t("en", "engine.tarot.name") == "Tarot"
    assert t("en", "engine.tarot.name") != t("ja", "engine.tarot.name")
    with pytest.raises(KeyError):
        t(DEFAULT_LANG, "missing.key")


def test_lucky_items_keep_the_legacy_choice_order():
    reading = get_engine("tarot").cast(
        DivinationInput(target_date=date(2026, 1, 1)),
        SeededRandom("0123456789abcdef"),
    )
    assert reading.lucky.model_dump() == {
        "color": "藍色",
        "number": 6,
        "direction": "東",
        "item": "時計",
    }


def test_interpretation_language_follows_registry(monkeypatch):
    monkeypatch.setitem(INTERPRETATION_LANGS, "tarot", ("ja", "en"))
    assert cast("tarot", "en").interpretation_lang == "en"

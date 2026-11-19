import re
from datetime import date

import pytest

from app.divination.base import DivinationInput
from app.divination.data.en import TEXTS as EN_TEXTS
from app.divination.engines._common import first_sentence
from app.divination.interpretation import (
    TRANSLATABLE_KEYS_BY_ENGINE,
    interpretation_langs,
)
from app.divination.registry import all_engines, get_engine
from app.divination.seed import SeededRandom, build_seed
from app.i18n import CATALOGS, DEFAULT_LANG, resolve_lang, t

CJK = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")


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


def test_interpretation_translation_keys_are_covered_and_nonempty():
    for engine_id, texts in EN_TEXTS.items():
        keys = TRANSLATABLE_KEYS_BY_ENGINE[engine_id]
        assert keys <= texts.keys()
        assert all(texts[key] for key in keys)
        assert all(not CJK.search(value) for value in texts.values())


def test_interpretation_language_coverage():
    assert all(interpretation_langs(engine.id) == ("ja", "en") for engine in all_engines())


def test_english_data_casts_contain_no_cjk():
    for engine_id in (engine.id for engine in all_engines()):
        reading = cast(engine_id, "en")
        assert not CJK.search(reading.summary)
        assert all(not CJK.search(section.body) for section in reading.sections)
        assert all(not CJK.search(section.title) for section in reading.sections)
        assert all(not CJK.search(symbol.name) for symbol in reading.drawn)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("日本語の一文。次の文です。", "日本語の一文"),
        ("The first sentence. The next sentence.", "The first sentence"),
        ("No terminator", "No terminator"),
    ],
)
def test_first_sentence(text, expected):
    assert first_sentence(text) == expected


def test_lucky_items_keep_a_fixed_choice_order():
    # スコア乱数削除で一度変わった期待値であり、再変更はラッキーアイテムの非互換を示す。
    reading = get_engine("tarot").cast(
        DivinationInput(target_date=date(2026, 1, 1)),
        SeededRandom("0123456789abcdef"),
    )
    assert reading.lucky.model_dump() == {
        "color": "白色",
        "number": 2,
        "direction": "南",
        "item": "ノート",
    }


def test_interpretation_language_follows_registry(monkeypatch):
    monkeypatch.setitem(TRANSLATABLE_KEYS_BY_ENGINE, "tarot", frozenset({"the-fool.name"}))
    assert cast("tarot", "en").interpretation_lang == "en"


def test_interpretation_language_falls_back_when_translation_is_incomplete(
    monkeypatch,
):
    monkeypatch.setitem(
        TRANSLATABLE_KEYS_BY_ENGINE,
        "tarot",
        frozenset({"missing.name"}),
    )
    assert interpretation_langs("tarot") == ("ja",)
    assert cast("tarot", "en").interpretation_lang == "ja"
    assert interpretation_langs("unknown") == ("ja",)

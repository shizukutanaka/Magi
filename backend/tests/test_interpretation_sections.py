import re
from datetime import date

from app.divination.base import DivinationInput
from app.divination.data.runes import RUNES
from app.divination.data.tarot import CARDS
from app.divination.registry import get_engine
from app.divination.seed import SeededRandom, build_seed
from app.divination.service import cast_reading

CJK = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")


def reading_input(**kwargs):
    return DivinationInput(
        target_date=date(2026, 9, 1),
        question="仕事の方向を考えたい",
        **kwargs,
    )


def test_tarot_three_card_sections_follow_drawn_positions_and_meanings():
    inp = reading_input(options={"spread": "three-card"})
    reading = get_engine("tarot").cast(
        inp,
        SeededRandom(build_seed("sections", "tarot", inp)),
        "ja",
    )
    cards = {card.key: card for card in CARDS}

    assert [section.title for section in reading.sections[:-1]] == [
        symbol.position for symbol in reading.drawn
    ]
    assert reading.sections[-1].title == "助言"
    assert [section.body for section in reading.sections[:-1]] == [
        cards[symbol.key].reversed_meaning
        if symbol.reversed
        else cards[symbol.key].upright_meaning
        for symbol in reading.drawn
    ]


def test_tarot_celtic_cross_interprets_all_ten_cards():
    inp = reading_input(options={"spread": "celtic-cross"})
    reading = get_engine("tarot").cast(
        inp,
        SeededRandom(build_seed("celtic", "tarot", inp)),
        "ja",
    )

    assert len(reading.drawn) == 10
    assert len(reading.sections) == 11
    assert [section.title for section in reading.sections[:-1]] == [
        symbol.position for symbol in reading.drawn
    ]
    assert reading.sections[-1].title == "助言"


def test_runes_interpret_all_three_positions_and_reversals():
    inp = reading_input()
    reading = get_engine("runes").cast(
        inp,
        SeededRandom(build_seed("sections", "runes", inp)),
        "ja",
    )
    runes = {rune.key: rune for rune in RUNES}

    assert [section.title for section in reading.sections[:-1]] == [
        symbol.position for symbol in reading.drawn
    ]
    assert reading.sections[-1].title == "助言"
    assert [section.body for section in reading.sections[:-1]] == [
        runes[symbol.key].reversed_meaning
        if symbol.reversed
        else runes[symbol.key].meaning
        for symbol in reading.drawn
    ]
    reversed_index = next(
        index for index, symbol in enumerate(reading.drawn) if symbol.reversed
    )
    reversed_symbol = reading.drawn[reversed_index]
    assert reading.sections[reversed_index].body == runes[reversed_symbol.key].reversed_meaning


def test_tarot_and_rune_position_meanings_vary_across_draws():
    tarot_bodies = [set() for _ in range(3)]
    rune_bodies = [set() for _ in range(3)]
    for index in range(150):
        tarot_input = reading_input(options={"spread": "three-card"})
        tarot = get_engine("tarot").cast(
            tarot_input,
            SeededRandom(build_seed(f"variation-{index}", "tarot", tarot_input)),
            "ja",
        )
        runes_input = reading_input()
        runes = get_engine("runes").cast(
            runes_input,
            SeededRandom(build_seed(f"variation-{index}", "runes", runes_input)),
            "ja",
        )
        for position in range(3):
            tarot_bodies[position].add(tarot.sections[position].body)
            rune_bodies[position].add(runes.sections[position].body)

    assert all(len(bodies) >= 20 for bodies in tarot_bodies)
    assert all(len(bodies) >= 20 for bodies in rune_bodies)


def test_english_tarot_and_rune_sections_are_localized():
    for engine_id, options in (("tarot", {"spread": "three-card"}), ("runes", {})):
        inp = reading_input(options=options)
        reading = get_engine(engine_id).cast(
            inp,
            SeededRandom(build_seed(f"english-{engine_id}", engine_id, inp)),
            "en",
        )
        assert all(not CJK.search(section.title) for section in reading.sections)
        assert all(not CJK.search(section.body) for section in reading.sections)


def test_cast_reading_keeps_question_focus_section():
    reading = cast_reading(
        "tarot",
        reading_input(options={"spread": "three-card"}),
        "focus-test",
    )
    assert reading.sections[1].title == "問いについて（仕事）"
    assert reading.sections[1].body

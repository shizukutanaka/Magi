from app.divination.data.iching import CARDS as HEXAGRAMS
from app.divination.data.mayan import GALACTIC_TONES, SOLAR_SEALS
from app.divination.data.runes import RUNES
from app.divination.data.tarot import CARDS


def test_tarot_data_integrity():
    assert len(CARDS) == 78
    assert len({card.key for card in CARDS}) == 78
    assert len({card.upright_meaning for card in CARDS}) == 78
    assert len({card.reversed_meaning for card in CARDS}) == 78
    assert all(len(card.upright_keywords) == 3 and len(card.reversed_keywords) == 3 for card in CARDS)
    assert all(len(card.upright_meaning) >= 15 and len(card.reversed_meaning) >= 15 for card in CARDS)


def test_iching_data_integrity():
    assert {card.number for card in HEXAGRAMS} == set(range(1, 65))
    assert len({card.judgment for card in HEXAGRAMS}) == 64
    assert len({card.interpretation for card in HEXAGRAMS}) == 64
    assert all(len(card.judgment) >= 15 and len(card.interpretation) >= 15 for card in HEXAGRAMS)
    assert all(card.name_ja not in card.judgment and card.name_ja not in card.interpretation for card in HEXAGRAMS)
    assert len({card.judgment.replace(card.name_ja, "") for card in HEXAGRAMS}) == 64


def test_rune_data_integrity():
    assert len(RUNES) == 24
    assert len({rune.key for rune in RUNES}) == 24
    assert len({rune.meaning for rune in RUNES}) == 24
    assert all(len(rune.meaning) >= 15 and len(rune.reversed_meaning) >= 15 for rune in RUNES)


def test_other_data_integrity():
    assert len(SOLAR_SEALS) == 20
    assert len(GALACTIC_TONES) == 13

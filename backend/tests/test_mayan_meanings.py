from datetime import date, timedelta

from app.divination.base import DivinationInput
from app.divination.data.en.mayan import TEXTS as EN_MAYAN
from app.divination.data.mayan import (
    GALACTIC_TONE_MEANINGS,
    GALACTIC_TONES,
    SOLAR_SEAL_MEANINGS,
    SOLAR_SEALS,
)
from app.divination.service import cast_reading
from tests.test_i18n import CJK

TONE_TITLE = "銀河の音"
SEAL_TITLE = "太陽の紋章"


def _section(reading, title):
    return next(section.body for section in reading.sections if section.title == title)


def test_japanese_meanings_are_complete_and_distinct():
    assert len(SOLAR_SEAL_MEANINGS) == len(SOLAR_SEALS)
    assert len(GALACTIC_TONE_MEANINGS) == len(GALACTIC_TONES)
    assert all(meaning for meaning in SOLAR_SEAL_MEANINGS + GALACTIC_TONE_MEANINGS)
    assert len(set(SOLAR_SEAL_MEANINGS)) == len(SOLAR_SEALS)
    assert len(set(GALACTIC_TONE_MEANINGS)) == len(GALACTIC_TONES)


def test_english_meanings_are_complete_and_distinct():
    seals = [EN_MAYAN[f"solar_seal.{index}.meaning"] for index in range(len(SOLAR_SEALS))]
    tones = [EN_MAYAN[f"galactic_tone.{index}.meaning"] for index in range(len(GALACTIC_TONES))]
    assert all(seals) and all(tones)
    assert len(set(seals)) == len(SOLAR_SEALS)
    assert len(set(tones)) == len(GALACTIC_TONES)


def test_sections_vary_with_the_drawn_kin():
    tones = set()
    seals = set()
    for offset in range(260):
        inp = DivinationInput(
            target_date=date(2026, 9, 1),
            birth_date=date(1990, 1, 1) + timedelta(offset),
        )
        reading = cast_reading("mayan", inp, "mayan-variation")
        tones.add(_section(reading, TONE_TITLE))
        seals.add(_section(reading, SEAL_TITLE))
    assert len(tones) == len(GALACTIC_TONES)
    assert len(seals) == len(SOLAR_SEALS)


def test_english_reading_sections_have_no_japanese_characters():
    inp = DivinationInput(target_date=date(2026, 9, 1), birth_date=date(1990, 5, 17))
    reading = cast_reading("mayan", inp, "mayan-english", "en")
    assert all(not CJK.search(section.body) for section in reading.sections)
    assert all(not CJK.search(section.title) for section in reading.sections)

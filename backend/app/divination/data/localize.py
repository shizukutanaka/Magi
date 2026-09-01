"""Localization helpers for interpretation data."""

from app.divination.data.en import TEXTS as EN_TEXTS
from app.i18n import Lang


def dt(lang: Lang, engine_id: str, key: str, japanese: str) -> str:
    """Return the localized data string, falling back to the Japanese source."""
    if lang == "ja":
        return japanese
    return EN_TEXTS.get(engine_id, {}).get(key, japanese)

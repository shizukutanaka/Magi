"""Interpretation-language coverage derived from source and locale data."""

from app.divination.data.astrology import TRANSLATABLE_KEYS as ASTROLOGY_KEYS
from app.divination.data.bazi import TRANSLATABLE_KEYS as BAZI_KEYS
from app.divination.data.en import TEXTS as EN_TEXTS
from app.divination.data.geomancy import TRANSLATABLE_KEYS as GEOMANCY_KEYS
from app.divination.data.iching import TRANSLATABLE_KEYS as ICHING_KEYS
from app.divination.data.mayan import TRANSLATABLE_KEYS as MAYAN_KEYS
from app.divination.data.numerology import TRANSLATABLE_KEYS as NUMEROLOGY_KEYS
from app.divination.data.omikuji import TRANSLATABLE_KEYS as OMIKUJI_KEYS
from app.divination.data.runes import TRANSLATABLE_KEYS as RUNES_KEYS
from app.divination.data.tarot import TRANSLATABLE_KEYS as TAROT_KEYS

TRANSLATABLE_KEYS_BY_ENGINE: dict[str, frozenset[str]] = {
    "tarot": TAROT_KEYS,
    "iching": ICHING_KEYS,
    "runes": RUNES_KEYS,
    "geomancy": GEOMANCY_KEYS,
    "omikuji": OMIKUJI_KEYS,
    "astrology": ASTROLOGY_KEYS,
    "numerology": NUMEROLOGY_KEYS,
    "bazi": BAZI_KEYS,
    "mayan": MAYAN_KEYS,
}


def interpretation_langs(engine_id: str) -> tuple[str, ...]:
    keys = TRANSLATABLE_KEYS_BY_ENGINE[engine_id]
    covered = bool(keys) and keys <= EN_TEXTS.get(engine_id, {}).keys()
    return ("ja", "en") if covered else ("ja",)

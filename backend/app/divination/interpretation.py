"""Interpretation-language coverage derived from source and locale data."""

from app.divination.data.en import TEXTS as EN_TEXTS
from app.divination.data.tarot import TRANSLATABLE_KEYS as TAROT_KEYS

TRANSLATABLE_KEYS_BY_ENGINE: dict[str, frozenset[str]] = {
    "tarot": TAROT_KEYS,
}


def interpretation_langs(engine_id: str) -> tuple[str, ...]:
    """Empty keys mean the engine is fully catalog-driven."""
    keys = TRANSLATABLE_KEYS_BY_ENGINE.get(engine_id)
    if keys is None:
        return ("ja",)
    covered = keys <= EN_TEXTS.get(engine_id, {}).keys()
    return ("ja", "en") if covered else ("ja",)

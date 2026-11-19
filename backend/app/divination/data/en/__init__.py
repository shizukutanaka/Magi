"""English interpretation data by divination system."""

from app.divination.data.en.tarot import TEXTS as TAROT_TEXTS

TEXTS: dict[str, dict[str, str]] = {
    "tarot": TAROT_TEXTS,
}

"""Language negotiation and presentation strings."""

from typing import Literal

from app.i18n.en import MESSAGES as EN_MESSAGES
from app.i18n.ja import MESSAGES as JA_MESSAGES

Lang = Literal["ja", "en"]
SUPPORTED_LANGS: tuple[Lang, ...] = ("ja", "en")
DEFAULT_LANG: Lang = "ja"
CATALOGS: dict[Lang, dict[str, str]] = {"ja": JA_MESSAGES, "en": EN_MESSAGES}


def _primary(value: str) -> str:
    return value.strip().lower().split("-", 1)[0]


def resolve_lang(explicit: str | None, accept_language: str | None) -> Lang:
    """Resolve an explicit language, then an Accept-Language header."""
    if explicit:
        primary = _primary(explicit)
        if primary in SUPPORTED_LANGS:
            return primary
    candidates: list[tuple[float, int, str]] = []
    for index, token in enumerate((accept_language or "").split(",")):
        parts = token.strip().split(";")
        primary = _primary(parts[0])
        quality = 1.0
        for parameter in parts[1:]:
            name, _, value = parameter.strip().partition("=")
            if name.lower() == "q":
                try:
                    quality = float(value)
                except ValueError:
                    quality = 0.0
        if primary in SUPPORTED_LANGS and 0 <= quality <= 1:
            candidates.append((quality, -index, primary))
    if candidates:
        candidates.sort(reverse=True)
        return candidates[0][2]
    return DEFAULT_LANG


def t(lang: Lang, key: str, /, **params: object) -> str:
    """Translate a catalog key, falling back to Japanese when needed."""
    template = CATALOGS[lang].get(key, JA_MESSAGES.get(key))
    if template is None:
        raise KeyError(key)
    return template.format(**params)

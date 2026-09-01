"""Built-in divination engines."""

from importlib import import_module

for _module_name in (
    "tarot",
    "iching",
    "runes",
    "omikuji",
    "astrology",
    "numerology",
    "bazi",
    "mayan",
    "geomancy",
):
    import_module(f"{__name__}.{_module_name}")

__all__ = ["astrology", "bazi", "geomancy", "iching", "mayan", "numerology", "omikuji", "runes", "tarot"]

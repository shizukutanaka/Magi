"""English interpretation data by divination system."""

from app.divination.data.en.astrology import TEXTS as ASTROLOGY_TEXTS
from app.divination.data.en.bazi import TEXTS as BAZI_TEXTS
from app.divination.data.en.geomancy import TEXTS as GEOMANCY_TEXTS
from app.divination.data.en.mayan import TEXTS as MAYAN_TEXTS
from app.divination.data.en.omikuji import TEXTS as OMIKUJI_TEXTS
from app.divination.data.en.runes import TEXTS as RUNES_TEXTS

TEXTS: dict[str, dict[str, str]] = {
    "astrology": ASTROLOGY_TEXTS,
    "bazi": BAZI_TEXTS,
    "runes": RUNES_TEXTS,
    "geomancy": GEOMANCY_TEXTS,
    "omikuji": OMIKUJI_TEXTS,
    "mayan": MAYAN_TEXTS,
}

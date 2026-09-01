"""Sun-sign, moon-phase, and weekday-ruler astrology without ephemeris."""

from datetime import date

from app.divination.base import DivinationEngine, DivinationInput, DrawnSymbol, ReadingSection
from app.divination.data.astrology import MOON_PHASES, WEEKDAY_RULERS, ZODIAC
from app.divination.engines._common import finish
from app.divination.registry import register
from app.divination.seed import SeededRandom
from app.i18n import Lang, t


def sun_sign(birth_date: date) -> tuple[str, str, str]:
    for name, start, end, element, quality in ZODIAC:
        if (birth_date.month, birth_date.day) >= start and (birth_date.month, birth_date.day) <= end:
            return name, element, quality
    return "やぎ座", "土", "堅実さ"


class AstrologyEngine:
    id = "astrology"
    name = "西洋占星術"
    tradition = "西洋"
    required_fields = frozenset({"birth_date"})
    default_options: dict[str, str] = {}

    def cast(self, inp: DivinationInput, rng: SeededRandom, lang: Lang = "ja"):
        if inp.birth_date is None:
            raise ValueError("birth_date is required")
        sign, element, quality = sun_sign(inp.birth_date)
        epoch = date(2000, 1, 6)
        days = (inp.target_date - epoch).days
        phase = MOON_PHASES[int((days % 29.530588853) / (29.530588853 / 8))]
        ruler = WEEKDAY_RULERS[inp.target_date.weekday()]
        drawn = [
            DrawnSymbol(key=sign, name=sign, position=t(lang, "position.astrology.sun_sign"), image_hint=f"astrology/{sign}"),
            DrawnSymbol(key=phase, name=phase, position=t(lang, "position.astrology.moon_phase"), image_hint=f"astrology/{phase}"),
            DrawnSymbol(key=ruler, name=ruler, position=t(lang, "position.astrology.weekday_ruler"), image_hint=f"astrology/{ruler}"),
        ]
        return finish(
            self.id, t(lang, "engine.astrology.name"), t(lang, "engine.astrology.tradition"), rng.seed, drawn,
            t(lang, "summary.astrology", sign=sign, quality=quality, phase=phase, ruler=ruler),
            [
                ReadingSection(title=t(lang, "section.astrology.sun_sign"), body=t(lang, "body.astrology.sun_sign", sign=sign, element=element, quality=quality)),
                ReadingSection(title=t(lang, "section.astrology.moon_phase"), body=t(lang, "body.astrology.moon_phase", phase=phase)),
                ReadingSection(title=t(lang, "section.astrology.weekday_ruler"), body=t(lang, "body.astrology.weekday_ruler", ruler=ruler)),
                ReadingSection(title=t(lang, "section.guidance"), body=t(lang, "body.astrology.guidance")),
            ],
            rng.randint(45, 93), rng, lang,
        )


engine: DivinationEngine = register(AstrologyEngine())

"""Sun-sign, moon-phase, and weekday-ruler astrology without ephemeris."""

from datetime import date

from app.divination.base import DivinationEngine, DivinationInput, DrawnSymbol, ReadingSection
from app.divination.data.astrology import MOON_PHASES, WEEKDAY_RULERS, ZODIAC
from app.divination.data.localize import dt
from app.divination.engines._common import finish
from app.divination.registry import register
from app.divination.seed import SeededRandom
from app.i18n import Lang, t

SYNODIC_MONTH = 29.530588853


def sun_sign(birth_date: date) -> int:
    for index, (_, start, end, _, _) in enumerate(ZODIAC):
        if (birth_date.month, birth_date.day) >= start and (birth_date.month, birth_date.day) <= end:
            return index
    return 0


class AstrologyEngine:
    id = "astrology"
    name = "西洋占星術"
    tradition = "西洋"
    required_fields = frozenset({"birth_date"})
    default_options: dict[str, str] = {}

    def cast(self, inp: DivinationInput, rng: SeededRandom, lang: Lang = "ja"):
        if inp.birth_date is None:
            raise ValueError("birth_date is required")
        zodiac_index = sun_sign(inp.birth_date)
        sign, _, _, element, quality = ZODIAC[zodiac_index]
        epoch = date(2000, 1, 6)
        days = (inp.target_date - epoch).days
        # 8つの名前は各位相を中心とする区間なので、半ビンずらして分類する
        phase_index = int(
            ((days + SYNODIC_MONTH / 16) % SYNODIC_MONTH) / (SYNODIC_MONTH / 8)
        ) % 8
        phase = MOON_PHASES[phase_index]
        ruler_index = inp.target_date.weekday()
        ruler = WEEKDAY_RULERS[ruler_index]
        localized_sign = dt(lang, self.id, f"zodiac.{zodiac_index}.name", sign)
        localized_element = dt(
            lang, self.id, f"zodiac.{zodiac_index}.element", element
        )
        localized_quality = dt(
            lang, self.id, f"zodiac.{zodiac_index}.quality", quality
        )
        localized_phase = dt(lang, self.id, f"moon_phase.{phase_index}", phase)
        localized_ruler = dt(lang, self.id, f"weekday.{ruler_index}", ruler)
        drawn = [
            DrawnSymbol(key=sign, name=localized_sign, position=t(lang, "position.astrology.sun_sign")),
            DrawnSymbol(key=phase, name=localized_phase, position=t(lang, "position.astrology.moon_phase")),
            DrawnSymbol(key=ruler, name=localized_ruler, position=t(lang, "position.astrology.weekday_ruler")),
        ]
        return finish(
            self.id, t(lang, "engine.astrology.name"), t(lang, "engine.astrology.tradition"), rng.seed, drawn,
            t(lang, "summary.astrology", sign=localized_sign, quality=localized_quality, phase=localized_phase, ruler=localized_ruler),
            [
                ReadingSection(title=t(lang, "section.astrology.sun_sign"), body=t(lang, "body.astrology.sun_sign", sign=localized_sign, element=localized_element, quality=localized_quality)),
                ReadingSection(title=t(lang, "section.astrology.moon_phase"), body=t(lang, "body.astrology.moon_phase", phase=localized_phase)),
                ReadingSection(title=t(lang, "section.astrology.weekday_ruler"), body=t(lang, "body.astrology.weekday_ruler", ruler=localized_ruler)),
                ReadingSection(title=t(lang, "section.guidance"), body=t(lang, "body.astrology.guidance")),
            ],
            rng.randint(45, 93), rng, lang,
        )


engine: DivinationEngine = register(AstrologyEngine())

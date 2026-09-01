"""Weighted Japanese omikuji engine."""

from app.divination.base import DivinationEngine, DivinationInput, DrawnSymbol, ReadingSection
from app.divination.data.localize import dt
from app.divination.data.omikuji import CATEGORIES, GRADES
from app.divination.engines._common import finish
from app.divination.registry import register
from app.divination.seed import SeededRandom
from app.i18n import Lang, t


class OmikujiEngine:
    id = "omikuji"
    name = "おみくじ"
    tradition = "日本"
    required_fields = frozenset()
    default_options: dict[str, str] = {}

    def cast(self, inp: DivinationInput, rng: SeededRandom, lang: Lang = "ja"):
        grade_key = rng.pick([row[0] for row in GRADES for _ in range(row[2])])
        row = next(row for row in GRADES if row[0] == grade_key)
        _, grade, _, *japanese_advice = row
        advice = dict(zip(CATEGORIES, japanese_advice, strict=True))
        grade_name = dt(lang, self.id, f"{grade_key}.name", grade)
        localized_advice = {
            category: dt(lang, self.id, f"{grade_key}.category.{index}", text)
            for index, (category, text) in enumerate(advice.items())
        }
        drawn = [DrawnSymbol(key=grade_key, name=grade_name, position=t(lang, "position.omikuji.drawn"), image_hint=f"omikuji/{grade_key}")]
        sections = [ReadingSection(title=t(lang, "section.overall"), body=t(lang, "body.omikuji.overall", grade=grade_name, wish=localized_advice["願望"]))]
        sections.extend(
            ReadingSection(title=title, body=localized_advice[title])
            for title in advice
            if title != "願望"
        )
        return finish(
            self.id, t(lang, "engine.omikuji.name"), t(lang, "engine.omikuji.tradition"), rng.seed, drawn,
            t(lang, "summary.omikuji", grade=grade_name, wish=localized_advice["願望"]), sections, rng.randint(35, 98), rng, lang,
        )


engine: DivinationEngine = register(OmikujiEngine())

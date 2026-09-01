"""Weighted Japanese omikuji engine."""

from app.divination.base import DivinationEngine, DivinationInput, DrawnSymbol, ReadingSection
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
        grade = rng.pick([grade for grade, weight, *_ in GRADES for _ in range(weight)])
        row = next(row for row in GRADES if row[0] == grade)
        advice = dict(zip(CATEGORIES, row[2:], strict=True))
        drawn = [DrawnSymbol(key=grade.lower(), name=grade, position=t(lang, "position.omikuji.drawn"), image_hint=f"omikuji/{grade.lower()}")]
        sections = [ReadingSection(title=t(lang, "section.overall"), body=t(lang, "body.omikuji.overall", grade=grade, wish=advice["願望"]))]
        sections.extend(ReadingSection(title=title, body=text) for title, text in advice.items() if title != "願望")
        return finish(
            self.id, t(lang, "engine.omikuji.name"), t(lang, "engine.omikuji.tradition"), rng.seed, drawn,
            t(lang, "summary.omikuji", grade=grade, wish=advice["願望"]), sections, rng.randint(35, 98), rng, lang,
        )


engine: DivinationEngine = register(OmikujiEngine())

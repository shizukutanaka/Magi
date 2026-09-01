"""Weighted Japanese omikuji engine."""

from app.divination.base import DivinationEngine, DivinationInput, DrawnSymbol, ReadingSection
from app.divination.data.omikuji import CATEGORIES, GRADES
from app.divination.engines._common import finish
from app.divination.registry import register
from app.divination.seed import SeededRandom


class OmikujiEngine:
    id = "omikuji"
    name = "おみくじ"
    tradition = "日本"
    required_fields = frozenset()

    def cast(self, inp: DivinationInput, rng: SeededRandom):
        grade = rng.pick([grade for grade, weight, *_ in GRADES for _ in range(weight)])
        row = next(row for row in GRADES if row[0] == grade)
        advice = dict(zip(CATEGORIES, row[2:], strict=True))
        drawn = [DrawnSymbol(key=grade.lower(), name=grade, position="本籤")]
        sections = [ReadingSection(title="総合", body=f"運勢は{grade}。{advice['願望']}")]
        sections.extend(ReadingSection(title=title, body=text) for title, text in advice.items() if title != "願望")
        return finish(
            self.id, self.name, self.tradition, rng.seed, drawn,
            f"{grade}。{advice['願望']}", sections, rng.randint(35, 98), rng,
        )


engine: DivinationEngine = register(OmikujiEngine())

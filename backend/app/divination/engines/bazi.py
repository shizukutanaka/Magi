"""Abbreviated BaZi engine based on fixed sexagenary-cycle references."""

from datetime import date

from app.divination.base import DivinationEngine, DivinationInput, DrawnSymbol, ReadingSection
from app.divination.data.bazi import ANIMALS, BRANCHES, COMPATIBILITY, ELEMENTS, STEMS
from app.divination.engines._common import finish
from app.divination.registry import register
from app.divination.seed import SeededRandom


def _cycle_index(year: int) -> int:
    return (year - 1984) % 60


def _day_cycle(birth_date: date) -> int:
    # A fixed Julian-day-compatible anchor: 1949-10-01 is 甲子 (index 0).
    return (birth_date - date(1949, 10, 1)).days % 60


class BaziEngine:
    id = "bazi"
    name = "干支・四柱推命（略式）"
    tradition = "中国"
    required_fields = frozenset({"birth_date"})

    def cast(self, inp: DivinationInput, rng: SeededRandom):
        if inp.birth_date is None:
            raise ValueError("birth_date is required")
        year_index = _cycle_index(inp.birth_date.year)
        day_index = _day_cycle(inp.birth_date)
        year_stem, year_branch = STEMS[year_index % 10], BRANCHES[year_index % 12]
        day_stem, day_branch = STEMS[day_index % 10], BRANCHES[day_index % 12]
        drawn = [
            DrawnSymbol(key=f"year-{year_index}", name=f"{year_stem}{year_branch}", position="年柱"),
            DrawnSymbol(key=f"day-{day_index}", name=f"{day_stem}{day_branch}", position="日柱"),
        ]
        return finish(
            self.id, self.name, self.tradition, rng.seed, drawn,
            f"略式鑑定では、年柱{year_stem}{year_branch}と日柱{day_stem}{day_branch}から流れを読みます。",
            [
                ReadingSection(title="年柱", body=f"{year_stem}{year_branch}は{ANIMALS[year_index % 12]}（{ELEMENTS[year_index % 10]}）の気を帯びます。"),
                ReadingSection(title="日柱", body=f"{day_stem}{day_branch}は日々の自分らしさを表し、{ELEMENTS[day_index % 10]}の性質を示します。"),
                ReadingSection(title="相性", body=COMPATIBILITY[year_branch]),
                ReadingSection(title="助言", body="本来の四柱推命を簡略化した読みです。季節や出生時刻も含めた判断は専門家に委ねましょう。"),
            ],
            rng.randint(38, 91), rng,
        )


engine: DivinationEngine = register(BaziEngine())

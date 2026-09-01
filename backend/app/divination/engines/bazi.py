"""Abbreviated BaZi engine based on fixed sexagenary-cycle references."""

from datetime import date

from app.divination.base import DivinationEngine, DivinationInput, DrawnSymbol, ReadingSection
from app.divination.data.bazi import ANIMALS, BRANCHES, COMPATIBILITY, ELEMENTS, STEMS
from app.divination.engines._common import finish
from app.divination.registry import register
from app.divination.seed import SeededRandom
from app.i18n import Lang, t


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
    default_options: dict[str, str] = {}

    def cast(self, inp: DivinationInput, rng: SeededRandom, lang: Lang = "ja"):
        if inp.birth_date is None:
            raise ValueError("birth_date is required")
        year_index = _cycle_index(inp.birth_date.year)
        day_index = _day_cycle(inp.birth_date)
        year_stem, year_branch = STEMS[year_index % 10], BRANCHES[year_index % 12]
        day_stem, day_branch = STEMS[day_index % 10], BRANCHES[day_index % 12]
        drawn = [
            DrawnSymbol(
                key=f"year-{year_index}",
                name=f"{year_stem}{year_branch}",
                position=t(lang, "position.bazi.year_pillar"),
                image_hint=f"bazi/year-{year_index}",
            ),
            DrawnSymbol(
                key=f"day-{day_index}",
                name=f"{day_stem}{day_branch}",
                position=t(lang, "position.bazi.day_pillar"),
                image_hint=f"bazi/day-{day_index}",
            ),
        ]
        return finish(
            self.id, t(lang, "engine.bazi.name"), t(lang, "engine.bazi.tradition"), rng.seed, drawn,
            t(lang, "summary.bazi", year=f"{year_stem}{year_branch}", day=f"{day_stem}{day_branch}"),
            [
                ReadingSection(title=t(lang, "section.bazi.year_pillar"), body=t(lang, "body.bazi.year_pillar", pillar=f"{year_stem}{year_branch}", animal=ANIMALS[year_index % 12], element=ELEMENTS[year_index % 10])),
                ReadingSection(title=t(lang, "section.bazi.day_pillar"), body=t(lang, "body.bazi.day_pillar", pillar=f"{day_stem}{day_branch}", element=ELEMENTS[day_index % 10])),
                ReadingSection(title=t(lang, "section.bazi.compatibility"), body=COMPATIBILITY[year_branch]),
                ReadingSection(title=t(lang, "section.guidance"), body=t(lang, "body.bazi.guidance")),
            ],
            rng.randint(38, 91), rng, lang,
        )


engine: DivinationEngine = register(BaziEngine())

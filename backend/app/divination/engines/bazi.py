"""Abbreviated BaZi engine based on fixed sexagenary-cycle references."""

from datetime import date

from app.divination.base import DivinationEngine, DivinationInput, DrawnSymbol, ReadingSection
from app.divination.data.bazi import ANIMALS, BRANCHES, COMPATIBILITY, ELEMENTS, STEMS
from app.divination.data.localize import dt
from app.divination.engines._common import finish
from app.divination.registry import register
from app.divination.seed import SeededRandom
from app.i18n import Lang, t


def _cycle_index(year: int) -> int:
    return (year - 1984) % 60


def _day_cycle(birth_date: date) -> int:
    # A fixed Julian-day-compatible anchor: 1949-10-01 is 甲子 (index 0).
    return (birth_date - date(1949, 10, 1)).days % 60


def _localized_pillar(
    stem_index: int, branch_index: int, lang: Lang
) -> str:
    stem = dt(lang, "bazi", f"stem.{stem_index}", STEMS[stem_index])
    branch = dt(lang, "bazi", f"branch.{branch_index}", BRANCHES[branch_index])
    return t(lang, "format.bazi.pillar", stem=stem, branch=branch)


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
        year_stem_index, year_branch_index = year_index % 10, year_index % 12
        day_stem_index, day_branch_index = day_index % 10, day_index % 12
        year_branch = BRANCHES[year_branch_index]
        year_pillar = _localized_pillar(year_stem_index, year_branch_index, lang)
        day_pillar = _localized_pillar(day_stem_index, day_branch_index, lang)
        year_animal = dt(lang, self.id, f"animal.{year_index % 12}", ANIMALS[year_index % 12])
        year_element = dt(lang, self.id, f"element.{year_index % 10}", ELEMENTS[year_index % 10])
        day_element = dt(lang, self.id, f"element.{day_index % 10}", ELEMENTS[day_index % 10])
        compatibility = dt(
            lang,
            self.id,
            f"compatibility.{year_branch_index}",
            COMPATIBILITY[year_branch],
        )
        drawn = [
            DrawnSymbol(
                key=f"year-{year_index}",
                name=year_pillar,
                position=t(lang, "position.bazi.year_pillar"),
            ),
            DrawnSymbol(
                key=f"day-{day_index}",
                name=day_pillar,
                position=t(lang, "position.bazi.day_pillar"),
            ),
        ]
        return finish(
            self.id, t(lang, "engine.bazi.name"), t(lang, "engine.bazi.tradition"), rng.seed, drawn,
            t(lang, "summary.bazi", year=year_pillar, day=day_pillar),
            [
                ReadingSection(title=t(lang, "section.bazi.year_pillar"), body=t(lang, "body.bazi.year_pillar", pillar=year_pillar, animal=year_animal, element=year_element)),
                ReadingSection(title=t(lang, "section.bazi.day_pillar"), body=t(lang, "body.bazi.day_pillar", pillar=day_pillar, element=day_element)),
                ReadingSection(title=t(lang, "section.bazi.compatibility"), body=compatibility),
                ReadingSection(title=t(lang, "section.guidance"), body=t(lang, "body.bazi.guidance")),
            ],
            rng.randint(38, 91), rng, lang,
        )


engine: DivinationEngine = register(BaziEngine())

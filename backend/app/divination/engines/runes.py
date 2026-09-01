"""Elder Futhark three-rune engine."""

from app.divination.base import DivinationEngine, DivinationInput, DrawnSymbol, ReadingSection
from app.divination.data.localize import dt
from app.divination.data.runes import RUNES
from app.divination.engines._common import finish
from app.divination.registry import register
from app.divination.seed import SeededRandom
from app.i18n import Lang, t


class RunesEngine:
    id = "runes"
    name = "ルーン"
    tradition = "北欧"
    required_fields = frozenset()
    default_options: dict[str, str] = {}

    def cast(self, inp: DivinationInput, rng: SeededRandom, lang: Lang = "ja"):
        runes = rng.sample(RUNES, 3)
        drawn = []
        for rune, position_key in zip(runes, ("past", "present", "future"), strict=True):
            reversed_rune = rune.has_reversed and bool(rng.randint(0, 1))
            drawn.append(
                DrawnSymbol(
                    key=rune.key,
                    name=dt(lang, self.id, f"{rune.key}.name", rune.name_ja),
                    position=t(lang, f"position.runes.{position_key}"),
                    reversed=reversed_rune,
                )
            )
        first = runes[0]
        first_meaning = first.reversed_meaning if drawn[0].reversed else first.meaning
        first_meaning = dt(
            lang,
            self.id,
            f"{first.key}.reversed_meaning" if drawn[0].reversed else f"{first.key}.meaning",
            first_meaning,
        )
        return finish(
            self.id, t(lang, "engine.runes.name"), t(lang, "engine.runes.tradition"), rng.seed, drawn,
            t(lang, "summary.runes", name=drawn[0].name, meaning=first_meaning),
            [
                ReadingSection(title=t(lang, "section.overall"), body=first_meaning),
                ReadingSection(title=t(lang, "section.runes_flow"), body=t(lang, "body.runes.flow")),
                ReadingSection(title=t(lang, "section.relationship"), body=t(lang, "body.runes.relationship")),
                ReadingSection(title=t(lang, "section.guidance"), body=t(lang, "body.runes.guidance")),
            ],
            rng.randint(42, 94), rng, lang,
        )


engine: DivinationEngine = register(RunesEngine())

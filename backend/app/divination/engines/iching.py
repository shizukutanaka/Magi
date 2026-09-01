"""Six-coin I Ching engine."""

from app.divination.base import DivinationEngine, DivinationInput, DrawnSymbol, ReadingSection
from app.divination.data.iching import CARDS
from app.divination.data.localize import dt
from app.divination.engines._common import finish, first_sentence
from app.divination.registry import register
from app.divination.seed import SeededRandom
from app.i18n import Lang, t


class IChingEngine:
    id = "iching"
    name = "易経（周易）"
    tradition = "中国"
    required_fields = frozenset()
    default_options: dict[str, str] = {}

    def cast(self, inp: DivinationInput, rng: SeededRandom, lang: Lang = "ja"):
        lines = [sum(rng.randint(2, 3) for _ in range(3)) for _ in range(6)]
        number = sum((1 if line in (7, 9) else 0) << index for index, line in enumerate(lines)) + 1
        primary = CARDS[number - 1]
        changed_lines = [8 if line == 9 else 7 if line == 6 else line for line in lines]
        changed_number = sum((1 if line in (7, 9) else 0) << index for index, line in enumerate(changed_lines)) + 1
        changed = CARDS[changed_number - 1]
        primary_key = f"hex-{primary.number:02d}"
        changed_key = f"hex-{changed.number:02d}"
        primary_name = dt(lang, self.id, f"{primary_key}.name", primary.name_ja)
        primary_judgment = dt(
            lang, self.id, f"{primary_key}.judgment", primary.judgment
        )
        primary_interpretation = dt(
            lang, self.id, f"{primary_key}.interpretation", primary.interpretation
        )
        changed_name = dt(lang, self.id, f"{changed_key}.name", changed.name_ja)
        changed_interpretation = dt(
            lang,
            self.id,
            f"{changed_key}.interpretation",
            changed.interpretation,
        )
        drawn = [
            DrawnSymbol(
                key=f"hex-{primary.number:02d}",
                name=primary_name,
                position=t(lang, "position.iching.primary"),
            )
        ]
        if changed_number != number:
            drawn.append(
                DrawnSymbol(
                    key=f"hex-{changed.number:02d}",
                    name=changed_name,
                    position=t(lang, "position.iching.transformed"),
                )
            )
        return finish(
            self.id, t(lang, "engine.iching.name"), t(lang, "engine.iching.tradition"), rng.seed, drawn,
            t(
                lang,
                "summary.iching.primary",
                name=primary_name,
                meaning=first_sentence(primary_interpretation),
                change=t(lang, "body.iching.change", changed_name=changed_name) if changed_number != number else "",
            ),
            [
                ReadingSection(title=t(lang, "section.overall"), body=primary_interpretation),
                ReadingSection(title=t(lang, "section.iching.judgment"), body=primary_judgment),
                ReadingSection(title=t(lang, "section.iching.change"), body=changed_interpretation if changed_number != number else t(lang, "body.iching.no_change")),
                ReadingSection(title=t(lang, "section.practice"), body=t(lang, "body.iching.practice")),
            ],
            rng.randint(40, 92), rng, lang,
        )


engine: DivinationEngine = register(IChingEngine())

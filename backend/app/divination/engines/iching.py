"""Six-coin I Ching engine."""

from app.divination.base import DivinationEngine, DivinationInput, DrawnSymbol, ReadingSection
from app.divination.data.iching import CARDS
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
        drawn = [
            DrawnSymbol(
                key=f"hex-{primary.number:02d}",
                name=primary.name_ja,
                position=t(lang, "position.iching.primary"),
                image_hint=f"iching/hex-{primary.number:02d}",
            )
        ]
        if changed_number != number:
            drawn.append(
                DrawnSymbol(
                    key=f"hex-{changed.number:02d}",
                    name=changed.name_ja,
                    position=t(lang, "position.iching.transformed"),
                    image_hint=f"iching/hex-{changed.number:02d}",
                )
            )
        return finish(
            self.id, t(lang, "engine.iching.name"), t(lang, "engine.iching.tradition"), rng.seed, drawn,
            t(
                lang,
                "summary.iching.primary",
                name=primary.name_ja,
                meaning=first_sentence(primary.interpretation),
                change=t(lang, "body.iching.change", changed_name=changed.name_ja) if changed_number != number else "",
            ),
            [
                ReadingSection(title=t(lang, "section.overall"), body=primary.interpretation),
                ReadingSection(title=t(lang, "section.iching.judgment"), body=primary.judgment),
                ReadingSection(title=t(lang, "section.iching.change"), body=changed.interpretation if changed_number != number else t(lang, "body.iching.no_change")),
                ReadingSection(title=t(lang, "section.practice"), body=t(lang, "body.iching.practice")),
            ],
            rng.randint(40, 92), rng, lang,
        )


engine: DivinationEngine = register(IChingEngine())

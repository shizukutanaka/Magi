"""Geomancy engine based on a generated shield chart."""

from dataclasses import dataclass

from app.divination.base import DivinationEngine, DivinationInput, DrawnSymbol, ReadingSection
from app.divination.data.geomancy import FIGURES_BY_LINES, GeomancyFigure
from app.divination.data.localize import dt
from app.divination.engines._common import finish
from app.divination.registry import register
from app.divination.seed import SeededRandom
from app.i18n import Lang, t


@dataclass(frozen=True)
class ShieldChart:
    mothers: tuple[GeomancyFigure, ...]
    daughters: tuple[GeomancyFigure, ...]
    nieces: tuple[GeomancyFigure, ...]
    right_witness: GeomancyFigure
    left_witness: GeomancyFigure
    judge: GeomancyFigure


def add_figures(first: GeomancyFigure, second: GeomancyFigure) -> GeomancyFigure:
    lines = tuple(1 if (left + right) % 2 else 2 for left, right in zip(first.lines, second.lines, strict=True))
    return FIGURES_BY_LINES[lines]


def build_shield(rng: SeededRandom) -> ShieldChart:
    mothers = tuple(
        FIGURES_BY_LINES[
            tuple(1 if rng.randint(1, 16) % 2 else 2 for _ in range(4))
        ]
        for _ in range(4)
    )
    daughters = tuple(
        FIGURES_BY_LINES[tuple(mother.lines[index] for mother in mothers)]
        for index in range(4)
    )
    nieces = (
        add_figures(mothers[0], mothers[1]),
        add_figures(mothers[2], mothers[3]),
        add_figures(daughters[0], daughters[1]),
        add_figures(daughters[2], daughters[3]),
    )
    right_witness = add_figures(nieces[0], nieces[1])
    left_witness = add_figures(nieces[2], nieces[3])
    judge = add_figures(right_witness, left_witness)
    return ShieldChart(mothers, daughters, nieces, right_witness, left_witness, judge)


class GeomancyEngine:
    id = "geomancy"
    name = "ジオマンシー"
    tradition = "西アフリカ・ヨーロッパ"
    required_fields = frozenset()
    default_options: dict[str, str] = {}

    def cast(self, inp: DivinationInput, rng: SeededRandom, lang: Lang = "ja"):
        shield = build_shield(rng)
        right = shield.right_witness
        left = shield.left_witness
        judge = shield.judge
        drawn = [
            DrawnSymbol(
                key=figure.key,
                name=dt(lang, self.id, f"{figure.key}.name", figure.name),
                position=t(lang, f"position.geomancy.{position}"),
                reversed=False,
                image_hint=f"geomancy/{figure.key}",
            )
            for figure, position in (
                (right, "right_witness"),
                (left, "left_witness"),
                (judge, "judge"),
            )
        ]
        score = round(judge.base_score * 0.6 + (right.base_score + left.base_score) / 2 * 0.4)
        return finish(
            self.id,
            t(lang, "engine.geomancy.name"),
            t(lang, "engine.geomancy.tradition"),
            rng.seed,
            drawn,
            t(
                lang,
                "summary.geomancy",
                name=dt(lang, self.id, f"{judge.key}.name", judge.name),
                judgment=dt(lang, self.id, f"{judge.key}.judgment", judge.judgment),
            ),
            [
                ReadingSection(
                    title=t(lang, "section.overall"),
                    body=dt(lang, self.id, f"{judge.key}.judgment", judge.judgment),
                ),
                ReadingSection(
                    title=t(lang, "section.geomancy.story"),
                    body=t(
                        lang,
                        "body.geomancy.story",
                        name_right=dt(lang, self.id, f"{right.key}.name", right.name),
                        witness_right=dt(lang, self.id, f"{right.key}.witness", right.witness),
                        name_left=dt(lang, self.id, f"{left.key}.name", left.name),
                        witness_left=dt(lang, self.id, f"{left.key}.witness", left.witness),
                    ),
                ),
                ReadingSection(
                    title=t(lang, "section.practice"),
                    body=dt(lang, self.id, f"{judge.key}.practice", judge.practice),
                ),
                ReadingSection(
                    title=t(lang, "section.guidance"),
                    body=t(lang, "body.geomancy.guidance"),
                ),
            ],
            score,
            rng,
            lang,
        )


engine: DivinationEngine = register(GeomancyEngine())

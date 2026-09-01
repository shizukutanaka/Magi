"""Geomancy engine based on a generated shield chart."""

from dataclasses import dataclass

from app.divination.base import DivinationEngine, DivinationInput, DrawnSymbol, ReadingSection
from app.divination.data.geomancy import FIGURES_BY_LINES, GeomancyFigure
from app.divination.engines._common import finish
from app.divination.registry import register
from app.divination.seed import SeededRandom


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

    def cast(self, inp: DivinationInput, rng: SeededRandom):
        shield = build_shield(rng)
        right = shield.right_witness
        left = shield.left_witness
        judge = shield.judge
        drawn = [
            DrawnSymbol(
                key=figure.key,
                name=figure.name,
                position=position,
                reversed=False,
                image_hint=f"geomancy/{figure.key}",
            )
            for figure, position in (
                (right, "右証人"),
                (left, "左証人"),
                (judge, "判事"),
            )
        ]
        score = round(judge.base_score * 0.6 + (right.base_score + left.base_score) / 2 * 0.4)
        return finish(
            self.id,
            self.name,
            self.tradition,
            rng.seed,
            drawn,
            f"{judge.name}が示す「{judge.judgment}」を、今回の中心的な手がかりとします。",
            [
                ReadingSection(title="総合", body=judge.judgment),
                ReadingSection(title="経緯", body=f"{right.witness}そして{left.witness}"),
                ReadingSection(title="実践", body=judge.practice),
                ReadingSection(
                    title="助言",
                    body="盾形図の母体から判事までの流れをたどり、単独の象徴ではなく各段階のつながりとして読み解いてください。",
                ),
            ],
            score,
            rng,
        )


engine: DivinationEngine = register(GeomancyEngine())

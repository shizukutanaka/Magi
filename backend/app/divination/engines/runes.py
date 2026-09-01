"""Elder Futhark three-rune engine."""

from app.divination.base import DivinationEngine, DivinationInput, DrawnSymbol, ReadingSection
from app.divination.data.runes import RUNES
from app.divination.engines._common import finish
from app.divination.registry import register
from app.divination.seed import SeededRandom


class RunesEngine:
    id = "runes"
    name = "ルーン"
    tradition = "北欧"
    required_fields = frozenset()

    def cast(self, inp: DivinationInput, rng: SeededRandom):
        runes = rng.sample(RUNES, 3)
        drawn = []
        for rune, position in zip(runes, ("過去", "現在", "未来"), strict=True):
            reversed_rune = rune.has_reversed and bool(rng.randint(0, 1))
            drawn.append(DrawnSymbol(key=rune.key, name=rune.name_ja, position=position, reversed=reversed_rune, image_hint=f"runes/{rune.key}"))
        first = runes[0]
        return finish(
            self.id, self.name, self.tradition, rng.seed, drawn,
            f"{first.name_ja}の「{first.meaning}」が、流れを読み解く最初のしるしです。",
            [
                ReadingSection(title="総合", body=first.meaning),
                ReadingSection(title="過去・現在・未来", body="三つのルーンを時間の流れとして眺めると、経験が今の選択を支え、未来の方向を照らします。"),
                ReadingSection(title="関係", body="相手を変えようとせず、互いの境界と信頼を尊重しましょう。"),
                ReadingSection(title="助言", body="意味を一つに固定せず、今日の状況に響く言葉を選び取ってください。"),
            ],
            rng.randint(42, 94), rng,
        )


engine: DivinationEngine = register(RunesEngine())

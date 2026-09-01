"""Rider-Waite-Smith tarot engine."""

from app.divination.base import DivinationEngine, DivinationInput, DrawnSymbol, ReadingSection
from app.divination.data.tarot import CARDS
from app.divination.engines._common import finish
from app.divination.registry import register
from app.divination.seed import SeededRandom

ALLOWED_SPREADS = ("three-card", "celtic-cross")


class TarotEngine:
    id = "tarot"
    name = "タロット"
    tradition = "西洋"
    required_fields = frozenset()

    def cast(self, inp: DivinationInput, rng: SeededRandom):
        spread = inp.options.get("spread", "three-card")
        if spread not in ALLOWED_SPREADS:
            raise ValueError(f"unknown tarot spread: {spread}")
        positions = (
            ("過去", "present"), ("現在", "present"), ("未来", "present")
        ) if spread == "three-card" else (
            ("現状", "present"), ("課題", "present"), ("過去", "present"), ("近い未来", "present"),
            ("意識", "present"), ("無意識", "present"), ("自分", "present"), ("環境", "present"),
            ("願望", "present"), ("結論", "present"),
        )
        cards = rng.sample(CARDS, len(positions))
        drawn = []
        for card, (position, _) in zip(cards, positions, strict=True):
            reversed_card = bool(rng.randint(0, 1))
            drawn.append(
                DrawnSymbol(
                    key=card.key,
                    name=card.name_ja,
                    position=position,
                    reversed=reversed_card,
                    image_hint=f"tarot/{card.key}",
                )
            )
        lead = cards[0]
        meaning = lead.reversed_meaning if drawn[0].reversed else lead.upright_meaning
        return finish(
            self.id, self.name, self.tradition, rng.seed, drawn,
            f"{lead.name_ja}が示す「{meaning.split('。')[0]}」を今日の手がかりにしましょう。",
            [
                ReadingSection(title="総合", body=meaning),
                ReadingSection(title="恋愛", body="相手の言葉を決めつけず、感じたことを丁寧に伝えると関係が整います。"),
                ReadingSection(title="仕事", body="優先順位を一つに絞り、目の前の役割を着実に進めましょう。"),
                ReadingSection(title="金運", body="必要なものと勢いで欲しいものを分けて考えると安心です。"),
                ReadingSection(title="助言", body="カードの象徴を自分の問いに重ね、今日できる小さな一歩を選びましょう。"),
            ],
            rng.randint(45, 95), rng,
        )


engine: DivinationEngine = register(TarotEngine())

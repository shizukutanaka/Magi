"""Six-coin I Ching engine."""

from app.divination.base import DivinationEngine, DivinationInput, DrawnSymbol, ReadingSection
from app.divination.data.iching import CARDS
from app.divination.engines._common import finish
from app.divination.registry import register
from app.divination.seed import SeededRandom


class IChingEngine:
    id = "iching"
    name = "易経（周易）"
    tradition = "中国"
    required_fields = frozenset()

    def cast(self, inp: DivinationInput, rng: SeededRandom):
        lines = [sum(rng.randint(2, 3) for _ in range(3)) for _ in range(6)]
        number = sum((1 if line in (7, 9) else 0) << index for index, line in enumerate(lines)) + 1
        primary = CARDS[number - 1]
        changed_lines = [8 if line == 9 else 7 if line == 6 else line for line in lines]
        changed_number = sum((1 if line in (7, 9) else 0) << index for index, line in enumerate(changed_lines)) + 1
        changed = CARDS[changed_number - 1]
        drawn = [DrawnSymbol(key=f"hex-{primary.number:02d}", name=primary.name_ja, position="本卦")]
        if changed_number != number:
            drawn.append(DrawnSymbol(key=f"hex-{changed.number:02d}", name=changed.name_ja, position="之卦"))
        return finish(
            self.id, self.name, self.tradition, rng.seed, drawn,
            f"本卦{primary.name_ja}は、{primary.interpretation.split('。')[0]}。"
            + (f"変化の先には{changed.name_ja}が現れます。" if changed_number != number else ""),
            [
                ReadingSection(title="総合", body=primary.interpretation),
                ReadingSection(title="卦辞", body=primary.judgment),
                ReadingSection(title="変化", body=changed.interpretation if changed_number != number else "変爻はなく、現在の流れを丁寧に保つ時です。"),
                ReadingSection(title="実践", body="一度に全てを動かさず、時機と周囲の調和を確認して進みましょう。"),
            ],
            rng.randint(40, 92), rng,
        )


engine: DivinationEngine = register(IChingEngine())

"""Pythagorean numerology with deterministic Unicode support.

ASCII letters use the traditional A=1..I=9 cycle. Non-ASCII characters are
normalized with NFKC and mapped by ``Unicode code point % 9 + 1`` so Japanese
names and other scripts are handled without silently discarding their value.
"""

import unicodedata

from app.divination.base import DivinationEngine, DivinationInput, DrawnSymbol, ReadingSection
from app.divination.data.numerology import LETTER_VALUES, MASTER_NUMBERS
from app.divination.engines._common import finish
from app.divination.registry import register
from app.divination.seed import SeededRandom


def _reduce(value: int) -> int:
    while value > 9 and value not in MASTER_NUMBERS:
        value = sum(int(digit) for digit in str(value))
    return value


def _name_number(name: str) -> int:
    normalized = unicodedata.normalize("NFKC", name).lower()
    values = [
        LETTER_VALUES[char] if char in LETTER_VALUES else (ord(char) % 9) + 1
        for char in normalized
        if not char.isspace()
    ]
    return _reduce(sum(values))


def _life_path(birth_date) -> int:
    return _reduce(sum(int(digit) for digit in birth_date.strftime("%Y%m%d")))


class NumerologyEngine:
    id = "numerology"
    name = "数秘術"
    tradition = "西洋（ピタゴラス）"
    required_fields = frozenset({"full_name", "birth_date"})

    def cast(self, inp: DivinationInput, rng: SeededRandom):
        if inp.full_name is None or inp.birth_date is None:
            raise ValueError("full_name and birth_date are required")
        life_path = _life_path(inp.birth_date)
        destiny = _name_number(inp.full_name)
        drawn = [
            DrawnSymbol(key=str(life_path), name=f"ライフパス {life_path}", position="生年月日"),
            DrawnSymbol(key=str(destiny), name=f"運命数 {destiny}", position="氏名"),
        ]
        return finish(
            self.id, self.name, self.tradition, rng.seed, drawn,
            f"ライフパス{life_path}と運命数{destiny}が、あなたらしい選択の軸を示しています。",
            [
                ReadingSection(title="ライフパス", body=f"生年月日から導く{life_path}は、経験を通じて育つ人生のテーマです。"),
                ReadingSection(title="運命数", body=f"氏名から導く{destiny}は、周囲に届ける才能と役割を表します。"),
                ReadingSection(title="活かし方", body="数字の意味を決めつけず、得意な行動として日常に小さく取り入れましょう。"),
                ReadingSection(title="助言", body="マスターナンバーを持つ場合も、理想と現実の両方に足場を置くことが大切です。"),
            ],
            rng.randint(40, 96), rng,
        )


engine: DivinationEngine = register(NumerologyEngine())

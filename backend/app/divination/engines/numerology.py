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
from app.i18n import Lang, t


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
    default_options: dict[str, str] = {}

    def cast(self, inp: DivinationInput, rng: SeededRandom, lang: Lang = "ja"):
        if inp.full_name is None or inp.birth_date is None:
            raise ValueError("full_name and birth_date are required")
        life_path = _life_path(inp.birth_date)
        destiny = _name_number(inp.full_name)
        drawn = [
            DrawnSymbol(
                key=str(life_path),
                name=f"ライフパス {life_path}",
                position=t(lang, "position.numerology.birth_date"),
                image_hint=f"numerology/{life_path}",
            ),
            DrawnSymbol(
                key=str(destiny),
                name=f"運命数 {destiny}",
                position=t(lang, "position.numerology.name"),
                image_hint=f"numerology/{destiny}",
            ),
        ]
        return finish(
            self.id, t(lang, "engine.numerology.name"), t(lang, "engine.numerology.tradition"), rng.seed, drawn,
            t(lang, "summary.numerology", life_path=life_path, destiny=destiny),
            [
                ReadingSection(title=t(lang, "section.numerology.life_path"), body=t(lang, "body.numerology.life_path", life_path=life_path)),
                ReadingSection(title=t(lang, "section.numerology.destiny"), body=t(lang, "body.numerology.destiny", destiny=destiny)),
                ReadingSection(title=t(lang, "section.numerology.practice"), body=t(lang, "body.numerology.practice")),
                ReadingSection(title=t(lang, "section.guidance"), body=t(lang, "body.numerology.guidance")),
            ],
            rng.randint(40, 96), rng, lang,
        )


engine: DivinationEngine = register(NumerologyEngine())

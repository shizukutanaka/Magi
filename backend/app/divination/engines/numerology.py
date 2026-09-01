"""Pythagorean numerology with deterministic Unicode support.

ASCII letters use the traditional A=1..I=9 cycle. After NFKC normalization,
only alphabetic characters are counted; non-ASCII letters are mapped by
``Unicode code point % 9 + 1`` so Japanese names and other scripts are handled.
"""

import unicodedata

from app.divination.base import DivinationEngine, DivinationInput, DrawnSymbol, ReadingSection
from app.divination.data.localize import dt
from app.divination.data.numerology import LETTER_VALUES, MASTER_NUMBERS, NUMBERS
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
        if char.isalpha()
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
                name=t(lang, "symbol.numerology.life_path", number=life_path),
                position=t(lang, "position.numerology.birth_date"),
            ),
            DrawnSymbol(
                key=str(destiny),
                name=t(lang, "symbol.numerology.destiny", number=destiny),
                position=t(lang, "position.numerology.name"),
            ),
        ]
        return finish(
            self.id, t(lang, "engine.numerology.name"), t(lang, "engine.numerology.tradition"), rng.seed, drawn,
            t(lang, "summary.numerology", life_path=life_path, destiny=destiny),
            [
                ReadingSection(
                    title=t(lang, "section.numerology.life_path"),
                    body=dt(lang, self.id, f"{life_path}.life_path", NUMBERS[str(life_path)].life_path),
                ),
                ReadingSection(
                    title=t(lang, "section.numerology.destiny"),
                    body=dt(lang, self.id, f"{destiny}.destiny", NUMBERS[str(destiny)].destiny),
                ),
                ReadingSection(title=t(lang, "section.numerology.practice"), body=t(lang, "body.numerology.practice")),
                ReadingSection(
                    title=t(lang, "section.guidance"),
                    body=t(
                        lang,
                        "body.numerology.guidance"
                        if life_path in MASTER_NUMBERS or destiny in MASTER_NUMBERS
                        else "body.numerology.guidance_plain",
                    ),
                ),
            ],
            rng.randint(40, 96), rng, lang,
        )


engine: DivinationEngine = register(NumerologyEngine())

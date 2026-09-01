"""Mayan Tzolkin kin engine.

The calculation uses the GMT correlation constant 584283. A proleptic
Gregorian date is converted to a Julian day number, then ``JDN + 0 - 584283``
is reduced into the 260-day cycle; the zero offset is a documented v1
convention because this product does not use an ephemeris.
"""

from datetime import date

from app.divination.base import DivinationEngine, DivinationInput, DrawnSymbol, ReadingSection
from app.divination.data.mayan import GALACTIC_TONES, SOLAR_SEALS
from app.divination.engines._common import finish
from app.divination.registry import register
from app.divination.seed import SeededRandom

GMT_CORRELATION = 584283


def _julian_day(day: date) -> int:
    year, month = day.year, day.month
    adjusted_year = year + 4800 - ((14 - month) // 12)
    adjusted_month = month + 12 * ((14 - month) // 12) - 3
    return day.day + ((153 * adjusted_month + 2) // 5) + 365 * adjusted_year + adjusted_year // 4 - adjusted_year // 100 + adjusted_year // 400 - 32045


class MayanEngine:
    id = "mayan"
    name = "マヤ暦ツォルキン"
    tradition = "中米"
    required_fields = frozenset({"birth_date"})

    def cast(self, inp: DivinationInput, rng: SeededRandom):
        if inp.birth_date is None:
            raise ValueError("birth_date is required")
        kin = ((_julian_day(inp.birth_date) - GMT_CORRELATION) % 260) + 1
        seal = SOLAR_SEALS[(kin - 1) % 20]
        tone = GALACTIC_TONES[(kin - 1) % 13]
        drawn = [DrawnSymbol(key=f"kin-{kin}", name=f"{tone}{seal}", position="誕生キン", image_hint=f"mayan/{kin}")]
        return finish(
            self.id, self.name, self.tradition, rng.seed, drawn,
            f"{tone}{seal}（KIN {kin}）の象徴は、自分のリズムで才能を育てることを促します。",
            [
                ReadingSection(title="銀河の音", body=f"{tone}音は、意図を定めてエネルギーの流れを整える響きです。"),
                ReadingSection(title="太陽の紋章", body=f"{seal}は、経験の中で磨かれる個性と行動の方向を示します。"),
                ReadingSection(title="今日の流れ", body="生まれ持った象徴を固定的な運命ではなく、選択を見直す鏡として活用しましょう。"),
                ReadingSection(title="助言", body="ツォルキンはGMT相関定数584283に基づく簡略計算です。"),
            ],
            rng.randint(44, 95), rng,
        )


engine: DivinationEngine = register(MayanEngine())

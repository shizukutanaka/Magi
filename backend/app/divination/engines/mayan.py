"""Mayan Tzolkin kin engine.

The traditional Tzolkin count is used: a proleptic Gregorian date is
converted to a Julian day number and reduced into the 260-day cycle with
the GMT correlation constant 584283. Long Count 13.0.0.0.0 (JDN 584283 +
1872000, i.e. 2012-12-21) is the documented 4 Ahau, so ``KIN_OFFSET``
aligns the correlation day with kin 160 = 4 Ahau. This is not the
Dreamspell count, which skips February 29.
"""

from datetime import date

from app.divination.base import DivinationEngine, DivinationInput, DrawnSymbol, ReadingSection
from app.divination.data.localize import dt
from app.divination.data.mayan import GALACTIC_TONES, SOLAR_SEALS
from app.divination.engines._common import finish
from app.divination.registry import register
from app.divination.seed import SeededRandom
from app.i18n import Lang, t

GMT_CORRELATION = 584283

# kin 1 を「磁気の赤い竜」(1 Imix) としたとき 4 Ahau は kin 160 になる。
# 相関日（JDN 584283）と 2012-12-21 を 4 Ahau に合わせるためのオフセット。
KIN_OFFSET = 159


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
    default_options: dict[str, str] = {}

    def cast(self, inp: DivinationInput, rng: SeededRandom, lang: Lang = "ja"):
        if inp.birth_date is None:
            raise ValueError("birth_date is required")
        kin = ((_julian_day(inp.birth_date) - GMT_CORRELATION + KIN_OFFSET) % 260) + 1
        seal_index = (kin - 1) % 20
        tone_index = (kin - 1) % 13
        seal = SOLAR_SEALS[seal_index]
        tone = GALACTIC_TONES[tone_index]
        localized_seal = dt(lang, self.id, f"solar_seal.{seal_index}", seal)
        localized_tone = dt(lang, self.id, f"galactic_tone.{tone_index}", tone)
        symbol = t(
            lang,
            "format.mayan.kin",
            tone=localized_tone,
            seal=localized_seal,
        )
        drawn = [
            DrawnSymbol(
                key=f"kin-{kin}",
                name=symbol,
                position=t(lang, "position.mayan.birth_kin"),
            )
        ]
        return finish(
            self.id, t(lang, "engine.mayan.name"), t(lang, "engine.mayan.tradition"), rng.seed, drawn,
            t(lang, "summary.mayan", symbol=symbol, kin=kin),
            [
                ReadingSection(title=t(lang, "section.mayan.galactic_tone"), body=t(lang, "body.mayan.galactic_tone", tone=localized_tone)),
                ReadingSection(title=t(lang, "section.mayan.solar_seal"), body=t(lang, "body.mayan.solar_seal", seal=localized_seal)),
                ReadingSection(title=t(lang, "section.mayan.flow"), body=t(lang, "body.mayan.flow")),
                ReadingSection(title=t(lang, "section.guidance"), body=t(lang, "body.mayan.guidance")),
            ],
            rng.randint(44, 95), rng, lang,
        )


engine: DivinationEngine = register(MayanEngine())

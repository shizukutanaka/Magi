"""Sun-sign, moon-phase, and weekday-ruler astrology without ephemeris."""

from datetime import date

from app.core.entitlement import Tier
from app.divination.base import DivinationEngine, DivinationInput, DrawnSymbol, ReadingSection
from app.divination.data.astrology import MOON_PHASES, WEEKDAY_RULERS, ZODIAC
from app.divination.engines._common import finish
from app.divination.registry import register
from app.divination.seed import SeededRandom


def sun_sign(birth_date: date) -> tuple[str, str, str]:
    for name, start, end, element, quality in ZODIAC:
        if (birth_date.month, birth_date.day) >= start and (birth_date.month, birth_date.day) <= end:
            return name, element, quality
    return "やぎ座", "土", "堅実さ"


class AstrologyEngine:
    id = "astrology"
    name = "西洋占星術"
    tradition = "西洋"
    required_fields = frozenset({"birth_date"})
    min_tier = Tier.PLUS

    def cast(self, inp: DivinationInput, rng: SeededRandom):
        if inp.birth_date is None:
            raise ValueError("birth_date is required")
        sign, element, quality = sun_sign(inp.birth_date)
        epoch = date(2000, 1, 6)
        days = (inp.target_date - epoch).days
        phase = MOON_PHASES[int((days % 29.530588853) / (29.530588853 / 8))]
        ruler = WEEKDAY_RULERS[inp.target_date.weekday()]
        drawn = [
            DrawnSymbol(key=sign, name=sign, position="太陽星座", image_hint=f"astrology/{sign}"),
            DrawnSymbol(key=phase, name=phase, position="月相"),
            DrawnSymbol(key=ruler, name=ruler, position="曜日の支配星"),
        ]
        return finish(
            self.id, self.name, self.tradition, rng.seed, drawn,
            f"{sign}の{quality}を、{phase}の内省と{ruler}の行動力で活かす日です。",
            [
                ReadingSection(title="太陽星座", body=f"{sign}（{element}）の持ち味である{quality}を、無理なく表現しましょう。"),
                ReadingSection(title="月相", body=f"{phase}は心のリズムを見つめる節目です。気持ちを言葉にすると整理が進みます。"),
                ReadingSection(title="曜日の支配星", body=f"{ruler}の象徴が示す力を借り、今日の最優先事項を一つ実行しましょう。"),
                ReadingSection(title="助言", body="星の配置を決定としてではなく、自分を振り返る視点として受け取りましょう。"),
            ],
            rng.randint(45, 93), rng,
        )


engine: DivinationEngine = register(AstrologyEngine())

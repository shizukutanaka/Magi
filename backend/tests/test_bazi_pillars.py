from datetime import date

from app.divination.data.bazi import BRANCHES, STEMS
from app.divination.engines.bazi import _cycle_index, _day_cycle

# 外部の暦ライブラリ（sxtwl 2.0.7）と突き合わせて確認した日柱。
KNOWN_DAY_PILLARS = {
    date(1949, 10, 1): "甲子",
    date(1984, 6, 15): "庚辰",
    date(1990, 5, 4): "己巳",
    date(2000, 1, 1): "戊午",
    date(2026, 9, 1): "戊寅",
}


def _pillar(index: int) -> str:
    return STEMS[index % 10] + BRANCHES[index % 12]


def test_day_pillars_match_reference_calendar():
    for day, expected in KNOWN_DAY_PILLARS.items():
        assert _pillar(_day_cycle(day)) == expected, day


def test_year_pillar_uses_january_first_not_lichun():
    # 略式であることの明示的な回帰: 伝統的には立春までは前年の年柱（1999年は己卯）だが、
    # Magiは1月1日で切り替えるため 2000-01-01 は庚辰になる。
    assert _pillar(_cycle_index(2000)) == "庚辰"
    assert _pillar(_cycle_index(1984)) == "甲子"

from datetime import date

from app.divination.data.mayan import GALACTIC_TONES, SOLAR_SEALS
from app.divination.engines.mayan import GMT_CORRELATION, KIN_OFFSET, _julian_day


def _kin(day: date) -> int:
    return ((_julian_day(day) - GMT_CORRELATION + KIN_OFFSET) % 260) + 1


def _label(kin: int) -> str:
    return GALACTIC_TONES[(kin - 1) % 13] + SOLAR_SEALS[(kin - 1) % 20]


def test_julian_day_matches_known_value():
    assert _julian_day(date(2000, 1, 1)) == 2451545


def test_long_count_zero_and_13_baktun_share_a_tzolkin_day():
    # 13.0.0.0.0 は相関日から 1872000 日後で、1872000 は 260 の倍数。
    assert 1872000 % 260 == 0
    assert _julian_day(date(2012, 12, 21)) - GMT_CORRELATION == 1872000


def test_2012_12_21_is_four_ahau():
    # 13.0.0.0.0（2012-12-21）のツォルキンは 4 Ahau = 自己存在の黄色い太陽。
    kin = _kin(date(2012, 12, 21))
    assert kin == 160
    assert SOLAR_SEALS[(kin - 1) % 20] == "黄色い太陽"
    assert GALACTIC_TONES[(kin - 1) % 13] == "自己存在の"
    assert _label(kin) == "自己存在の黄色い太陽"


def test_kin_advances_by_one_each_day():
    base = _kin(date(2026, 9, 1))
    assert _kin(date(2026, 9, 2)) == (base % 260) + 1

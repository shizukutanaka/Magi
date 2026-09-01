from app.divination.data.iching import CARDS, KING_WEN_BY_LINES

# 三爻の名称と、その爻を下から並べたビット値（陽=1）。
TRIGRAM_BITS = {
    "乾": 0b111,
    "天": 0b111,
    "坤": 0b000,
    "地": 0b000,
    "震": 0b001,
    "雷": 0b001,
    "坎": 0b010,
    "水": 0b010,
    "兌": 0b011,
    "沢": 0b011,
    "艮": 0b100,
    "山": 0b100,
    "離": 0b101,
    "火": 0b101,
    "巽": 0b110,
    "風": 0b110,
}


def _table_from_hexagram_names() -> dict[int, int]:
    """Derive lines -> King Wen number from the hexagram names in the data file."""
    table: dict[int, int] = {}
    for hexagram in CARDS:
        name = hexagram.name_ja
        if "為" in name:
            upper = lower = TRIGRAM_BITS[name[0]]
        else:
            upper, lower = TRIGRAM_BITS[name[0]], TRIGRAM_BITS[name[1]]
        key = lower | (upper << 3)
        assert key not in table, f"duplicate trigram pair for {name}"
        table[key] = hexagram.number
    return table


def test_king_wen_table_matches_hexagram_names():
    derived = _table_from_hexagram_names()
    assert len(derived) == 64
    assert tuple(derived[bits] for bits in range(64)) == KING_WEN_BY_LINES


def test_pure_yang_and_pure_yin():
    assert KING_WEN_BY_LINES[0b111111] == 1  # 六爻すべて陽は乾為天
    assert KING_WEN_BY_LINES[0b000000] == 2  # 六爻すべて陰は坤為地


def test_known_hexagram_from_lines():
    # 下から 陽・陰・陰（震＝雷）／陰・陽・陰（坎＝水）→ 水雷屯（第3卦）
    assert KING_WEN_BY_LINES[0b010_001] == 3

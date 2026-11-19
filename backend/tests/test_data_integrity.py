from app.divination.data.tarot import CARDS


def test_tarot_data_integrity():
    assert len(CARDS) == 78
    assert len({card.key for card in CARDS}) == 78
    assert len({card.upright_meaning for card in CARDS}) == 78
    assert len({card.reversed_meaning for card in CARDS}) == 78
    assert all(len(card.upright_keywords) == 3 and len(card.reversed_keywords) == 3 for card in CARDS)
    assert all(len(card.upright_meaning) >= 15 and len(card.reversed_meaning) >= 15 for card in CARDS)


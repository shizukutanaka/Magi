import json
import re
from pathlib import Path

from app.divination.data.en.tarot import _ROWS as EN_ROWS
from app.divination.data.tarot import CARDS


def test_tarot_data_integrity():
    assert len(CARDS) == 78
    assert len({card.key for card in CARDS}) == 78
    assert len({card.upright_meaning for card in CARDS}) == 78
    assert len({card.reversed_meaning for card in CARDS}) == 78
    assert all(len(card.upright_keywords) == 3 and len(card.reversed_keywords) == 3 for card in CARDS)
    assert all(len(card.upright_meaning) >= 15 and len(card.reversed_meaning) >= 15 for card in CARDS)



def _tarot_page_cards():
    html = (Path(__file__).resolve().parents[2] / "frontend" / "tarot.html").read_text(encoding="utf-8")
    match = re.search(r"/\*CARDS-BEGIN\*/(\[.*?\])/\*CARDS-END\*/", html, re.S)
    assert match, "tarot.html must embed the card data between CARDS markers"
    return json.loads(match.group(1))


def test_tarot_page_card_data_matches_backend():
    english = {key: (name, upright, reversed_) for key, name, upright, reversed_ in EN_ROWS}
    expected = [
        {
            "key": card.key,
            "name": {"ja": card.name_ja, "en": english[card.key][0]},
            "kwUp": list(card.upright_keywords),
            "kwRev": list(card.reversed_keywords),
            "up": {"ja": card.upright_meaning, "en": english[card.key][1]},
            "rev": {"ja": card.reversed_meaning, "en": english[card.key][2]},
        }
        for card in CARDS
    ]
    fields = ("key", "name", "kwUp", "kwRev", "up", "rev")
    actual = [{field: page_card.get(field) for field in fields} for page_card in _tarot_page_cards()]
    assert actual == expected

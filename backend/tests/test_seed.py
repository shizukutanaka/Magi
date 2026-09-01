from datetime import date

from app.divination.base import DivinationInput
from app.divination.seed import build_seed, normalize_question


def test_normalize_fullwidth_space():
    assert normalize_question("問い　　です") == "問い です"


def test_normalize_case():
    assert normalize_question("What IS this?") == "what is this?"


def test_normalize_surrounding_whitespace():
    assert normalize_question("  今日の運勢  ") == "今日の運勢"


def test_seed_regression():
    inp = DivinationInput(target_date=date(2026, 1, 2), question="  ＡＢＣ  ")
    assert build_seed("subject", "tarot", inp) == "564ca55f6b77173b9843ad73994f8d3dd460d2029a93689f75f53034667b47dc"

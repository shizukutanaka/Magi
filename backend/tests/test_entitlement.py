from app.core.entitlement import DAILY_READING_LIMIT, Tier, allowed_engines, allowed_spreads


def test_free_entitlement():
    assert [engine.id for engine in allowed_engines(Tier.FREE)] == ["tarot", "iching", "omikuji"]
    assert allowed_spreads(Tier.FREE) == ("three-card",)
    assert allowed_spreads(Tier.PLUS) == ("three-card", "celtic-cross")
    assert DAILY_READING_LIMIT[Tier.FREE] == 3
    assert DAILY_READING_LIMIT[Tier.PLUS] is None

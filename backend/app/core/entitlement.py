"""Pure subscription-tier permissions."""

from enum import Enum
from typing import Any


class Tier(str, Enum):
    FREE = "free"
    PLUS = "plus"
    PRO = "pro"

    @property
    def rank(self) -> int:
        return {Tier.FREE: 0, Tier.PLUS: 1, Tier.PRO: 2}[self]


DAILY_READING_LIMIT: dict[Tier, int | None] = {
    Tier.FREE: 3,
    Tier.PLUS: None,
    Tier.PRO: None,
}


def can_use(tier: Tier, engine: Any) -> bool:
    return tier.rank >= engine.min_tier.rank


def allowed_engines(tier: Tier) -> list[Any]:
    from app.divination.registry import all_engines

    return [engine for engine in all_engines() if can_use(tier, engine)]


def allowed_spreads(tier: Tier) -> tuple[str, ...]:
    if tier is Tier.FREE:
        return ("three-card",)
    return ("three-card", "celtic-cross")

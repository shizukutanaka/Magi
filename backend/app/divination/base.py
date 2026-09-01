"""Shared models and protocol for divination engines."""

from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Protocol

from pydantic import BaseModel, Field

from app.i18n import Lang

if TYPE_CHECKING:
    from app.divination.seed import SeededRandom

DISCLAIMER = "本鑑定はエンターテインメントおよび内省の補助を目的とし、医療・法律・投資の助言ではありません。"


class DivinationInput(BaseModel):
    target_date: date
    question: str | None = None
    birth_date: date | None = None
    full_name: str | None = None
    options: dict[str, str] = Field(default_factory=dict)


class DrawnSymbol(BaseModel):
    key: str
    name: str
    position: str
    reversed: bool = False


class ReadingSection(BaseModel):
    title: str
    body: str


class LuckyItems(BaseModel):
    color: str
    number: int
    direction: str
    item: str


class Reading(BaseModel):
    engine_id: str
    engine_name: str
    tradition: str
    seed: str
    drawn: list[DrawnSymbol]
    summary: str
    sections: list[ReadingSection]
    score: int | None
    lucky: LuckyItems | None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    disclaimer: str = DISCLAIMER
    lang: str = "ja"
    interpretation_lang: str = "ja"


class DivinationEngine(Protocol):
    id: str
    name: str
    tradition: str
    required_fields: frozenset[str]
    default_options: dict[str, str]

    def cast(self, inp: DivinationInput, rng: "SeededRandom", lang: Lang = "ja") -> Reading:
        """Return a deterministic reading for the supplied seeded random source."""

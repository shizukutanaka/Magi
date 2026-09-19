"""Shared models and protocol for divination engines."""

from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Annotated, Protocol

from pydantic import BaseModel, Field

from app.i18n import Lang

if TYPE_CHECKING:
    from app.divination.seed import SeededRandom

DISCLAIMER = "本鑑定はエンターテインメントおよび内省の補助を目的とし、医療・法律・投資の助言ではありません。"


class MissingFieldsError(Exception):
    """Raised when an engine does not receive all required input fields.

    必須フィールドは値を持っていても実質的に欠落している場合がある
    （例: 文字を1文字も含まない氏名）。サービス層だけでなくエンジンも
    送出できるよう、循環参照を避けてここに定義する。
    """

    def __init__(self, fields: list[str]) -> None:
        self.fields = sorted(fields)
        super().__init__(f"missing fields: {', '.join(self.fields)}")


OptionText = Annotated[str, Field(max_length=64)]


class DivinationInput(BaseModel):
    target_date: date
    question: str | None = Field(default=None, max_length=200)
    birth_date: date | None = None
    full_name: str | None = Field(default=None, max_length=100)
    options: dict[OptionText, OptionText] = Field(default_factory=dict)


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
    culture: str
    required_fields: frozenset[str]
    default_options: dict[str, str]

    def cast(self, inp: DivinationInput, rng: "SeededRandom", lang: Lang = "ja") -> Reading:
        """Return a deterministic reading for the supplied seeded random source."""

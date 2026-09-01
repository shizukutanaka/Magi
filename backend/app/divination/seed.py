"""Stable, input-derived random sources for readings."""

import hashlib
import random
import re
import unicodedata
from collections.abc import MutableSequence, Sequence
from typing import TypeVar

from app.divination.base import DivinationInput

T = TypeVar("T")


def normalize_question(question: str | None) -> str:
    """Normalize equivalent Japanese/Latin questions to the same form."""
    value = unicodedata.normalize("NFKC", question or "").strip().lower()
    return re.sub(r"\s+", " ", value)


def build_seed(subject_key: str, engine_id: str, inp: DivinationInput) -> str:
    options = sorted(inp.options.items())
    raw = (
        f"{subject_key}|{engine_id}|{inp.target_date.isoformat()}|"
        f"{normalize_question(inp.question)}|{inp.birth_date or ''}|{inp.full_name or ''}|{options}"
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class SeededRandom:
    """Thin wrapper around a private random.Random instance."""

    def __init__(self, seed: str):
        self.seed = seed
        self._random = random.Random(int(seed[:16], 16))

    def choice(self, seq: Sequence[T]) -> T:
        return self._random.choice(seq)

    def sample(self, population: Sequence[T], k: int) -> list[T]:
        return self._random.sample(population, k)

    def shuffle(self, sequence: MutableSequence[T]) -> None:
        self._random.shuffle(sequence)

    def randint(self, start: int, end: int) -> int:
        return self._random.randint(start, end)

    def pick(self, values: list[T]) -> T:
        return self.choice(values)

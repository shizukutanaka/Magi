"""HTTP-independent reading orchestration."""

import hashlib

from app.divination.base import DivinationEngine, DivinationInput, Reading
from app.divination.engines.tarot import ALLOWED_SPREADS
from app.divination.registry import all_engines, get_engine
from app.divination.seed import SeededRandom, build_seed
from app.i18n import DEFAULT_LANG, Lang, t


class ReadingError(Exception):
    """Base class for expected reading-service errors."""


class UnknownSpreadError(ReadingError):
    """Raised when Tarot receives an unsupported spread."""


class MissingFieldsError(ReadingError):
    """Raised when an engine does not receive all required input fields."""

    def __init__(self, fields: list[str]) -> None:
        self.fields = sorted(fields)
        super().__init__(f"missing fields: {', '.join(self.fields)}")


def _validate_spread(inp: DivinationInput) -> None:
    if inp.options.get("spread", "three-card") not in ALLOWED_SPREADS:
        raise UnknownSpreadError


def cast_reading(
    engine_id: str,
    inp: DivinationInput,
    subject_key: str,
    lang: Lang = DEFAULT_LANG,
) -> Reading:
    """Cast one reading using the same path as the HTTP API."""
    engine = get_engine(engine_id)
    missing = [field for field in engine.required_fields if getattr(inp, field, None) is None]
    if missing:
        raise MissingFieldsError(missing)
    inp = inp.model_copy(update={"options": {**engine.default_options, **inp.options}})
    if engine.id == "tarot":
        _validate_spread(inp)
    seed = build_seed(subject_key, engine.id, inp)
    return engine.cast(inp, SeededRandom(seed), lang)


def select_daily_engines(
    inp: DivinationInput,
    subject_key: str,
    lang: Lang = DEFAULT_LANG,
) -> list[DivinationEngine]:
    """Select up to three eligible engines from distinct traditions."""
    available = [
        engine
        for engine in all_engines()
        if all(getattr(inp, field, None) is not None for field in engine.required_fields)
    ]
    selection_rng = SeededRandom(hashlib.sha256(f"{subject_key}|{inp.target_date}".encode()).hexdigest())
    selection = []
    traditions = set()
    for engine in selection_rng.sample(available, len(available)):
        if engine.tradition not in traditions:
            selection.append(engine)
            traditions.add(engine.tradition)
    return selection[:3]


def daily_reading(
    inp: DivinationInput,
    subject_key: str,
    lang: Lang = DEFAULT_LANG,
) -> dict:
    """Return the deterministic three-tradition daily reading."""
    _validate_spread(inp)
    selection = select_daily_engines(inp, subject_key, lang)
    readings = [cast_reading(engine.id, inp, subject_key, lang) for engine in selection]
    scores = [reading.score for reading in readings if reading.score is not None]
    names = [symbol.name for reading in readings for symbol in reading.drawn]
    overview = t(lang, "daily.overview", count=len(readings), names="・".join(names[:3]))
    return {
        "readings": readings,
        "overview": overview,
        "score": round(sum(scores) / len(scores)) if scores else None,
    }

"""HTTP-independent reading orchestration."""

from app.divination.base import DivinationInput, Reading, ReadingSection
from app.divination.engines.tarot import ALLOWED_SPREADS
from app.divination.question import classify_question
from app.divination.registry import get_engine
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


def _add_question_focus(reading: Reading, inp: DivinationInput, lang: Lang) -> Reading:
    topic = classify_question(inp.question)
    if topic is None or not reading.drawn:
        return reading
    focus = ReadingSection(
        title=t(lang, "section.focus", topic=t(lang, f"topic.{topic}")),
        body=t(lang, f"body.focus.{reading.engine_id}.{topic}"),
    )
    sections = list(reading.sections)
    sections.insert(min(1, len(sections)), focus)
    return reading.model_copy(update={"sections": sections})


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
    known = {key: value for key, value in inp.options.items() if key in engine.default_options}
    inp = inp.model_copy(update={"options": {**engine.default_options, **known}})
    if engine.id == "tarot":
        _validate_spread(inp)
    seed = build_seed(subject_key, engine.id, inp)
    return _add_question_focus(engine.cast(inp, SeededRandom(seed), lang), inp, lang)


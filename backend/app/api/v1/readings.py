"""Reading endpoints."""

import hashlib
from datetime import date, time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.ratelimit import rate_limit
from app.divination.base import DivinationInput
from app.divination.engines.tarot import ALLOWED_SPREADS
from app.divination.registry import UnknownEngineError, all_engines, get_engine
from app.divination.seed import SeededRandom, build_seed

router = APIRouter(tags=["readings"])


class ReadingRequest(BaseModel):
    engine_id: str
    input: DivinationInput
    subject_key: str = "anonymous"


class DailyRequest(BaseModel):
    target_date: date = Field(default_factory=date.today)
    question: str | None = None
    birth_date: date | None = None
    birth_time: time | None = None
    full_name: str | None = None
    options: dict[str, str] = Field(default_factory=dict)
    subject_key: str = "anonymous"


def _validate_spread(inp: DivinationInput) -> None:
    if inp.options.get("spread", "three-card") not in ALLOWED_SPREADS:
        raise HTTPException(status_code=422, detail="未知のスプレッドです。")


def _cast(engine_id: str, inp: DivinationInput, subject_key: str):
    try:
        engine = get_engine(engine_id)
    except UnknownEngineError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown engine: {engine_id}") from exc
    missing = [field for field in engine.required_fields if getattr(inp, field, None) is None]
    if missing:
        raise HTTPException(status_code=422, detail={"missing_fields": sorted(missing)})
    if engine.id == "tarot":
        _validate_spread(inp)
    seed = build_seed(subject_key, engine.id, inp)
    return engine.cast(inp, SeededRandom(seed))


@router.post("/readings")
def create_reading(payload: ReadingRequest, _: None = Depends(rate_limit)):
    return _cast(payload.engine_id, payload.input, payload.subject_key)


@router.post("/readings/daily")
def daily_reading(payload: DailyRequest, _: None = Depends(rate_limit)):
    inp = DivinationInput(
        target_date=payload.target_date,
        question=payload.question,
        birth_date=payload.birth_date,
        birth_time=payload.birth_time,
        full_name=payload.full_name,
        options=payload.options,
    )
    _validate_spread(inp)
    available = [
        engine
        for engine in all_engines()
        if all(getattr(inp, field, None) is not None for field in engine.required_fields)
    ]
    selection_rng = SeededRandom(hashlib.sha256(f"{payload.subject_key}|{payload.target_date}".encode()).hexdigest())
    selection = []
    traditions = set()
    for engine in selection_rng.sample(available, len(available)):
        if engine.tradition not in traditions:
            selection.append(engine)
            traditions.add(engine.tradition)
    selection = selection[:3]
    readings = [_cast(engine.id, inp, payload.subject_key) for engine in selection]
    scores = [reading.score for reading in readings if reading.score is not None]
    names = [symbol.name for reading in readings for symbol in reading.drawn]
    overview = f"{len(readings)}つの流派が、{ '・'.join(names[:3]) }を共通の手がかりとして示しています。"
    return {
        "readings": readings,
        "overview": overview,
        "score": round(sum(scores) / len(scores)) if scores else None,
    }

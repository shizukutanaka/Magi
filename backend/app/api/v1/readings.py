"""Reading endpoints."""

from datetime import date, time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.ratelimit import rate_limit
from app.divination.base import DivinationInput
from app.divination.registry import UnknownEngineError
from app.divination.service import (
    MissingFieldsError,
    UnknownSpreadError,
    cast_reading,
)
from app.divination.service import daily_reading as build_daily_reading

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


def _cast(engine_id: str, inp: DivinationInput, subject_key: str):
    try:
        return cast_reading(engine_id, inp, subject_key)
    except UnknownEngineError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown engine: {engine_id}") from exc
    except MissingFieldsError as exc:
        raise HTTPException(status_code=422, detail={"missing_fields": exc.fields}) from exc
    except UnknownSpreadError as exc:
        raise HTTPException(status_code=422, detail="未知のスプレッドです。") from exc


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
    try:
        return build_daily_reading(inp, payload.subject_key)
    except UnknownSpreadError as exc:
        raise HTTPException(status_code=422, detail="未知のスプレッドです。") from exc

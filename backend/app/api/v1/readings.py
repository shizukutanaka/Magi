"""Reading endpoints."""

from datetime import date, time

from fastapi import APIRouter, Depends, Header, HTTPException
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
from app.i18n import DEFAULT_LANG, resolve_lang, t

router = APIRouter(tags=["readings"])


class ReadingRequest(BaseModel):
    engine_id: str
    input: DivinationInput
    subject_key: str = "anonymous"
    lang: str | None = None


class DailyRequest(BaseModel):
    target_date: date = Field(default_factory=date.today)
    question: str | None = None
    birth_date: date | None = None
    birth_time: time | None = None
    full_name: str | None = None
    options: dict[str, str] = Field(default_factory=dict)
    subject_key: str = "anonymous"
    lang: str | None = None


def _cast(
    engine_id: str,
    inp: DivinationInput,
    subject_key: str,
    lang: str = DEFAULT_LANG,
):
    try:
        return cast_reading(engine_id, inp, subject_key, resolve_lang(lang, None))
    except UnknownEngineError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown engine: {engine_id}") from exc
    except MissingFieldsError as exc:
        raise HTTPException(status_code=422, detail={"missing_fields": exc.fields}) from exc
    except UnknownSpreadError as exc:
        raise HTTPException(status_code=422, detail=t(resolve_lang(lang, None), "error.unknown_spread")) from exc


@router.post("/readings")
def create_reading(
    payload: ReadingRequest,
    _: None = Depends(rate_limit),
    accept_language: str | None = Header(default=None, alias="Accept-Language"),
):
    lang = resolve_lang(payload.lang, accept_language)
    return _cast(payload.engine_id, payload.input, payload.subject_key, lang)


@router.post("/readings/daily")
def daily_reading(
    payload: DailyRequest,
    _: None = Depends(rate_limit),
    accept_language: str | None = Header(default=None, alias="Accept-Language"),
):
    inp = DivinationInput(
        target_date=payload.target_date,
        question=payload.question,
        birth_date=payload.birth_date,
        birth_time=payload.birth_time,
        full_name=payload.full_name,
        options=payload.options,
    )
    try:
        return build_daily_reading(inp, payload.subject_key, resolve_lang(payload.lang, accept_language))
    except UnknownSpreadError as exc:
        lang = resolve_lang(payload.lang, accept_language)
        raise HTTPException(status_code=422, detail=t(lang, "error.unknown_spread")) from exc

"""Reading endpoints."""

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
from app.i18n import Lang, resolve_lang, t

router = APIRouter(tags=["readings"])


class ReadingRequest(BaseModel):
    engine_id: str
    input: DivinationInput
    subject_key: str = Field(default="anonymous", min_length=1, max_length=64)
    lang: str | None = None


def _cast(
    engine_id: str,
    inp: DivinationInput,
    subject_key: str,
    lang: Lang,
):
    try:
        return cast_reading(engine_id, inp, subject_key, lang)
    except UnknownEngineError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown engine: {engine_id}") from exc
    except MissingFieldsError as exc:
        raise HTTPException(status_code=422, detail={"missing_fields": exc.fields}) from exc
    except UnknownSpreadError as exc:
        raise HTTPException(status_code=422, detail=t(lang, "error.unknown_spread")) from exc


@router.post("/readings")
def create_reading(
    payload: ReadingRequest,
    _: None = Depends(rate_limit),
    accept_language: str | None = Header(default=None, alias="Accept-Language"),
):
    lang = resolve_lang(payload.lang, accept_language)
    return _cast(payload.engine_id, payload.input, payload.subject_key, lang)


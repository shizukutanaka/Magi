"""Available divination-system metadata endpoint."""

from fastapi import APIRouter, Header, Query

from app.divination.interpretation import interpretation_langs
from app.divination.registry import all_engines
from app.i18n import resolve_lang, t

router = APIRouter(tags=["systems"])


@router.get("/systems")
def list_systems(
    lang: str | None = Query(default=None),
    accept_language: str | None = Header(default=None, alias="Accept-Language"),
):
    resolved_lang = resolve_lang(lang, accept_language)
    return [
        {
            "id": engine.id,
            "name": t(resolved_lang, f"engine.{engine.id}.name"),
            "tradition": t(resolved_lang, f"engine.{engine.id}.tradition"),
            "required_fields": sorted(engine.required_fields),
            "interpretation_langs": list(interpretation_langs(engine.id)),
        }
        for engine in all_engines()
    ]

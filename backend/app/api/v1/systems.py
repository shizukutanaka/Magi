"""Available divination-system metadata endpoint."""

from fastapi import APIRouter, Header, Query, Response

from app.divination.interpretation import interpretation_langs
from app.divination.registry import all_engines
from app.i18n import resolve_lang, t

router = APIRouter(tags=["systems"])


@router.get("/systems")
def list_systems(
    response: Response,
    lang: str | None = Query(default=None),
    accept_language: str | None = Header(default=None, alias="Accept-Language"),
):
    # 応答は Accept-Language で変わるため、共有キャッシュが別言語の
    # 応答を誤って配信しないよう Vary を付ける（?lang= はURL自体がキー）。
    response.headers["Vary"] = "Accept-Language"
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

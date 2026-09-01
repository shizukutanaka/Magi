"""Available divination-system metadata endpoint."""

from fastapi import APIRouter

from app.divination.registry import all_engines

router = APIRouter(tags=["systems"])


@router.get("/systems")
def list_systems():
    return [
        {
            "id": engine.id,
            "name": engine.name,
            "tradition": engine.tradition,
            "required_fields": sorted(engine.required_fields),
        }
        for engine in all_engines()
    ]

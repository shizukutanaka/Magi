"""Available divination-system metadata endpoint."""

from fastapi import APIRouter, Depends

from app.api.v1.readings import get_current_tier
from app.core.entitlement import Tier, can_use
from app.divination.registry import all_engines

router = APIRouter(tags=["systems"])


@router.get("/systems")
def list_systems(tier: Tier = Depends(get_current_tier)):
    return [
        {
            "id": engine.id,
            "name": engine.name,
            "tradition": engine.tradition,
            "required_fields": sorted(engine.required_fields),
            "min_tier": engine.min_tier.value,
            "available": can_use(tier, engine),
        }
        for engine in all_engines()
    ]

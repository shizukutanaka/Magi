"""Version one route collection."""

from fastapi import APIRouter

from app.api.v1 import readings, systems

router = APIRouter()
router.include_router(systems.router)
router.include_router(readings.router)

"""Stable registry of available divination engines."""

from collections.abc import Iterable
from importlib import import_module

from app.divination.base import DivinationEngine


class UnknownEngineError(LookupError):
    """Raised when a caller asks for an unregistered engine."""


_engines: dict[str, DivinationEngine] = {}
_builtins_loaded = False


def _ensure_builtins() -> None:
    global _builtins_loaded
    if not _builtins_loaded:
        import_module("app.divination.engines")
        _builtins_loaded = True


def register(engine: DivinationEngine) -> DivinationEngine:
    _engines[engine.id] = engine
    return engine


def get_engine(engine_id: str) -> DivinationEngine:
    _ensure_builtins()
    try:
        return _engines[engine_id]
    except KeyError as exc:
        raise UnknownEngineError(engine_id) from exc


def all_engines() -> list[DivinationEngine]:
    _ensure_builtins()
    return list(_engines.values())


def register_all(engines: Iterable[DivinationEngine]) -> None:
    for engine in engines:
        register(engine)

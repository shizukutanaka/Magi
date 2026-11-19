"""Built-in divination engines."""

from importlib import import_module

import_module(f"{__name__}.tarot")

__all__ = ["tarot"]

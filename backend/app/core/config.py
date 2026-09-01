"""Environment-backed application configuration."""

import os


def get_rate_limit_per_minute() -> int:
    value = os.getenv("MAGI_RATE_LIMIT_PER_MINUTE")
    if value is None:
        return 60
    try:
        return int(value)
    except ValueError:
        return 60

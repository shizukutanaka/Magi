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


def get_trust_proxy_headers() -> bool:
    value = os.getenv("MAGI_TRUST_PROXY")
    if value is None:
        return False
    return value.strip().lower() in ("1", "true", "yes", "on")

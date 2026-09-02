"""Environment-backed application configuration."""

import os


class ConfigError(RuntimeError):
    """設定値が不正であることを示す。"""


TRUE_VALUES = ("1", "true", "yes", "on")
FALSE_VALUES = ("0", "false", "no", "off")


def _read(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def get_rate_limit_per_minute() -> int:
    value = _read("MAGI_RATE_LIMIT_PER_MINUTE")
    if value is None:
        return 60
    try:
        return int(value)
    except ValueError as exc:
        raise ConfigError(
            f"MAGI_RATE_LIMIT_PER_MINUTE の値 {value!r} は整数でなければなりません。"
            " 0以下にするとレートリミットを無効にできます。"
        ) from exc


def get_trust_proxy_headers() -> bool:
    value = _read("MAGI_TRUST_PROXY")
    if value is None:
        return False
    normalized = value.lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    accepted = ", ".join((*TRUE_VALUES, *FALSE_VALUES))
    raise ConfigError(
        f"MAGI_TRUST_PROXY の値 {value!r} は不正です。"
        f"受け付ける値: {accepted}。"
    )


def validate_environment() -> None:
    get_rate_limit_per_minute()
    get_trust_proxy_headers()

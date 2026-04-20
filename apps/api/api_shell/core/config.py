from functools import lru_cache

from kalshi_signal_shared.settings import AppSettings


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()

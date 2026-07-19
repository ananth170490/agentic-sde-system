from __future__ import annotations

from app.store import UrlStore


class AnalyticsService:
    def __init__(self, store: UrlStore) -> None:
        self._store = store

    def clicks_for(self, code: str) -> int:
        return self._store.get_click_count(code)

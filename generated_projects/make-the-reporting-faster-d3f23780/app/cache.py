from __future__ import annotations


class ReportCache:
    def __init__(self, max_entries: int = 3) -> None:
        self._max_entries = max_entries
        self._items: dict[str, str] = {}
        self._order: list[str] = []

    def put(self, key: str, value: str) -> None:
        if key in self._items:
            self._order.remove(key)
        elif len(self._order) >= self._max_entries:
            oldest = self._order.pop(0)
            del self._items[oldest]

        self._items[key] = value
        self._order.append(key)

    def get(self, key: str) -> str | None:
        return self._items.get(key)

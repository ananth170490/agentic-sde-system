from __future__ import annotations

import sqlite3
from pathlib import Path


class UrlStore:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _init_db(self) -> None:
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS url_mappings (code TEXT PRIMARY KEY, target_url TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
            conn.execute("CREATE TABLE IF NOT EXISTS click_events (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
            conn.commit()

    def save_url(self, code: str, target_url: str) -> None:
        with self._connect() as conn:
            conn.execute("INSERT OR REPLACE INTO url_mappings(code, target_url) VALUES (?, ?)", (code, target_url))
            conn.commit()

    def get_url(self, code: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute("SELECT target_url FROM url_mappings WHERE code = ?", (code,)).fetchone()
        return row[0] if row else None

    def record_click(self, code: str) -> None:
        with self._connect() as conn:
            conn.execute("INSERT INTO click_events(code) VALUES (?)", (code,))
            conn.commit()

    def get_click_count(self, code: str) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) FROM click_events WHERE code = ?", (code,)).fetchone()
        return int(row[0] if row else 0)

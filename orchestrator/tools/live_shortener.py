from __future__ import annotations

import secrets
import sqlite3
from pathlib import Path


def _db_path(db_path: str | None = None) -> str:
    if db_path:
        return db_path
    return str((Path.cwd() / "generated_projects" / "url-shortener" / "live_demo_url_shortener.db").resolve())


def _connect(db_path: str | None = None) -> sqlite3.Connection:
    target = _db_path(db_path)
    Path(target).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(target)


def ensure_schema(db_path: str | None = None) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS url_mappings ("
            "code TEXT PRIMARY KEY, "
            "target_url TEXT NOT NULL, "
            "created_at TEXT DEFAULT CURRENT_TIMESTAMP"
            ")"
        )
        conn.commit()


def _new_code() -> str:
    return secrets.token_urlsafe(6)[:8]


def create_short_url(target_url: str, db_path: str | None = None) -> tuple[str, str]:
    ensure_schema(db_path)
    with _connect(db_path) as conn:
        code = _new_code()
        for _ in range(12):
            row = conn.execute("SELECT 1 FROM url_mappings WHERE code = ?", (code,)).fetchone()
            if row is None:
                break
            code = _new_code()
        else:
            raise RuntimeError("Failed to generate unique short code")

        conn.execute("INSERT OR REPLACE INTO url_mappings(code, target_url) VALUES (?, ?)", (code, target_url))
        conn.commit()
    return code, f"/demo/{code}"


def resolve_short_code(code: str, db_path: str | None = None) -> str | None:
    ensure_schema(db_path)
    with _connect(db_path) as conn:
        row = conn.execute("SELECT target_url FROM url_mappings WHERE code = ?", (code,)).fetchone()
    return row[0] if row else None

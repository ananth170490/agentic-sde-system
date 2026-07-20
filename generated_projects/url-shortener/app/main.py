from __future__ import annotations

import os
import secrets

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl

from app.analytics import AnalyticsService
from app.store import UrlStore


class ShortenRequest(BaseModel):
    target_url: HttpUrl


class ShortenResponse(BaseModel):
    code: str
    short_url: str


def _new_code() -> str:
    return secrets.token_urlsafe(6)[:8]


def create_app(db_path: str | None = None) -> FastAPI:
    app = FastAPI(title="URL Shortener", version="1.0.0")
    store = UrlStore(db_path or os.getenv("URL_SHORTENER_DB", "url_shortener.db"))
    analytics = AnalyticsService(store)

    @app.post("/api/v1/shorten", response_model=ShortenResponse, status_code=201)
    def shorten(payload: ShortenRequest) -> ShortenResponse:
        code = _new_code()
        for _ in range(10):
            if store.get_url(code) is None:
                break
            code = _new_code()
        else:
            raise HTTPException(status_code=500, detail="Failed to generate unique code")

        store.save_url(code, str(payload.target_url))
        return ShortenResponse(code=code, short_url=f"/api/v1/{code}")

    @app.get("/api/v1/{code}")
    def resolve(code: str) -> RedirectResponse:
        target = store.get_url(code)
        if target is None:
            raise HTTPException(status_code=404, detail="Short code not found")
        store.record_click(code)
        return RedirectResponse(url=target, status_code=307)

    @app.get("/api/v1/analytics/{code}")
    def analytics_endpoint(code: str) -> dict[str, int | str]:
        target = store.get_url(code)
        if target is None:
            raise HTTPException(status_code=404, detail="Short code not found")
        return {"code": code, "clicks": analytics.clicks_for(code)}

    return app


app = create_app()

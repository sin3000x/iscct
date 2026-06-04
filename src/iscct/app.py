from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .mock_data import APP_TITLE
from .ui import render_home_page

app = FastAPI(title=APP_TITLE)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return render_home_page()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "mock", "ui": "single-screen-ct"}

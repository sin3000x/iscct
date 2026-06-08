from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .mock_data import APP_TITLE
from .ui import render_home_page

# FastAPI 应用实例，负责承载首页和健康检查接口。
app = FastAPI(title=APP_TITLE)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    """返回控制塔演示首页。

    :return: 适合直接交给浏览器渲染的 HTML 字符串。
    """
    return render_home_page()


@app.get("/api/health")
def health() -> dict[str, str]:
    """返回服务健康状态。

    :return: 描述当前服务与前端模式的状态字典。
    """
    return {"status": "ok", "mode": "mock", "ui": "single-screen-ct"}

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

UI_DIST = Path("ui/dist")


def init():
    # 设置为服务器模式
    from mdcx.server import var

    var.is_server = True

    # 使用 ServerSignals 替代 Qt Signal
    from mdcx.server.signals import signal
    from mdcx.signals import set_signal

    set_signal(signal)


def create_app() -> FastAPI:
    init()

    from mdcx.server.api.v1 import api
    from mdcx.server.ws.auth import WebSocketProtocolBearerMiddleware

    app = FastAPI(title="MDCx API", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allows all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allows all methods
        allow_headers=["*"],  # Allows all headers
    )
    app.add_middleware(WebSocketProtocolBearerMiddleware)

    app.include_router(api)

    # 前端是单页应用。原先是 `app.mount("/", StaticFiles(..., html=True))`,
    # 但那个只把目录请求映射到 index.html, 不含通配回落: 在 /tool、/results、/logs
    # 这类子路由上按 F5 会拿到 404。这里把静态资源与 SPA 回落分开处理, 并让 api/
    # 前缀保持 404 语义, 免得接口调错时拿到一坨 HTML。
    app.mount("/static", StaticFiles(directory=UI_DIST / "static"), name="static")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_index(full_path: str):
        if full_path.lstrip("/").startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        candidate = (UI_DIST / full_path).resolve()
        if full_path and UI_DIST.resolve() in candidate.parents and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(UI_DIST / "index.html")

    return app


app = create_app()

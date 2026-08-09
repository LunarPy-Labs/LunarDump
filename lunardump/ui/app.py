"""FastAPI application factory & server launcher for LunarDump Web UI."""

import asyncio
import os
import sys
import webbrowser
from pathlib import Path
from typing import Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse

from lunardump.ui.routes import router as api_router

STATIC_DIR = Path(__file__).parent / "static"


class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: str):
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                self.disconnect(connection)


ws_manager = ConnectionManager()


def create_app() -> FastAPI:
    """Create and configure FastAPI Web Dashboard application."""
    app = FastAPI(
        title="LunarDump Web Dashboard",
        description="Zero-Trust Database Backup & Live Migration Control Panel",
        version="0.4.0",
    )

    app.include_router(api_router)

    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def serve_index():
        index_file = STATIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return HTMLResponse("<h1>LunarDump Web UI Dashboard</h1><p>Static assets directory missing.</p>")

    @app.websocket("/ws/logs")
    async def websocket_logs(websocket: WebSocket):
        await ws_manager.connect(websocket)
        try:
            await websocket.send_text("🚀 Connected to LunarDump Real-Time Log Streamer\n")
            while True:
                data = await websocket.receive_text()
                # Echo / handle client messages
                await websocket.send_text(f"Received: {data}")
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)

    return app


def start_ui_server(host: str = "127.0.0.1", port: int = 8080, open_browser: bool = True):
    """Start uvicorn web server running LunarDump dashboard."""
    import uvicorn

    url = f"http://{host}:{port}"
    print(f"🚀 LunarDump Web UI Dashboard launching at {url}")

    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    app = create_app()
    uvicorn.run(app, host=host, port=port, log_level="info")

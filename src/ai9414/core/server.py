"""FastAPI server and launcher helpers."""

from __future__ import annotations

import socket
import webbrowser
from importlib import resources
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from ai9414.core.errors import AI9414Error


def find_free_port(host: str = "127.0.0.1") -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return int(sock.getsockname()[1])


def create_fastapi_app(app_instance: Any) -> FastAPI:
    api = FastAPI(title=app_instance.app_title)

    api.mount(
        "/assets",
        StaticFiles(packages=[("ai9414.frontend", "student")]),
        name="assets",
    )

    @api.get("/", include_in_schema=False)
    def index() -> HTMLResponse:
        html = resources.files("ai9414.frontend").joinpath("student").joinpath("index.html")
        return HTMLResponse(html.read_text(encoding="utf-8"))

    @api.get("/api/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "app_type": app_instance.app_type,
            "session_id": app_instance.session_id,
        }

    @api.get("/api/manifest")
    def manifest() -> dict[str, Any]:
        return app_instance.build_manifest()

    @api.get("/api/state")
    def state() -> dict[str, Any]:
        return app_instance.build_state_payload()

    @api.get("/api/trace")
    def trace() -> dict[str, Any]:
        return app_instance.get_trace_payload()

    @api.get("/api/examples")
    def examples() -> dict[str, Any]:
        return {"ok": True, "examples": app_instance.list_examples()}

    @api.get("/api/errors")
    def errors() -> dict[str, Any]:
        return app_instance.get_recent_errors()

    @api.post("/api/action")
    def action(request: dict[str, Any]) -> JSONResponse:
        payload = app_instance.handle_action(request)
        status_code = 200 if payload.get("ok", True) else 400
        return JSONResponse(payload, status_code=status_code)

    return api


class AppLauncher:
    """Launch a local FastAPI app and open the browser."""

    def __init__(
        self,
        app_instance: Any,
        *,
        host: str = "127.0.0.1",
        port: int | None = None,
        open_browser: bool = True,
    ) -> None:
        self.app_instance = app_instance
        self.host = host
        self.port = port or find_free_port(host)
        self.open_browser = open_browser
        self.url = f"http://{self.host}:{self.port}"

    def start(self) -> None:
        self._log_startup()
        self._open_browser_if_possible()
        uvicorn.run(
            create_fastapi_app(self.app_instance),
            host=self.host,
            port=self.port,
            log_level="warning",
        )

    def _log_startup(self) -> None:
        loaded_name = self.app_instance.config_name or self.app_instance.example_name or "default"
        print(f"app name: {self.app_instance.app_title}")
        print(f"mode: {self.app_instance.mode}")
        print(f"execution mode: {self.app_instance.execution_mode}")
        print(f"localhost url: {self.url}")
        print(f"example or config loaded: {loaded_name}")

    def _open_browser_if_possible(self) -> None:
        if not self.open_browser:
            return
        try:
            opened = webbrowser.open(self.url)
        except Exception as exc:  # pragma: no cover - platform-specific guard
            raise AI9414Error(
                code="browser_open_failed",
                message=(
                    "Could not open the browser automatically. "
                    f"Open this URL manually: {self.url}"
                ),
                details={"exception_type": type(exc).__name__, "url": self.url},
            ) from exc
        if not opened:
            print(f"Could not open the browser automatically. Open this URL manually: {self.url}")


def launch_app(app_instance: Any, *, host: str = "127.0.0.1", port: int | None = None) -> None:
    launcher = AppLauncher(app_instance, host=host, port=port)
    launcher.start()

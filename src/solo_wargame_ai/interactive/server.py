"""Small stdlib HTTP server for local interactive play sessions."""

from __future__ import annotations

import json
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from .session import PlaySession, PlaySessionError

STATIC_DIR = Path(__file__).resolve().parent / "static"

_STATIC_CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
}
_STATIC_FILES = frozenset({"index.html", "app.js", "styles.css"})


class RequestPayloadError(ValueError):
    """Raised when a JSON request body is malformed for this server contract."""


class PlaySessionHTTPServer(ThreadingHTTPServer):
    """HTTP server carrying one in-memory play session."""

    allow_reuse_address = True

    def __init__(
        self,
        server_address: tuple[str, int],
        session: PlaySession,
        *,
        static_dir: Path = STATIC_DIR,
    ) -> None:
        super().__init__(server_address, PlaySessionRequestHandler)
        self.session = session
        self.session_lock = threading.Lock()
        self.static_dir = static_dir


class PlaySessionRequestHandler(BaseHTTPRequestHandler):
    """Request handler for the local play-session JSON and static endpoints."""

    server: PlaySessionHTTPServer

    def do_GET(self) -> None:
        """Serve the app shell, static assets, or current state."""

        parsed = urlparse(self.path)
        if parsed.path == "/state":
            with self.server.session_lock:
                self._send_json(self.server.session.current_view())
            return

        static_path = self._resolve_static_path(parsed.path)
        if static_path is not None:
            self._send_static_file(static_path)
            return

        self._send_json(
            _error_payload("not_found", f"No endpoint for GET {parsed.path}"),
            status=HTTPStatus.NOT_FOUND,
        )

    def do_POST(self) -> None:
        """Handle action application and session reset."""

        parsed = urlparse(self.path)
        try:
            payload = self._read_json_body()
            if parsed.path == "/action":
                self._handle_action(payload)
                return
            if parsed.path == "/reset":
                self._handle_reset(payload)
                return
        except RequestPayloadError as exc:
            self._send_json(
                _error_payload("bad_request", str(exc)),
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        self._send_json(
            _error_payload("not_found", f"No endpoint for POST {parsed.path}"),
            status=HTTPStatus.NOT_FOUND,
        )

    def log_message(self, format: str, *args: Any) -> None:
        """Keep the local CLI output focused on the server URL."""

    def _handle_action(self, payload: object) -> None:
        if not isinstance(payload, dict):
            raise RequestPayloadError("Request body must be a JSON object")

        action_id = payload.get("action_id")
        if not isinstance(action_id, str) or not action_id:
            raise RequestPayloadError("POST /action requires a non-empty action_id string")

        try:
            with self.server.session_lock:
                view = self.server.session.apply_ui_action(action_id)
        except PlaySessionError as exc:
            self._send_json(exc.to_payload(), status=HTTPStatus(exc.status_code))
            return

        self._send_json(view)

    def _handle_reset(self, payload: object) -> None:
        if payload is None:
            payload = {}
        if not isinstance(payload, dict):
            raise RequestPayloadError("Request body must be a JSON object")

        seed = payload.get("seed")
        if seed is not None and (not isinstance(seed, int) or isinstance(seed, bool)):
            raise RequestPayloadError("POST /reset seed must be an integer when supplied")

        with self.server.session_lock:
            view = self.server.session.reset(seed=seed)
        self._send_json(view)

    def _read_json_body(self) -> object:
        content_length = self.headers.get("Content-Length")
        if content_length is None:
            return {}

        try:
            length = int(content_length)
        except ValueError as exc:
            raise RequestPayloadError("Content-Length must be an integer") from exc

        if length == 0:
            return {}
        if length < 0:
            raise RequestPayloadError("Content-Length must not be negative")

        raw_body = self.rfile.read(length)
        try:
            return json.loads(raw_body.decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise RequestPayloadError("Request body must be UTF-8 JSON") from exc
        except json.JSONDecodeError as exc:
            raise RequestPayloadError(f"Request body must be valid JSON: {exc.msg}") from exc

    def _resolve_static_path(self, request_path: str) -> Path | None:
        if request_path in ("", "/", "/index.html"):
            file_name = "index.html"
        elif request_path.startswith("/static/"):
            file_name = unquote(request_path.removeprefix("/static/"))
        else:
            return None

        if file_name not in _STATIC_FILES:
            return None

        static_path = (self.server.static_dir / file_name).resolve()
        if self.server.static_dir.resolve() not in static_path.parents:
            return None
        return static_path

    def _send_static_file(self, static_path: Path) -> None:
        if not static_path.is_file():
            self._send_json(
                _error_payload("not_found", f"Missing static file {static_path.name}"),
                status=HTTPStatus.NOT_FOUND,
            )
            return

        body = static_path.read_bytes()
        content_type = _STATIC_CONTENT_TYPES.get(
            static_path.suffix,
            "application/octet-stream",
        )
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(
        self,
        payload: object,
        *,
        status: HTTPStatus = HTTPStatus.OK,
    ) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def create_play_session_server(
    session: PlaySession,
    *,
    host: str,
    port: int,
    static_dir: Path = STATIC_DIR,
) -> PlaySessionHTTPServer:
    """Create a configured local play-session server without starting it."""

    return PlaySessionHTTPServer((host, port), session, static_dir=static_dir)


def serve_play_session(
    session: PlaySession,
    *,
    host: str,
    port: int,
    static_dir: Path = STATIC_DIR,
) -> None:
    """Serve a play session until interrupted."""

    server = create_play_session_server(
        session,
        host=host,
        port=port,
        static_dir=static_dir,
    )
    try:
        server.serve_forever()
    finally:
        server.server_close()


def server_url(server: PlaySessionHTTPServer) -> str:
    """Return the browser URL for a created play-session server."""

    host, port = server.server_address[:2]
    display_host = "127.0.0.1" if host in ("", "0.0.0.0") else host
    return f"http://{display_host}:{port}"


def _error_payload(code: str, message: str) -> dict[str, object]:
    return {
        "error": {
            "code": code,
            "message": message,
        },
    }


__all__ = [
    "PlaySessionHTTPServer",
    "PlaySessionRequestHandler",
    "RequestPayloadError",
    "create_play_session_server",
    "serve_play_session",
    "server_url",
]

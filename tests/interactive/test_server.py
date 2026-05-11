from __future__ import annotations

import io
import json
import threading
from http import HTTPStatus
from types import SimpleNamespace

from solo_wargame_ai.interactive import PlaySession
from solo_wargame_ai.interactive.server import STATIC_DIR, PlaySessionRequestHandler


def test_handler_returns_state_applies_actions_and_reports_stale_ids(mission) -> None:
    session = PlaySession(mission, default_seed=0)

    state_handler = _handler(session, "GET", "/state")
    state_handler.do_GET()

    assert state_handler.status == HTTPStatus.OK
    assert state_handler.payload["mission"]["id"] == "mission_01_secure_the_woods_1"
    action_id = state_handler.payload["legal_actions"][0]["id"]

    action_handler = _handler(session, "POST", "/action", {"action_id": action_id})
    action_handler.do_POST()

    assert action_handler.status == HTTPStatus.OK
    assert action_handler.payload["session"]["decision_step_count"] == 1
    assert action_handler.payload["pending_decision"]["kind"] == "choose_double_choice"

    stale_handler = _handler(session, "POST", "/action", {"action_id": action_id})
    stale_handler.do_POST()

    assert stale_handler.status == HTTPStatus.CONFLICT
    assert stale_handler.payload["error"]["code"] == "stale_action_id"

    reset_handler = _handler(session, "POST", "/reset", {"seed": 7})
    reset_handler.do_POST()

    assert reset_handler.status == HTTPStatus.OK
    assert reset_handler.payload["session"]["seed"] == 7
    assert reset_handler.payload["session"]["decision_step_count"] == 0


def test_handler_serves_the_static_browser_shell(mission) -> None:
    session = PlaySession(mission, default_seed=0)
    handler = _handler(session, "GET", "/")

    handler.do_GET()

    assert handler.status == HTTPStatus.OK
    assert handler.content_type == "text/html; charset=utf-8"
    assert b'<svg id="map-svg"' in handler.payload


class _HarnessHandler(PlaySessionRequestHandler):
    status: HTTPStatus
    payload: object
    content_type: str

    def _send_json(
        self,
        payload: object,
        *,
        status: HTTPStatus = HTTPStatus.OK,
    ) -> None:
        self.status = status
        self.payload = payload
        self.content_type = "application/json; charset=utf-8"

    def _send_static_file(self, static_path) -> None:
        self.status = HTTPStatus.OK
        self.payload = static_path.read_bytes()
        self.content_type = "text/html; charset=utf-8"


def _handler(
    session: PlaySession,
    method: str,
    path: str,
    payload: object | None = None,
) -> _HarnessHandler:
    handler = object.__new__(_HarnessHandler)
    handler.server = SimpleNamespace(
        session=session,
        session_lock=threading.Lock(),
        static_dir=STATIC_DIR,
    )
    handler.command = method
    handler.path = path
    body = b"" if payload is None else json.dumps(payload).encode("utf-8")
    handler.headers = {"Content-Length": str(len(body))}
    handler.rfile = io.BytesIO(body)
    return handler

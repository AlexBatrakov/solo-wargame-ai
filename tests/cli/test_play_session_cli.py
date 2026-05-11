from __future__ import annotations

from pathlib import Path

from solo_wargame_ai.cli import play_session


def test_cli_loads_mission_and_serves_until_interrupted(monkeypatch, capsys) -> None:
    calls: dict[str, object] = {}
    mission_path = Path("configs/missions/mission_01_secure_the_woods_1.toml")

    class FakeMission:
        name = "Mission 1 - Secure the Woods (1)"

    class FakeSession:
        def __init__(self, mission: object, *, default_seed: int) -> None:
            calls["session_mission"] = mission
            calls["session_seed"] = default_seed

    class FakeServer:
        server_address = ("127.0.0.1", 8766)

        def serve_forever(self) -> None:
            calls["served"] = True
            raise KeyboardInterrupt

        def server_close(self) -> None:
            calls["closed"] = True

    def fake_load_mission(path: Path) -> FakeMission:
        calls["mission_path"] = path
        return FakeMission()

    def fake_create_server(session: object, *, host: str, port: int) -> FakeServer:
        calls["server_session"] = session
        calls["host"] = host
        calls["port"] = port
        return FakeServer()

    monkeypatch.setattr(play_session, "load_mission", fake_load_mission)
    monkeypatch.setattr(play_session, "PlaySession", FakeSession)
    monkeypatch.setattr(play_session, "create_play_session_server", fake_create_server)

    exit_code = play_session.main(
        [
            "--mission",
            str(mission_path),
            "--seed",
            "7",
            "--host",
            "127.0.0.1",
            "--port",
            "8766",
        ],
    )

    assert exit_code == 0
    assert calls["mission_path"] == mission_path
    assert calls["session_seed"] == 7
    assert calls["host"] == "127.0.0.1"
    assert calls["port"] == 8766
    assert calls["served"] is True
    assert calls["closed"] is True

    output = capsys.readouterr().out
    assert "Interactive play session: http://127.0.0.1:8766" in output
    assert "Mission: Mission 1 - Secure the Woods (1)" in output
    assert "Seed: 7" in output
    assert "Stopped interactive play session." in output

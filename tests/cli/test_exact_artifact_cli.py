from __future__ import annotations

import json
from pathlib import Path

from solo_wargame_ai.cli import exact_artifact

MISSION1_PATH = (
    Path(__file__).resolve().parents[2]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def test_build_command_uses_default_artifact_dir(
    monkeypatch,
    tmp_path,
    capsys,
) -> None:
    default_dir = tmp_path / "default-exact"
    payload = {"artifact": "exact", "status": "built"}

    def fake_default_exact_artifact_dir(mission_path: Path) -> Path:
        assert mission_path == MISSION1_PATH
        return default_dir

    def fake_build_exact_artifact(**kwargs):  # type: ignore[no-untyped-def]
        assert kwargs["mission_path"] == MISSION1_PATH
        assert kwargs["artifact_dir"] == default_dir
        assert kwargs["store_action_values"] is True
        return payload

    monkeypatch.setattr(
        exact_artifact,
        "default_exact_artifact_dir",
        fake_default_exact_artifact_dir,
    )
    monkeypatch.setattr(
        exact_artifact,
        "build_exact_artifact",
        fake_build_exact_artifact,
    )

    exit_code = exact_artifact.main(
        [
            "build",
            "--mission",
            str(MISSION1_PATH),
            "--store-action-values",
        ],
    )

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out) == payload


def test_stats_and_verify_commands_emit_json_payloads(
    monkeypatch,
    tmp_path,
    capsys,
) -> None:
    artifact_dir = tmp_path / "artifact"

    class FakeVerification:
        def to_payload(self) -> dict[str, object]:
            return {"mode": "verify", "ok": True}

    monkeypatch.setattr(
        exact_artifact,
        "read_exact_artifact_stats",
        lambda path: {"mode": "stats", "artifact_dir": str(path)},
    )
    monkeypatch.setattr(
        exact_artifact,
        "verify_exact_artifact",
        lambda path: FakeVerification(),
    )

    stats_exit_code = exact_artifact.main(
        ["stats", "--artifact-dir", str(artifact_dir)],
    )
    assert stats_exit_code == 0
    assert json.loads(capsys.readouterr().out) == {
        "mode": "stats",
        "artifact_dir": str(artifact_dir),
    }

    verify_exit_code = exact_artifact.main(
        ["verify", "--artifact-dir", str(artifact_dir)],
    )
    assert verify_exit_code == 0
    assert json.loads(capsys.readouterr().out) == {"mode": "verify", "ok": True}

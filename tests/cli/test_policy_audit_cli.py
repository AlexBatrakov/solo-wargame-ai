from __future__ import annotations

import json
from pathlib import Path

from solo_wargame_ai.cli import policy_audit

MISSION1_PATH = (
    Path(__file__).resolve().parents[2]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def test_build_command_uses_explicit_loader_and_default_artifact_dir(
    monkeypatch,
    tmp_path,
    capsys,
) -> None:
    default_dir = tmp_path / "default-policy"
    sentinel_agent = object()
    payload = {"artifact": "policy-audit", "status": "built"}

    def fake_validate_agent_loader_spec(spec, *, require_loader: bool) -> None:  # type: ignore[no-untyped-def]
        assert spec.agent_factory == "pkg:make_agent"
        assert require_loader is True

    def fake_build_explicit_agent_factory(spec):  # type: ignore[no-untyped-def]
        assert spec.agent_factory == "pkg:make_agent"
        return lambda: sentinel_agent

    def fake_resolve_explicit_agent_name(spec, *, agent_factory):  # type: ignore[no-untyped-def]
        assert spec.agent_factory == "pkg:make_agent"
        assert agent_factory() is sentinel_agent
        return "loaded-agent"

    def fake_default_policy_audit_dir(mission_path: Path, agent_name: str) -> Path:
        assert mission_path == MISSION1_PATH
        assert agent_name == "loaded-agent"
        return default_dir

    def fake_build_policy_audit_artifact(**kwargs):  # type: ignore[no-untyped-def]
        assert kwargs["mission_path"] == MISSION1_PATH
        assert kwargs["artifact_dir"] == default_dir
        assert kwargs["agent_name"] == "loaded-agent"
        assert kwargs["build_agent"]() is sentinel_agent
        assert kwargs["store_action_values"] is True
        return payload

    monkeypatch.setattr(
        policy_audit,
        "validate_agent_loader_spec",
        fake_validate_agent_loader_spec,
    )
    monkeypatch.setattr(
        policy_audit,
        "build_explicit_agent_factory",
        fake_build_explicit_agent_factory,
    )
    monkeypatch.setattr(
        policy_audit,
        "resolve_explicit_agent_name",
        fake_resolve_explicit_agent_name,
    )
    monkeypatch.setattr(
        policy_audit,
        "default_policy_audit_dir",
        fake_default_policy_audit_dir,
    )
    monkeypatch.setattr(
        policy_audit,
        "build_policy_audit_artifact",
        fake_build_policy_audit_artifact,
    )

    exit_code = policy_audit.main(
        [
            "build",
            "--mission",
            str(MISSION1_PATH),
            "--agent-factory",
            "pkg:make_agent",
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
        policy_audit,
        "read_policy_audit_stats",
        lambda path: {"mode": "stats", "artifact_dir": str(path)},
    )
    monkeypatch.setattr(
        policy_audit,
        "verify_policy_audit_artifact",
        lambda path: FakeVerification(),
    )

    stats_exit_code = policy_audit.main(
        ["stats", "--artifact-dir", str(artifact_dir)],
    )
    assert stats_exit_code == 0
    assert json.loads(capsys.readouterr().out) == {
        "mode": "stats",
        "artifact_dir": str(artifact_dir),
    }

    verify_exit_code = policy_audit.main(
        ["verify", "--artifact-dir", str(artifact_dir)],
    )
    assert verify_exit_code == 0
    assert json.loads(capsys.readouterr().out) == {"mode": "verify", "ok": True}

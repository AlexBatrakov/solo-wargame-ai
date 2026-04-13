from __future__ import annotations

import io
import json
import sys
from pathlib import Path

from solo_wargame_ai.cli import episode_batch_runner
from solo_wargame_ai.eval.episode_batch_runner import (
    BUILTIN_POLICY_EXACT_GUIDED_HEURISTIC,
    BUILTIN_POLICY_HEURISTIC,
    EPISODE_BATCH_OPERATION,
    RUNNER_SCHEMA_VERSION,
)

MISSION1_PATH = (
    Path(__file__).resolve().parents[2]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)
MISSION3_PATH = (
    Path(__file__).resolve().parents[2]
    / "configs"
    / "missions"
    / "mission_03_secure_the_building.toml"
)


def _base_request_payload() -> dict[str, object]:
    return {
        "schema_version": RUNNER_SCHEMA_VERSION,
        "operation": EPISODE_BATCH_OPERATION,
        "mission_path": str(MISSION1_PATH),
        "policy": {
            "kind": "builtin",
            "name": BUILTIN_POLICY_HEURISTIC,
        },
        "seed_spec": {
            "kind": "range",
            "start": 0,
            "stop": 2,
        },
    }


def test_cli_reads_request_from_stdin_and_emits_json_result(
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(_base_request_payload())))

    exit_code = episode_batch_runner.main([])

    assert exit_code == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == RUNNER_SCHEMA_VERSION
    assert payload["status"] == "succeeded"
    assert payload["operation"] == EPISODE_BATCH_OPERATION
    assert payload["metrics"]["episode_count"] == 2
    assert payload["execution"]["mission_path"] == str(MISSION1_PATH.resolve())
    assert payload["artifacts"] == []
    assert payload["warnings"] == []


def test_cli_request_file_materializes_artifacts_and_episode_rows(
    tmp_path: Path,
    capsys,
) -> None:
    artifact_dir = tmp_path / "outputs" / "episode-batch"
    request_payload = _base_request_payload()
    request_payload["artifact_dir"] = str(artifact_dir)
    request_payload["write_episode_rows"] = True

    request_file = tmp_path / "request.json"
    request_file.write_text(json.dumps(request_payload), encoding="utf-8")

    exit_code = episode_batch_runner.main(["--request-file", str(request_file)])

    assert exit_code == 0
    assert artifact_dir.is_dir()

    stdout_payload = json.loads(capsys.readouterr().out)
    assert stdout_payload["status"] == "succeeded"
    assert stdout_payload["artifacts"] == [
        {
            "kind": "request",
            "path": str(artifact_dir / "request.json"),
            "format": "json",
            "description": "normalized episode-batch request payload",
        },
        {
            "kind": "episode_rows",
            "path": str(artifact_dir / "episodes.jsonl"),
            "format": "jsonl",
            "description": "one row per completed episode",
            "episode_count": 2,
        },
        {
            "kind": "result",
            "path": str(artifact_dir / "result.json"),
            "format": "json",
            "description": "machine-readable episode-batch result payload",
        },
    ]
    assert json.loads((artifact_dir / "request.json").read_text(encoding="utf-8")) == {
        **_base_request_payload(),
        "artifact_dir": str(artifact_dir.resolve()),
        "write_episode_rows": True,
        "mission_path": str(MISSION1_PATH.resolve()),
    }
    assert json.loads((artifact_dir / "result.json").read_text(encoding="utf-8")) == (
        stdout_payload
    )

    episode_rows = [
        json.loads(line)
        for line in (artifact_dir / "episodes.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert len(episode_rows) == 2
    assert [row["seed"] for row in episode_rows] == [0, 1]


def test_cli_preserves_machine_readable_failure_result(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    artifact_dir = tmp_path / "failure-artifacts"
    request_payload = {
        "schema_version": RUNNER_SCHEMA_VERSION,
        "operation": EPISODE_BATCH_OPERATION,
        "mission_path": str(MISSION3_PATH),
        "policy": {
            "kind": "builtin",
            "name": BUILTIN_POLICY_EXACT_GUIDED_HEURISTIC,
        },
        "seed_spec": {
            "kind": "range",
            "start": 0,
            "stop": 2,
        },
        "artifact_dir": str(artifact_dir),
    }
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(request_payload)))

    exit_code = episode_batch_runner.main([])

    assert exit_code == 1

    stdout_payload = json.loads(capsys.readouterr().out)
    assert stdout_payload["status"] == "failed"
    assert stdout_payload["error"]["kind"] == "policy_resolution_error"
    assert "does not support mission" in stdout_payload["error"]["message"]
    assert stdout_payload["artifacts"] == [
        {
            "kind": "request",
            "path": str(artifact_dir / "request.json"),
            "format": "json",
            "description": "normalized episode-batch request payload",
        },
        {
            "kind": "result",
            "path": str(artifact_dir / "result.json"),
            "format": "json",
            "description": "machine-readable episode-batch result payload",
        },
    ]
    assert json.loads((artifact_dir / "result.json").read_text(encoding="utf-8")) == (
        stdout_payload
    )

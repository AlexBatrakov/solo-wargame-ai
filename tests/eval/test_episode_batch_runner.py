from __future__ import annotations

from pathlib import Path

import pytest

from solo_wargame_ai.agents.heuristic_agent import HeuristicAgent
from solo_wargame_ai.eval.episode_batch_runner import (
    BUILTIN_POLICY_EXACT_GUIDED_HEURISTIC,
    BUILTIN_POLICY_HEURISTIC,
    BUILTIN_POLICY_RANDOM,
    EPISODE_BATCH_OPERATION,
    RUNNER_SCHEMA_VERSION,
    BuiltinPolicySpec,
    EpisodeBatchFailureResult,
    EpisodeBatchPolicyResolutionError,
    EpisodeBatchRequestValidationError,
    EpisodeBatchSuccessResult,
    RangeSeedSpec,
    episode_batch_request_from_payload,
    resolve_builtin_policy,
    resolve_episode_batch_seeds,
    run_episode_batch,
    run_episode_batch_from_payload,
)
from solo_wargame_ai.eval.episode_runner import run_episodes
from solo_wargame_ai.eval.metrics import aggregate_episode_results
from solo_wargame_ai.io.mission_loader import load_mission

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
            "stop": 4,
        },
    }


def test_episode_batch_request_from_payload_normalizes_the_v1_contract() -> None:
    request = episode_batch_request_from_payload(_base_request_payload())

    assert request.schema_version == RUNNER_SCHEMA_VERSION
    assert request.operation == EPISODE_BATCH_OPERATION
    assert request.mission_path == MISSION1_PATH.resolve()
    assert request.policy.kind == "builtin"
    assert request.policy.name == BUILTIN_POLICY_HEURISTIC
    assert request.seed_spec == RangeSeedSpec(kind="range", start=0, stop=4)
    assert request.artifact_dir is None
    assert request.write_episode_rows is False


def test_episode_batch_request_rejects_episode_rows_without_artifact_dir() -> None:
    payload = _base_request_payload()
    payload["write_episode_rows"] = True

    with pytest.raises(
        EpisodeBatchRequestValidationError,
        match="write_episode_rows requires artifact_dir",
    ):
        episode_batch_request_from_payload(payload)


def test_resolve_episode_batch_seeds_preserves_explicit_seed_lists() -> None:
    payload = _base_request_payload()
    payload["policy"] = {
        "kind": "builtin",
        "name": BUILTIN_POLICY_RANDOM,
    }
    payload["seed_spec"] = {
        "kind": "list",
        "seeds": [7, 3, 7],
    }

    request = episode_batch_request_from_payload(payload)

    assert resolve_episode_batch_seeds(request.seed_spec) == (7, 3, 7)


def test_resolve_builtin_policy_rejects_incompatible_mission3_exact_guided_use() -> None:
    mission = load_mission(MISSION3_PATH)

    with pytest.raises(
        EpisodeBatchPolicyResolutionError,
        match="does not support mission",
    ):
        resolve_builtin_policy(
            BuiltinPolicySpec(
                kind="builtin",
                name=BUILTIN_POLICY_EXACT_GUIDED_HEURISTIC,
            ),
            mission=mission,
        )


def test_run_episode_batch_uses_the_accepted_episode_runner_and_metrics_seam() -> None:
    request = episode_batch_request_from_payload(_base_request_payload())

    result = run_episode_batch(request)
    second_result = run_episode_batch(request)

    assert isinstance(result, EpisodeBatchSuccessResult)
    assert isinstance(second_result, EpisodeBatchSuccessResult)

    mission = load_mission(MISSION1_PATH)
    expected_runs = run_episodes(
        mission,
        agent_factory=lambda seed: HeuristicAgent(),
        seeds=(0, 1, 2, 3),
    )
    expected_metrics = aggregate_episode_results(run.result for run in expected_runs)

    assert result.metrics == expected_metrics
    assert second_result.metrics == expected_metrics

    payload = result.to_payload()
    assert payload["schema_version"] == RUNNER_SCHEMA_VERSION
    assert payload["status"] == "succeeded"
    assert payload["operation"] == EPISODE_BATCH_OPERATION
    assert payload["metrics"]["agent_name"] == HeuristicAgent.name
    assert payload["execution"]["mission_id"] == "mission_01_secure_the_woods_1"
    assert payload["execution"]["mission_path"] == str(MISSION1_PATH.resolve())
    assert payload["execution"]["policy"] == {
        "kind": "builtin",
        "name": BUILTIN_POLICY_HEURISTIC,
        "resolved_agent_name": HeuristicAgent.name,
    }
    assert payload["execution"]["seed_spec"] == {
        "kind": "range",
        "start": 0,
        "stop": 4,
    }
    assert payload["execution"]["resolved_seed_count"] == 4
    assert isinstance(payload["execution"]["python_version"], str)
    assert isinstance(payload["execution"]["duration_sec"], float)
    assert payload["artifacts"] == []
    assert payload["warnings"] == []


def test_run_episode_batch_from_payload_reports_policy_resolution_failures() -> None:
    result = run_episode_batch_from_payload(
        {
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
        },
    )

    assert isinstance(result, EpisodeBatchFailureResult)

    payload = result.to_payload()
    assert payload["schema_version"] == RUNNER_SCHEMA_VERSION
    assert payload["status"] == "failed"
    assert payload["operation"] == EPISODE_BATCH_OPERATION
    assert payload["execution"]["mission_id"] == "mission_03_secure_the_building"
    assert payload["execution"]["mission_path"] == str(MISSION3_PATH.resolve())
    assert payload["execution"]["policy"]["kind"] == "builtin"
    assert (
        payload["execution"]["policy"]["name"]
        == BUILTIN_POLICY_EXACT_GUIDED_HEURISTIC
    )
    assert payload["execution"]["seed_spec"] == {
        "kind": "range",
        "start": 0,
        "stop": 2,
    }
    assert payload["artifacts"] == []
    assert payload["warnings"] == []
    assert payload["error"]["kind"] == "policy_resolution_error"
    assert "does not support mission" in payload["error"]["message"]


def test_run_episode_batch_from_payload_reports_request_validation_failures() -> None:
    result = run_episode_batch_from_payload(
        {
            "schema_version": "unsupported_schema",
            "operation": EPISODE_BATCH_OPERATION,
        },
    )

    assert isinstance(result, EpisodeBatchFailureResult)

    payload = result.to_payload()
    assert payload["schema_version"] == "unsupported_schema"
    assert payload["status"] == "failed"
    assert payload["operation"] == EPISODE_BATCH_OPERATION
    assert payload["artifacts"] == []
    assert payload["warnings"] == []
    assert payload["error"]["kind"] == "request_validation_error"
    assert "schema_version must be" in payload["error"]["message"]

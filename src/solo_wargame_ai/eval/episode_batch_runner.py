"""Versioned contract core for orchestration-facing episode batches.

This module intentionally stays at the library/contract layer:

- request and result payloads are machine-readable and versioned
- builtin policy loading stays narrow and explicit
- execution builds on the accepted mission-loader, episode-runner, and
  aggregate-metrics seams
- CLI transport and artifact writing remain out of scope for this core
"""

from __future__ import annotations

import platform
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from time import perf_counter
from typing import Literal, TypeAlias

from solo_wargame_ai.agents.base import AgentFactory
from solo_wargame_ai.agents.exact_guided_heuristic_agent import ExactGuidedHeuristicAgent
from solo_wargame_ai.agents.heuristic_agent import HeuristicAgent
from solo_wargame_ai.agents.random_agent import RandomAgent
from solo_wargame_ai.domain.mission import Mission
from solo_wargame_ai.eval.episode_runner import run_episodes
from solo_wargame_ai.eval.metrics import EpisodeMetrics, aggregate_episode_results
from solo_wargame_ai.io.mission_loader import load_mission

RUNNER_SCHEMA_VERSION = "solo_wargame_runner_v1"
EPISODE_BATCH_OPERATION = "episode_batch"
SUCCESS_STATUS = "succeeded"
FAILURE_STATUS = "failed"

BUILTIN_POLICY_RANDOM = "random"
BUILTIN_POLICY_HEURISTIC = "heuristic"
BUILTIN_POLICY_EXACT_GUIDED_HEURISTIC = "exact_guided_heuristic"

SUPPORTED_BUILTIN_POLICIES: tuple[str, ...] = (
    BUILTIN_POLICY_RANDOM,
    BUILTIN_POLICY_HEURISTIC,
    BUILTIN_POLICY_EXACT_GUIDED_HEURISTIC,
)

HEURISTIC_MISSION_IDS = frozenset(
    {
        "mission_01_secure_the_woods_1",
        "mission_02_secure_the_woods_2",
    },
)
EXACT_GUIDED_MISSION_IDS = frozenset(
    {
        "mission_01_secure_the_woods_1",
        "mission_02_secure_the_woods_2",
    },
)

_REPO_ROOT = Path(__file__).resolve().parents[3]


class EpisodeBatchRequestValidationError(ValueError):
    """Raised when the versioned request payload is malformed."""


class EpisodeBatchPolicyResolutionError(ValueError):
    """Raised when a builtin policy cannot be resolved for the mission."""


@dataclass(frozen=True, slots=True)
class BuiltinPolicySpec:
    """Narrow v1 policy spec for the builtin policy catalog."""

    kind: Literal["builtin"]
    name: str

    def to_payload(self) -> dict[str, str]:
        return {
            "kind": self.kind,
            "name": self.name,
        }


@dataclass(frozen=True, slots=True)
class RangeSeedSpec:
    """Half-open deterministic range seed spec."""

    kind: Literal["range"]
    start: int
    stop: int

    def to_payload(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "start": self.start,
            "stop": self.stop,
        }


@dataclass(frozen=True, slots=True)
class ListSeedSpec:
    """Explicit deterministic seed list."""

    kind: Literal["list"]
    seeds: tuple[int, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "seeds": list(self.seeds),
        }


SeedSpec: TypeAlias = RangeSeedSpec | ListSeedSpec


@dataclass(frozen=True, slots=True)
class EpisodeBatchRequest:
    """Validated request for one episode-batch execution."""

    schema_version: str
    operation: str
    mission_path: Path
    policy: BuiltinPolicySpec
    seed_spec: SeedSpec
    artifact_dir: Path | None = None
    write_episode_rows: bool = False

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "operation": self.operation,
            "mission_path": str(self.mission_path),
            "policy": self.policy.to_payload(),
            "seed_spec": self.seed_spec.to_payload(),
            "write_episode_rows": self.write_episode_rows,
        }
        if self.artifact_dir is not None:
            payload["artifact_dir"] = str(self.artifact_dir)
        return payload


@dataclass(frozen=True, slots=True)
class ArtifactManifestEntry:
    """Stable artifact manifest row shape for v1 results."""

    kind: str
    path: str
    format: str
    size_bytes: int | None = None
    description: str | None = None
    episode_count: int | None = None

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "kind": self.kind,
            "path": self.path,
            "format": self.format,
        }
        if self.size_bytes is not None:
            payload["size_bytes"] = self.size_bytes
        if self.description is not None:
            payload["description"] = self.description
        if self.episode_count is not None:
            payload["episode_count"] = self.episode_count
        return payload


@dataclass(frozen=True, slots=True)
class ResolvedPolicyInfo:
    """Execution metadata for the resolved builtin policy."""

    kind: Literal["builtin"]
    name: str
    resolved_agent_name: str | None = None

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "kind": self.kind,
            "name": self.name,
        }
        if self.resolved_agent_name is not None:
            payload["resolved_agent_name"] = self.resolved_agent_name
        return payload


@dataclass(frozen=True, slots=True)
class ExecutionMetadata:
    """Resolved execution metadata for success and partial-failure payloads."""

    mission_path: str
    policy: ResolvedPolicyInfo
    seed_spec: SeedSpec
    mission_id: str | None = None
    resolved_seed_count: int | None = None
    git_commit: str | None = None
    git_dirty: bool | None = None
    python_version: str | None = None
    duration_sec: float | None = None

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {}
        if self.mission_id is not None:
            payload["mission_id"] = self.mission_id
        payload["mission_path"] = self.mission_path
        payload["policy"] = self.policy.to_payload()
        payload["seed_spec"] = self.seed_spec.to_payload()
        if self.resolved_seed_count is not None:
            payload["resolved_seed_count"] = self.resolved_seed_count
        if self.git_commit is not None:
            payload["git_commit"] = self.git_commit
        if self.git_dirty is not None:
            payload["git_dirty"] = self.git_dirty
        if self.python_version is not None:
            payload["python_version"] = self.python_version
        if self.duration_sec is not None:
            payload["duration_sec"] = self.duration_sec
        return payload


@dataclass(frozen=True, slots=True)
class EpisodeBatchError:
    """Machine-readable failure details."""

    kind: str
    message: str
    failed_seed: int | None = None
    completed_episode_count: int | None = None

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "kind": self.kind,
            "message": self.message,
        }
        if self.failed_seed is not None:
            payload["failed_seed"] = self.failed_seed
        if self.completed_episode_count is not None:
            payload["completed_episode_count"] = self.completed_episode_count
        return payload


@dataclass(frozen=True, slots=True)
class EpisodeBatchSuccessResult:
    """Success payload contract for one episode-batch execution."""

    schema_version: str
    status: Literal["succeeded"]
    operation: str
    metrics: EpisodeMetrics
    execution: ExecutionMetadata
    artifacts: tuple[ArtifactManifestEntry, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "operation": self.operation,
            "metrics": _episode_metrics_payload(self.metrics),
            "execution": self.execution.to_payload(),
            "artifacts": [artifact.to_payload() for artifact in self.artifacts],
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True, slots=True)
class EpisodeBatchFailureResult:
    """Failure payload contract for one episode-batch execution."""

    schema_version: str
    status: Literal["failed"]
    operation: str
    error: EpisodeBatchError
    execution: ExecutionMetadata | None = None
    artifacts: tuple[ArtifactManifestEntry, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "status": self.status,
            "operation": self.operation,
        }
        if self.execution is not None:
            payload["execution"] = self.execution.to_payload()
        payload["artifacts"] = [artifact.to_payload() for artifact in self.artifacts]
        payload["warnings"] = list(self.warnings)
        payload["error"] = self.error.to_payload()
        return payload


EpisodeBatchRunResult: TypeAlias = EpisodeBatchSuccessResult | EpisodeBatchFailureResult


@dataclass(frozen=True, slots=True)
class _ResolvedBuiltinPolicy:
    """Internal resolved builtin policy factory plus metadata."""

    agent_factory: AgentFactory
    metadata: ResolvedPolicyInfo


def episode_batch_request_from_payload(payload: object) -> EpisodeBatchRequest:
    """Validate and normalize a versioned episode-batch request payload."""

    request = _require_object(payload, "request")
    _reject_unknown_keys(
        request,
        allowed={
            "schema_version",
            "operation",
            "mission_path",
            "policy",
            "seed_spec",
            "artifact_dir",
            "write_episode_rows",
        },
        field_name="request",
    )

    schema_version = _require_string(request, "schema_version")
    if schema_version != RUNNER_SCHEMA_VERSION:
        raise EpisodeBatchRequestValidationError(
            f"schema_version must be {RUNNER_SCHEMA_VERSION!r}",
        )

    operation = _require_string(request, "operation")
    if operation != EPISODE_BATCH_OPERATION:
        raise EpisodeBatchRequestValidationError(
            f"operation must be {EPISODE_BATCH_OPERATION!r}",
        )

    mission_path = _normalize_path(_require_string(request, "mission_path"), "mission_path")
    policy = _parse_policy_spec(request.get("policy"))
    seed_spec = _parse_seed_spec(request.get("seed_spec"))
    artifact_dir = _parse_optional_path(request.get("artifact_dir"), "artifact_dir")
    write_episode_rows = _parse_optional_bool(
        request.get("write_episode_rows"),
        "write_episode_rows",
        default=False,
    )

    if write_episode_rows and artifact_dir is None:
        raise EpisodeBatchRequestValidationError(
            "write_episode_rows requires artifact_dir",
        )

    return EpisodeBatchRequest(
        schema_version=schema_version,
        operation=operation,
        mission_path=mission_path,
        policy=policy,
        seed_spec=seed_spec,
        artifact_dir=artifact_dir,
        write_episode_rows=write_episode_rows,
    )


def resolve_episode_batch_seeds(seed_spec: SeedSpec) -> tuple[int, ...]:
    """Resolve a normalized seed spec into the deterministic episode seed list."""

    if isinstance(seed_spec, RangeSeedSpec):
        if seed_spec.stop <= seed_spec.start:
            raise EpisodeBatchRequestValidationError(
                "seed_spec.stop must be greater than seed_spec.start",
            )
        return tuple(range(seed_spec.start, seed_spec.stop))

    if not seed_spec.seeds:
        raise EpisodeBatchRequestValidationError("seed_spec.seeds must not be empty")
    return seed_spec.seeds


def resolve_builtin_policy(
    policy: BuiltinPolicySpec,
    *,
    mission: Mission,
) -> _ResolvedBuiltinPolicy:
    """Resolve a builtin policy name into a narrow agent factory."""

    if policy.name == BUILTIN_POLICY_RANDOM:
        return _ResolvedBuiltinPolicy(
            agent_factory=lambda seed: RandomAgent(seed=seed),
            metadata=ResolvedPolicyInfo(
                kind=policy.kind,
                name=policy.name,
                resolved_agent_name=RandomAgent.name,
            ),
        )

    if policy.name == BUILTIN_POLICY_HEURISTIC:
        _require_supported_mission(
            mission=mission,
            policy_name=policy.name,
            supported_mission_ids=HEURISTIC_MISSION_IDS,
        )
        return _ResolvedBuiltinPolicy(
            agent_factory=lambda seed: HeuristicAgent(),
            metadata=ResolvedPolicyInfo(
                kind=policy.kind,
                name=policy.name,
                resolved_agent_name=HeuristicAgent.name,
            ),
        )

    if policy.name == BUILTIN_POLICY_EXACT_GUIDED_HEURISTIC:
        _require_supported_mission(
            mission=mission,
            policy_name=policy.name,
            supported_mission_ids=EXACT_GUIDED_MISSION_IDS,
        )
        return _ResolvedBuiltinPolicy(
            agent_factory=lambda seed: ExactGuidedHeuristicAgent(),
            metadata=ResolvedPolicyInfo(
                kind=policy.kind,
                name=policy.name,
                resolved_agent_name=ExactGuidedHeuristicAgent.name,
            ),
        )

    supported_names = ", ".join(repr(name) for name in SUPPORTED_BUILTIN_POLICIES)
    raise EpisodeBatchPolicyResolutionError(
        f"unsupported builtin policy {policy.name!r}; supported names: {supported_names}",
    )


def run_episode_batch(request: EpisodeBatchRequest) -> EpisodeBatchRunResult:
    """Execute one validated episode-batch request end to end."""

    started_at = perf_counter()
    execution = ExecutionMetadata(
        mission_path=str(request.mission_path),
        policy=ResolvedPolicyInfo(kind=request.policy.kind, name=request.policy.name),
        seed_spec=request.seed_spec,
    )

    try:
        mission = load_mission(request.mission_path)
    except Exception as exc:
        return EpisodeBatchFailureResult(
            schema_version=request.schema_version,
            status=FAILURE_STATUS,
            operation=request.operation,
            execution=_finalize_execution_metadata(execution, started_at=started_at),
            artifacts=(),
            warnings=(),
            error=EpisodeBatchError(
                kind="mission_load_error",
                message=str(exc),
            ),
        )

    execution = replace(execution, mission_id=mission.mission_id)

    try:
        resolved_policy = resolve_builtin_policy(request.policy, mission=mission)
    except EpisodeBatchPolicyResolutionError as exc:
        return EpisodeBatchFailureResult(
            schema_version=request.schema_version,
            status=FAILURE_STATUS,
            operation=request.operation,
            execution=_finalize_execution_metadata(execution, started_at=started_at),
            artifacts=(),
            warnings=(),
            error=EpisodeBatchError(
                kind="policy_resolution_error",
                message=str(exc),
            ),
        )

    execution = replace(execution, policy=resolved_policy.metadata)

    try:
        seeds = resolve_episode_batch_seeds(request.seed_spec)
    except EpisodeBatchRequestValidationError as exc:
        return EpisodeBatchFailureResult(
            schema_version=request.schema_version,
            status=FAILURE_STATUS,
            operation=request.operation,
            execution=_finalize_execution_metadata(execution, started_at=started_at),
            artifacts=(),
            warnings=(),
            error=EpisodeBatchError(
                kind="request_validation_error",
                message=str(exc),
            ),
        )

    execution = replace(execution, resolved_seed_count=len(seeds))

    try:
        episode_runs = run_episodes(
            mission,
            agent_factory=resolved_policy.agent_factory,
            seeds=seeds,
        )
        metrics = aggregate_episode_results(run.result for run in episode_runs)
    except Exception as exc:
        return EpisodeBatchFailureResult(
            schema_version=request.schema_version,
            status=FAILURE_STATUS,
            operation=request.operation,
            execution=_finalize_execution_metadata(execution, started_at=started_at),
            artifacts=(),
            warnings=(),
            error=EpisodeBatchError(
                kind="episode_execution_error",
                message=str(exc),
                completed_episode_count=0,
            ),
        )

    return EpisodeBatchSuccessResult(
        schema_version=request.schema_version,
        status=SUCCESS_STATUS,
        operation=request.operation,
        metrics=metrics,
        execution=_finalize_execution_metadata(execution, started_at=started_at),
        artifacts=(),
        warnings=_request_warnings(request),
    )


def run_episode_batch_from_payload(payload: object) -> EpisodeBatchRunResult:
    """Parse, validate, and execute an episode-batch request payload."""

    try:
        request = episode_batch_request_from_payload(payload)
    except EpisodeBatchRequestValidationError as exc:
        return EpisodeBatchFailureResult(
            schema_version=_infer_string_field(
                payload,
                field_name="schema_version",
                default=RUNNER_SCHEMA_VERSION,
            ),
            status=FAILURE_STATUS,
            operation=_infer_string_field(
                payload,
                field_name="operation",
                default=EPISODE_BATCH_OPERATION,
            ),
            artifacts=(),
            warnings=(),
            error=EpisodeBatchError(
                kind="request_validation_error",
                message=str(exc),
            ),
        )

    return run_episode_batch(request)


def _parse_policy_spec(value: object) -> BuiltinPolicySpec:
    policy = _require_object(value, "policy")
    _reject_unknown_keys(policy, allowed={"kind", "name"}, field_name="policy")

    kind = _require_string(policy, "kind", parent="policy")
    if kind != "builtin":
        raise EpisodeBatchRequestValidationError("policy.kind must be 'builtin'")

    name = _require_string(policy, "name", parent="policy")
    return BuiltinPolicySpec(kind="builtin", name=name)


def _parse_seed_spec(value: object) -> SeedSpec:
    seed_spec = _require_object(value, "seed_spec")
    kind = _require_string(seed_spec, "kind", parent="seed_spec")

    if kind == "range":
        _reject_unknown_keys(
            seed_spec,
            allowed={"kind", "start", "stop"},
            field_name="seed_spec",
        )
        start = _require_int(seed_spec, "start", parent="seed_spec")
        stop = _require_int(seed_spec, "stop", parent="seed_spec")
        if stop <= start:
            raise EpisodeBatchRequestValidationError(
                "seed_spec.stop must be greater than seed_spec.start",
            )
        return RangeSeedSpec(kind="range", start=start, stop=stop)

    if kind == "list":
        _reject_unknown_keys(
            seed_spec,
            allowed={"kind", "seeds"},
            field_name="seed_spec",
        )
        seeds_value = seed_spec.get("seeds")
        if not isinstance(seeds_value, list):
            raise EpisodeBatchRequestValidationError("seed_spec.seeds must be an array")
        seeds = tuple(_coerce_seed(seed, index=index) for index, seed in enumerate(seeds_value))
        if not seeds:
            raise EpisodeBatchRequestValidationError("seed_spec.seeds must not be empty")
        return ListSeedSpec(kind="list", seeds=seeds)

    raise EpisodeBatchRequestValidationError("seed_spec.kind must be 'range' or 'list'")


def _coerce_seed(value: object, *, index: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise EpisodeBatchRequestValidationError(
            f"seed_spec.seeds[{index}] must be an integer",
        )
    return value


def _finalize_execution_metadata(
    execution: ExecutionMetadata,
    *,
    started_at: float,
) -> ExecutionMetadata:
    git_commit, git_dirty = _resolve_git_metadata()
    return replace(
        execution,
        git_commit=git_commit,
        git_dirty=git_dirty,
        python_version=platform.python_version(),
        duration_sec=round(perf_counter() - started_at, 6),
    )


def _resolve_git_metadata() -> tuple[str | None, bool | None]:
    try:
        commit_result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=_REPO_ROOT,
            capture_output=True,
            check=True,
            text=True,
            timeout=2.0,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        git_commit = None
    else:
        git_commit = commit_result.stdout.strip() or None

    try:
        dirty_result = subprocess.run(
            ["git", "status", "--short"],
            cwd=_REPO_ROOT,
            capture_output=True,
            check=True,
            text=True,
            timeout=2.0,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        git_dirty = None
    else:
        git_dirty = bool(dirty_result.stdout.strip())

    return git_commit, git_dirty


def _request_warnings(request: EpisodeBatchRequest) -> tuple[str, ...]:
    warnings: list[str] = []
    if request.artifact_dir is not None:
        warnings.append(
            "artifact_dir was accepted but artifact writing "
            "is not implemented by the contract core",
        )
    if request.write_episode_rows:
        warnings.append(
            "write_episode_rows was accepted but episode row artifacts "
            "are not implemented by the contract core",
        )
    return tuple(warnings)


def _require_supported_mission(
    *,
    mission: Mission,
    policy_name: str,
    supported_mission_ids: frozenset[str],
) -> None:
    if mission.mission_id not in supported_mission_ids:
        supported = ", ".join(sorted(repr(mission_id) for mission_id in supported_mission_ids))
        raise EpisodeBatchPolicyResolutionError(
            f"builtin policy {policy_name!r} does not support mission "
            f"{mission.mission_id!r}; supported missions: {supported}",
        )


def _episode_metrics_payload(metrics: EpisodeMetrics) -> dict[str, object]:
    return {
        "agent_name": metrics.agent_name,
        "episode_count": metrics.episode_count,
        "victory_count": metrics.victory_count,
        "defeat_count": metrics.defeat_count,
        "win_rate": metrics.win_rate,
        "defeat_rate": metrics.defeat_rate,
        "mean_terminal_turn": metrics.mean_terminal_turn,
        "mean_resolved_marker_count": metrics.mean_resolved_marker_count,
        "mean_removed_german_count": metrics.mean_removed_german_count,
        "mean_player_decision_count": metrics.mean_player_decision_count,
    }


def _require_object(value: object, field_name: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise EpisodeBatchRequestValidationError(f"{field_name} must be an object")
    result: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise EpisodeBatchRequestValidationError(
                f"{field_name} must use string keys",
            )
        result[key] = item
    return result


def _reject_unknown_keys(
    mapping: Mapping[str, object],
    *,
    allowed: set[str],
    field_name: str,
) -> None:
    unknown = sorted(key for key in mapping if key not in allowed)
    if unknown:
        raise EpisodeBatchRequestValidationError(
            f"{field_name} contains unsupported keys: {', '.join(unknown)}",
        )


def _require_string(
    mapping: Mapping[str, object],
    field_name: str,
    *,
    parent: str | None = None,
) -> str:
    value = mapping.get(field_name)
    full_name = field_name if parent is None else f"{parent}.{field_name}"
    if not isinstance(value, str) or not value.strip():
        raise EpisodeBatchRequestValidationError(f"{full_name} must be a non-empty string")
    return value


def _require_int(
    mapping: Mapping[str, object],
    field_name: str,
    *,
    parent: str | None = None,
) -> int:
    value = mapping.get(field_name)
    full_name = field_name if parent is None else f"{parent}.{field_name}"
    if isinstance(value, bool) or not isinstance(value, int):
        raise EpisodeBatchRequestValidationError(f"{full_name} must be an integer")
    return value


def _parse_optional_bool(
    value: object,
    field_name: str,
    *,
    default: bool,
) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise EpisodeBatchRequestValidationError(f"{field_name} must be a boolean")
    return value


def _parse_optional_path(value: object, field_name: str) -> Path | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise EpisodeBatchRequestValidationError(f"{field_name} must be a non-empty string")
    return _normalize_path(value, field_name)


def _normalize_path(value: str, field_name: str) -> Path:
    path = Path(value).expanduser()
    try:
        return path.resolve(strict=False)
    except OSError as exc:
        raise EpisodeBatchRequestValidationError(
            f"{field_name} could not be normalized: {exc}",
        ) from exc


def _infer_string_field(
    payload: object,
    *,
    field_name: str,
    default: str,
) -> str:
    if not isinstance(payload, Mapping):
        return default
    value = payload.get(field_name)
    if isinstance(value, str) and value:
        return value
    return default


__all__ = [
    "ArtifactManifestEntry",
    "BUILTIN_POLICY_EXACT_GUIDED_HEURISTIC",
    "BUILTIN_POLICY_HEURISTIC",
    "BUILTIN_POLICY_RANDOM",
    "BuiltinPolicySpec",
    "EPISODE_BATCH_OPERATION",
    "EpisodeBatchError",
    "EpisodeBatchFailureResult",
    "EpisodeBatchPolicyResolutionError",
    "EpisodeBatchRequest",
    "EpisodeBatchRequestValidationError",
    "EpisodeBatchRunResult",
    "EpisodeBatchSuccessResult",
    "ExecutionMetadata",
    "ListSeedSpec",
    "RUNNER_SCHEMA_VERSION",
    "RangeSeedSpec",
    "ResolvedPolicyInfo",
    "SUPPORTED_BUILTIN_POLICIES",
    "SeedSpec",
    "episode_batch_request_from_payload",
    "resolve_builtin_policy",
    "resolve_episode_batch_seeds",
    "run_episode_batch",
    "run_episode_batch_from_payload",
]

"""Mission-3-local aggregate summary helpers over learned-policy artifact dirs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Any

from .metrics import EpisodeMetrics
from .mission3_learned_policy_reporting import (
    MISSION3_HISTORICAL_REFERENCE_QUALIFICATION,
    accepted_mission3_historical_reference,
    episode_metrics_from_payload,
    episode_metrics_payload,
)


@dataclass(frozen=True, slots=True)
class Mission3ArtifactResult:
    """One Mission 3 learned-policy artifact dir loaded from saved outputs."""

    artifact_dir: Path
    training_seed: int
    selected_checkpoint_path: str
    eval_mode: str
    eval_metrics: EpisodeMetrics


@dataclass(frozen=True, slots=True)
class Mission3AggregateSummary:
    """Aggregate Mission 3 learned-policy view over provided artifact dirs."""

    artifact_results: tuple[Mission3ArtifactResult, ...]
    eval_mode: str
    best_wins: int
    median_wins: int | float
    random_reference_wins: int
    heuristic_reference_wins: int
    rollout_search_reference_wins: int
    transfer_signal_vs_random_reference: str
    historical_reference_qualification: str


def load_mission3_artifact_result(artifact_dir: Path) -> Mission3ArtifactResult:
    """Load one Mission 3 learned-policy result from a saved artifact dir."""

    summary_payload = json.loads(
        (artifact_dir / "training_summary.json").read_text(encoding="utf-8"),
    )
    eval_mode, eval_metrics = _load_eval_metrics(artifact_dir)
    return Mission3ArtifactResult(
        artifact_dir=artifact_dir,
        training_seed=int(summary_payload["training_seed"]),
        selected_checkpoint_path=str(summary_payload["selected_checkpoint_path"]),
        eval_mode=eval_mode,
        eval_metrics=eval_metrics,
    )


def build_mission3_aggregate_summary(
    artifact_dirs: tuple[Path, ...],
) -> Mission3AggregateSummary:
    """Summarize provided Mission 3 learned-policy artifact dirs."""

    artifact_results = tuple(load_mission3_artifact_result(path) for path in artifact_dirs)
    if not artifact_results:
        raise ValueError(
            "build_mission3_aggregate_summary requires at least one artifact dir",
        )

    eval_modes = {result.eval_mode for result in artifact_results}
    if len(eval_modes) != 1:
        raise ValueError(
            "Mission 3 aggregate summary requires one shared evaluation mode across "
            f"artifact dirs; got {sorted(eval_modes)!r}",
        )

    eval_mode = artifact_results[0].eval_mode
    historical_reference = accepted_mission3_historical_reference(eval_mode)
    wins = tuple(result.eval_metrics.victory_count for result in artifact_results)
    best_wins = max(wins)
    median_wins = median(wins)
    return Mission3AggregateSummary(
        artifact_results=tuple(
            sorted(artifact_results, key=lambda result: result.training_seed),
        ),
        eval_mode=eval_mode,
        best_wins=best_wins,
        median_wins=median_wins,
        random_reference_wins=historical_reference.random_wins,
        heuristic_reference_wins=historical_reference.heuristic_wins,
        rollout_search_reference_wins=historical_reference.rollout_search_wins,
        transfer_signal_vs_random_reference=_transfer_signal(
            best_wins=best_wins,
            median_wins=median_wins,
            random_reference_wins=historical_reference.random_wins,
        ),
        historical_reference_qualification=MISSION3_HISTORICAL_REFERENCE_QUALIFICATION,
    )


def format_mission3_aggregate_summary(summary: Mission3AggregateSummary) -> str:
    """Render a compact Mission 3 learned-policy aggregate summary."""

    result_lines = [
        (
            f"training_seed={result.training_seed} "
            f"wins={result.eval_metrics.victory_count}/"
            f"{result.eval_metrics.episode_count} "
            f"checkpoint={result.selected_checkpoint_path}"
        )
        for result in summary.artifact_results
    ]
    return "\n".join(
        (
            "Mission 3 learned-policy aggregate summary",
            f"evaluation_mode: {summary.eval_mode}",
            f"artifact_count: {len(summary.artifact_results)}",
            "Artifact results:",
            *(result_lines or ("none",)),
            "",
            "Observation-based learned surface:",
            f"best_wins: {summary.best_wins}",
            f"median_wins: {_format_win_count(summary.median_wins)}",
            (
                "transfer_signal_vs_preserved_random_reference: "
                f"{summary.transfer_signal_vs_random_reference}"
            ),
            "",
            "Preserved historical Mission 3 references:",
            (
                "historical_reference_qualification: "
                f"{summary.historical_reference_qualification}"
            ),
            f"random_wins: {summary.random_reference_wins}",
            f"heuristic_wins: {summary.heuristic_reference_wins}",
            f"rollout_search_wins: {summary.rollout_search_reference_wins}",
            "",
            "Descriptive deltas vs preserved history:",
            f"best_vs_random_reference: {summary.best_wins - summary.random_reference_wins:+d}",
            (
                "best_vs_heuristic_reference: "
                f"{summary.best_wins - summary.heuristic_reference_wins:+d}"
            ),
            (
                "best_vs_rollout_search_reference: "
                f"{summary.best_wins - summary.rollout_search_reference_wins:+d}"
            ),
            (
                "median_vs_random_reference: "
                f"{summary.median_wins - summary.random_reference_wins:+.1f}"
            ),
            (
                "median_vs_heuristic_reference: "
                f"{summary.median_wins - summary.heuristic_reference_wins:+.1f}"
            ),
            (
                "median_vs_rollout_search_reference: "
                f"{summary.median_wins - summary.rollout_search_reference_wins:+.1f}"
            ),
        ),
    )


def mission3_aggregate_summary_payload(
    summary: Mission3AggregateSummary,
) -> dict[str, Any]:
    """Build a machine-readable payload for the aggregate Mission 3 summary."""

    return {
        "artifact_results": [
            {
                "artifact_dir": str(result.artifact_dir),
                "training_seed": result.training_seed,
                "selected_checkpoint_path": result.selected_checkpoint_path,
                "eval_mode": result.eval_mode,
                "eval_metrics": episode_metrics_payload(result.eval_metrics),
            }
            for result in summary.artifact_results
        ],
        "evaluation_mode": summary.eval_mode,
        "best_wins": summary.best_wins,
        "median_wins": summary.median_wins,
        "random_reference_wins": summary.random_reference_wins,
        "heuristic_reference_wins": summary.heuristic_reference_wins,
        "rollout_search_reference_wins": summary.rollout_search_reference_wins,
        "transfer_signal_vs_preserved_random_reference": (
            summary.transfer_signal_vs_random_reference
        ),
        "historical_reference_qualification": (
            summary.historical_reference_qualification
        ),
        "best_vs_random_reference": (
            summary.best_wins - summary.random_reference_wins
        ),
        "best_vs_heuristic_reference": (
            summary.best_wins - summary.heuristic_reference_wins
        ),
        "best_vs_rollout_search_reference": (
            summary.best_wins - summary.rollout_search_reference_wins
        ),
        "median_vs_random_reference": (
            summary.median_wins - summary.random_reference_wins
        ),
        "median_vs_heuristic_reference": (
            summary.median_wins - summary.heuristic_reference_wins
        ),
        "median_vs_rollout_search_reference": (
            summary.median_wins - summary.rollout_search_reference_wins
        ),
    }


def _load_eval_metrics(artifact_dir: Path) -> tuple[str, EpisodeMetrics]:
    benchmark_json_path = artifact_dir / "benchmark_eval.json"
    smoke_json_path = artifact_dir / "smoke_eval.json"
    benchmark_report_path = artifact_dir / "benchmark_eval_report.txt"
    smoke_report_path = artifact_dir / "smoke_eval_report.txt"

    if benchmark_json_path.exists():
        payload = json.loads(benchmark_json_path.read_text(encoding="utf-8"))
        return "benchmark", episode_metrics_from_payload(payload["metrics"])
    if smoke_json_path.exists():
        payload = json.loads(smoke_json_path.read_text(encoding="utf-8"))
        return "smoke", episode_metrics_from_payload(payload["metrics"])
    if benchmark_report_path.exists():
        return "benchmark", _parse_text_eval_metrics(
            benchmark_report_path.read_text(encoding="utf-8"),
        )
    if smoke_report_path.exists():
        return "smoke", _parse_text_eval_metrics(
            smoke_report_path.read_text(encoding="utf-8"),
        )
    raise FileNotFoundError(
        "Mission 3 artifact dir is missing benchmark_eval.* or smoke_eval.* "
        f"outputs: {artifact_dir}",
    )


def _parse_text_eval_metrics(report_text: str) -> EpisodeMetrics:
    lines = report_text.splitlines()
    metrics_header_index = lines.index("Observation-based learned metrics:")
    metrics_row = lines[metrics_header_index + 2]
    parts = metrics_row.split()
    if len(parts) != 10:
        raise ValueError(f"Unexpected Mission 3 metrics row: {metrics_row!r}")
    return EpisodeMetrics(
        agent_name=parts[0],
        episode_count=int(parts[1]),
        victory_count=int(parts[2]),
        defeat_count=int(parts[3]),
        win_rate=float(parts[4]),
        defeat_rate=float(parts[5]),
        mean_terminal_turn=float(parts[6]),
        mean_resolved_marker_count=float(parts[7]),
        mean_removed_german_count=float(parts[8]),
        mean_player_decision_count=float(parts[9]),
    )


def _transfer_signal(
    *,
    best_wins: int,
    median_wins: int | float,
    random_reference_wins: int,
) -> str:
    if best_wins > random_reference_wins and median_wins > random_reference_wins:
        return "median_provided_run_above_preserved_random_reference"
    if best_wins > random_reference_wins:
        return "at_least_one_provided_run_above_preserved_random_reference"
    if best_wins == random_reference_wins:
        return "best_provided_run_matches_preserved_random_reference"
    return "no_provided_run_above_preserved_random_reference_yet"


def _format_win_count(value: int | float) -> str:
    if isinstance(value, int):
        return str(value)
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.1f}"


__all__ = [
    "Mission3AggregateSummary",
    "Mission3ArtifactResult",
    "build_mission3_aggregate_summary",
    "format_mission3_aggregate_summary",
    "load_mission3_artifact_result",
    "mission3_aggregate_summary_payload",
]

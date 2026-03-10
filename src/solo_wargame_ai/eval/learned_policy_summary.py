"""Aggregate summary helpers for the accepted learned-policy training seeds."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Any

from .learned_policy_reporting import (
    accepted_phase3_anchor,
    episode_metrics_from_payload,
    episode_metrics_payload,
)
from .learned_policy_seeds import PHASE5_TRAINING_SEEDS
from .metrics import EpisodeMetrics


@dataclass(frozen=True, slots=True)
class Phase5ArtifactResult:
    """One accepted training-seed result loaded from saved artifacts."""

    artifact_dir: Path
    training_seed: int
    selected_checkpoint_path: str
    benchmark_metrics: EpisodeMetrics


@dataclass(frozen=True, slots=True)
class Phase5AggregateSummary:
    """Aggregate Phase 5 verdict over the accepted training seeds."""

    artifact_results: tuple[Phase5ArtifactResult, ...]
    best_benchmark_wins: int
    median_benchmark_wins: int
    random_anchor_wins: int
    heuristic_anchor_wins: int
    minimum_success_met: bool
    package_c_recommendation: str


def load_phase5_artifact_result(artifact_dir: Path) -> Phase5ArtifactResult:
    """Load one final training-seed result from saved Phase 5 artifacts."""

    summary_payload = json.loads(
        (artifact_dir / "training_summary.json").read_text(encoding="utf-8"),
    )
    benchmark_json_path = artifact_dir / "benchmark_eval.json"
    benchmark_report_path = artifact_dir / "benchmark_eval_report.txt"

    if benchmark_json_path.exists():
        benchmark_payload = json.loads(benchmark_json_path.read_text(encoding="utf-8"))
        benchmark_metrics = episode_metrics_from_payload(benchmark_payload["metrics"])
    elif benchmark_report_path.exists():
        benchmark_metrics = _parse_text_eval_metrics(
            benchmark_report_path.read_text(encoding="utf-8"),
        )
    else:
        raise FileNotFoundError(
            "Phase 5 artifact dir is missing benchmark_eval.json or "
            f"benchmark_eval_report.txt: {artifact_dir}",
        )

    return Phase5ArtifactResult(
        artifact_dir=artifact_dir,
        training_seed=int(summary_payload["training_seed"]),
        selected_checkpoint_path=str(summary_payload["selected_checkpoint_path"]),
        benchmark_metrics=benchmark_metrics,
    )


def build_phase5_aggregate_summary(
    artifact_dirs: tuple[Path, ...],
) -> Phase5AggregateSummary:
    """Combine the accepted training-seed results into one final verdict."""

    artifact_results = tuple(load_phase5_artifact_result(path) for path in artifact_dirs)
    if not artifact_results:
        raise ValueError("build_phase5_aggregate_summary requires at least one artifact dir")

    loaded_training_seeds = {result.training_seed for result in artifact_results}
    missing_training_seeds = set(PHASE5_TRAINING_SEEDS) - loaded_training_seeds
    if missing_training_seeds:
        raise ValueError(
            "Phase 5 aggregate summary is missing accepted training seeds: "
            f"{sorted(missing_training_seeds)!r}",
        )

    benchmark_wins = tuple(
        result.benchmark_metrics.victory_count for result in artifact_results
    )
    anchor = accepted_phase3_anchor("benchmark")
    best_benchmark_wins = max(benchmark_wins)
    median_benchmark_wins = int(median(benchmark_wins))
    minimum_success_met = (
        best_benchmark_wins >= 50 and median_benchmark_wins > anchor.random_wins
    )
    return Phase5AggregateSummary(
        artifact_results=tuple(sorted(artifact_results, key=lambda result: result.training_seed)),
        best_benchmark_wins=best_benchmark_wins,
        median_benchmark_wins=median_benchmark_wins,
        random_anchor_wins=anchor.random_wins,
        heuristic_anchor_wins=anchor.heuristic_wins,
        minimum_success_met=minimum_success_met,
        package_c_recommendation=(
            "Package C not recommended; proceed toward end-of-phase evaluation"
            if minimum_success_met
            else "Package C recommended"
        ),
    )


def format_phase5_aggregate_summary(summary: Phase5AggregateSummary) -> str:
    """Render a compact human-readable aggregate summary."""

    result_lines = [
        (
            f"training_seed={result.training_seed} "
            f"benchmark_wins={result.benchmark_metrics.victory_count}/"
            f"{result.benchmark_metrics.episode_count} "
            f"checkpoint={result.selected_checkpoint_path}"
        )
        for result in summary.artifact_results
    ]
    return "\n".join(
        (
            "Phase 5 aggregate summary",
            f"artifact_count: {len(summary.artifact_results)}",
            "Artifact results:",
            *(result_lines or ("none",)),
            "",
            f"best_benchmark_wins: {summary.best_benchmark_wins}",
            f"median_benchmark_wins: {summary.median_benchmark_wins}",
            f"random_anchor_wins: {summary.random_anchor_wins}",
            f"heuristic_anchor_wins: {summary.heuristic_anchor_wins}",
            (
                "best_vs_random_anchor: "
                f"{summary.best_benchmark_wins - summary.random_anchor_wins:+d}"
            ),
            (
                "best_vs_heuristic_anchor: "
                f"{summary.best_benchmark_wins - summary.heuristic_anchor_wins:+d}"
            ),
            (
                "median_vs_random_anchor: "
                f"{summary.median_benchmark_wins - summary.random_anchor_wins:+d}"
            ),
            (
                "median_vs_heuristic_anchor: "
                f"{summary.median_benchmark_wins - summary.heuristic_anchor_wins:+d}"
            ),
            f"minimum_success_verdict: {'met' if summary.minimum_success_met else 'not_met'}",
            f"package_c_recommendation: {summary.package_c_recommendation}",
        ),
    )


def phase5_aggregate_summary_payload(
    summary: Phase5AggregateSummary,
) -> dict[str, Any]:
    """Build a machine-readable payload for the aggregate Phase 5 summary."""

    return {
        "artifact_results": [
            {
                "artifact_dir": str(result.artifact_dir),
                "training_seed": result.training_seed,
                "selected_checkpoint_path": result.selected_checkpoint_path,
                "benchmark_metrics": episode_metrics_payload(result.benchmark_metrics),
            }
            for result in summary.artifact_results
        ],
        "best_benchmark_wins": summary.best_benchmark_wins,
        "median_benchmark_wins": summary.median_benchmark_wins,
        "random_anchor_wins": summary.random_anchor_wins,
        "heuristic_anchor_wins": summary.heuristic_anchor_wins,
        "best_vs_random_anchor": summary.best_benchmark_wins - summary.random_anchor_wins,
        "best_vs_heuristic_anchor": (
            summary.best_benchmark_wins - summary.heuristic_anchor_wins
        ),
        "median_vs_random_anchor": (
            summary.median_benchmark_wins - summary.random_anchor_wins
        ),
        "median_vs_heuristic_anchor": (
            summary.median_benchmark_wins - summary.heuristic_anchor_wins
        ),
        "minimum_success_verdict": "met" if summary.minimum_success_met else "not_met",
        "package_c_recommendation": summary.package_c_recommendation,
    }


def _parse_text_eval_metrics(report_text: str) -> EpisodeMetrics:
    lines = report_text.splitlines()
    metrics_header_index = lines.index("Metrics table:")
    metrics_row = lines[metrics_header_index + 2]
    parts = metrics_row.split()
    if len(parts) != 10:
        raise ValueError(f"Unexpected Phase 5 metrics row: {metrics_row!r}")

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


__all__ = [
    "Phase5AggregateSummary",
    "Phase5ArtifactResult",
    "build_phase5_aggregate_summary",
    "format_phase5_aggregate_summary",
    "load_phase5_artifact_result",
    "phase5_aggregate_summary_payload",
]

"""Fixed-seed aggregation helpers over the accepted EpisodeResult surface."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean
from typing import Iterable

from solo_wargame_ai.domain.state import TerminalOutcome
from solo_wargame_ai.eval.episode_runner import EpisodeResult


@dataclass(frozen=True, slots=True)
class EpisodeMetrics:
    """Stable aggregate metrics for one fixed-seed episode batch."""

    agent_name: str
    episode_count: int
    victory_count: int
    defeat_count: int
    win_rate: float
    defeat_rate: float
    mean_terminal_turn: float
    mean_resolved_marker_count: float
    mean_removed_german_count: float
    mean_player_decision_count: float


@dataclass(frozen=True, slots=True)
class EpisodeMetricsDelta:
    """Signed metric deltas between two fixed-seed episode batches."""

    episode_count_delta: int
    victory_count_delta: int
    defeat_count_delta: int
    win_rate_delta: float
    defeat_rate_delta: float
    mean_terminal_turn_delta: float
    mean_resolved_marker_count_delta: float
    mean_removed_german_count_delta: float
    mean_player_decision_count_delta: float


def aggregate_episode_results(results: Iterable[EpisodeResult]) -> EpisodeMetrics:
    """Aggregate the accepted fixed-seed metrics from episode-level results."""

    result_tuple = tuple(results)
    if not result_tuple:
        raise ValueError("aggregate_episode_results requires at least one EpisodeResult")

    agent_names = {result.agent_name for result in result_tuple}
    if len(agent_names) != 1:
        raise ValueError("aggregate_episode_results requires exactly one agent_name")

    episode_count = len(result_tuple)
    victory_count = sum(
        1 for result in result_tuple if result.terminal_outcome is TerminalOutcome.VICTORY
    )
    defeat_count = sum(
        1 for result in result_tuple if result.terminal_outcome is TerminalOutcome.DEFEAT
    )

    return EpisodeMetrics(
        agent_name=result_tuple[0].agent_name,
        episode_count=episode_count,
        victory_count=victory_count,
        defeat_count=defeat_count,
        win_rate=victory_count / episode_count,
        defeat_rate=defeat_count / episode_count,
        mean_terminal_turn=fmean(result.terminal_turn for result in result_tuple),
        mean_resolved_marker_count=fmean(
            result.resolved_marker_count for result in result_tuple
        ),
        mean_removed_german_count=fmean(
            result.removed_german_count for result in result_tuple
        ),
        mean_player_decision_count=fmean(
            result.player_decision_count for result in result_tuple
        ),
    )


def diff_episode_metrics(
    baseline: EpisodeMetrics,
    candidate: EpisodeMetrics,
) -> EpisodeMetricsDelta:
    """Return signed deltas from ``baseline`` to ``candidate`` metrics."""

    return EpisodeMetricsDelta(
        episode_count_delta=candidate.episode_count - baseline.episode_count,
        victory_count_delta=candidate.victory_count - baseline.victory_count,
        defeat_count_delta=candidate.defeat_count - baseline.defeat_count,
        win_rate_delta=candidate.win_rate - baseline.win_rate,
        defeat_rate_delta=candidate.defeat_rate - baseline.defeat_rate,
        mean_terminal_turn_delta=(
            candidate.mean_terminal_turn - baseline.mean_terminal_turn
        ),
        mean_resolved_marker_count_delta=(
            candidate.mean_resolved_marker_count - baseline.mean_resolved_marker_count
        ),
        mean_removed_german_count_delta=(
            candidate.mean_removed_german_count - baseline.mean_removed_german_count
        ),
        mean_player_decision_count_delta=(
            candidate.mean_player_decision_count - baseline.mean_player_decision_count
        ),
    )


def format_metrics_table(metrics: Iterable[EpisodeMetrics]) -> str:
    """Render a small stable comparison table for fixed-seed reports."""

    metric_tuple = tuple(metrics)
    if not metric_tuple:
        raise ValueError("format_metrics_table requires at least one metrics row")

    header = (
        "agent       episodes wins defeats win_rate defeat_rate "
        "mean_turn mean_markers mean_removed mean_decisions"
    )
    rows = [header]
    for metric in metric_tuple:
        rows.append(
            f"{metric.agent_name:<11}"
            f"{metric.episode_count:>8} "
            f"{metric.victory_count:>4} "
            f"{metric.defeat_count:>7} "
            f"{metric.win_rate:>8.3f} "
            f"{metric.defeat_rate:>11.3f} "
            f"{metric.mean_terminal_turn:>9.3f} "
            f"{metric.mean_resolved_marker_count:>12.3f} "
            f"{metric.mean_removed_german_count:>12.3f} "
            f"{metric.mean_player_decision_count:>14.3f}"
        )
    return "\n".join(rows)

__all__ = [
    "EpisodeMetrics",
    "EpisodeMetricsDelta",
    "aggregate_episode_results",
    "diff_episode_metrics",
    "format_metrics_table",
]

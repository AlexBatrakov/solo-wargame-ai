"""Evaluation helpers for Phase 3 baseline harness work."""

from .benchmark import (
    PHASE3_BENCHMARK_SEEDS,
    BenchmarkComparison,
    BenchmarkRun,
    run_agent_benchmark,
    run_random_vs_heuristic_comparison,
    run_smoke_comparison,
)
from .episode_runner import (
    PHASE3_SMOKE_SEEDS,
    EpisodeResult,
    EpisodeRun,
    agent_name,
    run_episode,
    run_episodes,
    run_smoke_episodes,
)
from .metrics import (
    EpisodeMetrics,
    EpisodeMetricsDelta,
    aggregate_episode_results,
    diff_episode_metrics,
    format_metrics_table,
)

__all__ = [
    "BenchmarkComparison",
    "BenchmarkRun",
    "EpisodeResult",
    "EpisodeMetrics",
    "EpisodeMetricsDelta",
    "EpisodeRun",
    "PHASE3_BENCHMARK_SEEDS",
    "PHASE3_SMOKE_SEEDS",
    "aggregate_episode_results",
    "agent_name",
    "diff_episode_metrics",
    "format_metrics_table",
    "run_episode",
    "run_episodes",
    "run_agent_benchmark",
    "run_random_vs_heuristic_comparison",
    "run_smoke_comparison",
    "run_smoke_episodes",
]

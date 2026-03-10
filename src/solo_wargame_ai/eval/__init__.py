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
from .learned_policy_eval import (
    LearnedEpisodeRun,
    LearnedPolicyEvaluation,
    evaluate_learned_policy,
    evaluate_phase5_benchmark_policy,
    evaluate_phase5_smoke_policy,
    run_learned_episode,
    run_learned_episodes,
)
from .metrics import (
    EpisodeMetrics,
    EpisodeMetricsDelta,
    aggregate_episode_results,
    diff_episode_metrics,
    format_metrics_table,
)
from .phase5_seed_policy import (
    PHASE5_BENCHMARK_EVAL_SEEDS,
    PHASE5_SMOKE_EVAL_SEEDS,
    PHASE5_TRAINING_SEEDS,
    training_rollout_seed,
)

__all__ = [
    "BenchmarkComparison",
    "BenchmarkRun",
    "EpisodeResult",
    "EpisodeMetrics",
    "EpisodeMetricsDelta",
    "EpisodeRun",
    "LearnedEpisodeRun",
    "LearnedPolicyEvaluation",
    "PHASE3_BENCHMARK_SEEDS",
    "PHASE3_SMOKE_SEEDS",
    "PHASE5_BENCHMARK_EVAL_SEEDS",
    "PHASE5_SMOKE_EVAL_SEEDS",
    "PHASE5_TRAINING_SEEDS",
    "aggregate_episode_results",
    "agent_name",
    "diff_episode_metrics",
    "evaluate_learned_policy",
    "evaluate_phase5_benchmark_policy",
    "evaluate_phase5_smoke_policy",
    "format_metrics_table",
    "run_learned_episode",
    "run_learned_episodes",
    "run_episode",
    "run_episodes",
    "run_agent_benchmark",
    "run_random_vs_heuristic_comparison",
    "run_smoke_comparison",
    "run_smoke_episodes",
    "training_rollout_seed",
]

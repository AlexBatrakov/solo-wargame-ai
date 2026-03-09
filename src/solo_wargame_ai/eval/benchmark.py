"""Fixed-seed Phase 3 benchmark helpers for random vs heuristic comparison."""

from __future__ import annotations

from dataclasses import dataclass

from solo_wargame_ai.agents.heuristic_agent import HeuristicAgent
from solo_wargame_ai.agents.random_agent import RandomAgent
from solo_wargame_ai.domain.mission import Mission
from solo_wargame_ai.eval.episode_runner import PHASE3_SMOKE_SEEDS, EpisodeResult, run_episodes
from solo_wargame_ai.eval.metrics import (
    EpisodeMetrics,
    EpisodeMetricsDelta,
    aggregate_episode_results,
    diff_episode_metrics,
    format_metrics_table,
)

PHASE3_BENCHMARK_SEEDS: tuple[int, ...] = tuple(range(200))


@dataclass(frozen=True, slots=True)
class BenchmarkRun:
    """One fixed-seed batch for a single agent baseline."""

    agent_name: str
    seeds: tuple[int, ...]
    episode_results: tuple[EpisodeResult, ...]
    metrics: EpisodeMetrics


@dataclass(frozen=True, slots=True)
class BenchmarkComparison:
    """The accepted Phase 3 random-vs-heuristic comparison surface."""

    seeds: tuple[int, ...]
    random_run: BenchmarkRun
    heuristic_run: BenchmarkRun
    metric_deltas: EpisodeMetricsDelta
    report_table: str


def run_agent_benchmark(
    mission: Mission,
    *,
    agent_name: str,
    seeds: tuple[int, ...],
) -> BenchmarkRun:
    """Run one fixed-seed batch for the named baseline agent."""

    if agent_name == RandomAgent.name:
        episode_runs = run_episodes(
            mission,
            agent_factory=lambda seed: RandomAgent(seed=seed),
            seeds=seeds,
        )
    elif agent_name == HeuristicAgent.name:
        episode_runs = run_episodes(
            mission,
            agent_factory=lambda seed: HeuristicAgent(),
            seeds=seeds,
        )
    else:
        raise ValueError(f"Unsupported benchmark agent: {agent_name!r}")

    episode_results = tuple(run.result for run in episode_runs)
    return BenchmarkRun(
        agent_name=agent_name,
        seeds=seeds,
        episode_results=episode_results,
        metrics=aggregate_episode_results(episode_results),
    )


def run_random_vs_heuristic_comparison(
    mission: Mission,
    *,
    seeds: tuple[int, ...] = PHASE3_BENCHMARK_SEEDS,
) -> BenchmarkComparison:
    """Run the first comparison-ready Phase 3 baseline benchmark on identical seeds."""

    random_run = run_agent_benchmark(
        mission,
        agent_name=RandomAgent.name,
        seeds=seeds,
    )
    heuristic_run = run_agent_benchmark(
        mission,
        agent_name=HeuristicAgent.name,
        seeds=seeds,
    )
    report_table = format_metrics_table((random_run.metrics, heuristic_run.metrics))
    return BenchmarkComparison(
        seeds=seeds,
        random_run=random_run,
        heuristic_run=heuristic_run,
        metric_deltas=diff_episode_metrics(random_run.metrics, heuristic_run.metrics),
        report_table=report_table,
    )


def run_smoke_comparison(mission: Mission) -> BenchmarkComparison:
    """Run the fixed 16-seed smoke comparison used during local verification."""

    return run_random_vs_heuristic_comparison(
        mission,
        seeds=PHASE3_SMOKE_SEEDS,
    )


__all__ = [
    "BenchmarkComparison",
    "BenchmarkRun",
    "PHASE3_BENCHMARK_SEEDS",
    "run_agent_benchmark",
    "run_random_vs_heuristic_comparison",
    "run_smoke_comparison",
]

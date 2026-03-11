"""Mission 3-local comparison helpers for the active baseline/search packet."""

from __future__ import annotations

from dataclasses import dataclass

from solo_wargame_ai.agents.base import AgentFactory
from solo_wargame_ai.agents.random_agent import RandomAgent
from solo_wargame_ai.domain.mission import Mission
from solo_wargame_ai.eval.episode_runner import EpisodeResult, run_episodes
from solo_wargame_ai.eval.metrics import (
    EpisodeMetrics,
    aggregate_episode_results,
    format_metrics_table,
)

MISSION3_SMOKE_SEEDS: tuple[int, ...] = tuple(range(16))
MISSION3_BENCHMARK_SEEDS: tuple[int, ...] = tuple(range(200))


@dataclass(frozen=True, slots=True)
class Mission3BaselineRun:
    """One fixed-seed Mission 3 batch for a named baseline."""

    agent_name: str
    seeds: tuple[int, ...]
    episode_results: tuple[EpisodeResult, ...]
    metrics: EpisodeMetrics


@dataclass(frozen=True, slots=True)
class Mission3Comparison:
    """Mission-3-only comparison surface for the active packet."""

    seeds: tuple[int, ...]
    baseline_runs: tuple[Mission3BaselineRun, ...]
    report_table: str


def run_mission3_baseline(
    mission: Mission,
    *,
    agent_factory: AgentFactory,
    seeds: tuple[int, ...],
) -> Mission3BaselineRun:
    """Run one Mission 3 baseline on a fixed local seed surface."""

    episode_runs = run_episodes(
        mission,
        agent_factory=agent_factory,
        seeds=seeds,
    )
    episode_results = tuple(run.result for run in episode_runs)
    metrics = aggregate_episode_results(episode_results)
    return Mission3BaselineRun(
        agent_name=metrics.agent_name,
        seeds=seeds,
        episode_results=episode_results,
        metrics=metrics,
    )


def build_mission3_comparison(
    baseline_runs: tuple[Mission3BaselineRun, ...],
) -> Mission3Comparison:
    """Assemble a Mission-3-only comparison table from fixed-seed baseline runs."""

    if not baseline_runs:
        raise ValueError("build_mission3_comparison requires at least one baseline run")

    seed_sets = {run.seeds for run in baseline_runs}
    if len(seed_sets) != 1:
        raise ValueError("Mission 3 comparison runs must use one shared seed surface")

    return Mission3Comparison(
        seeds=baseline_runs[0].seeds,
        baseline_runs=baseline_runs,
        report_table=format_metrics_table(
            tuple(run.metrics for run in baseline_runs),
        ),
    )


def run_mission3_random_floor_comparison(
    mission: Mission,
    *,
    seeds: tuple[int, ...] = MISSION3_BENCHMARK_SEEDS,
) -> Mission3Comparison:
    """Run the deterministic Mission 3 random floor on one local seed surface."""

    return build_mission3_comparison(
        (
            run_mission3_baseline(
                mission,
                agent_factory=lambda seed: RandomAgent(seed=seed),
                seeds=seeds,
            ),
        ),
    )


def run_mission3_smoke_comparison(mission: Mission) -> Mission3Comparison:
    """Run the deterministic Mission 3 random floor on the 16-seed smoke alias."""

    return run_mission3_random_floor_comparison(
        mission,
        seeds=MISSION3_SMOKE_SEEDS,
    )


__all__ = [
    "MISSION3_BENCHMARK_SEEDS",
    "MISSION3_SMOKE_SEEDS",
    "Mission3BaselineRun",
    "Mission3Comparison",
    "build_mission3_comparison",
    "run_mission3_baseline",
    "run_mission3_random_floor_comparison",
    "run_mission3_smoke_comparison",
]

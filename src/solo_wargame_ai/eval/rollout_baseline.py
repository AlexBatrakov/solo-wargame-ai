"""Phase 6 stronger-baseline comparison helpers."""

from __future__ import annotations

from dataclasses import dataclass

from solo_wargame_ai.agents.heuristic_agent import HeuristicAgent
from solo_wargame_ai.agents.random_agent import RandomAgent
from solo_wargame_ai.agents.rollout_search_agent import RolloutSearchAgent
from solo_wargame_ai.domain.mission import Mission
from solo_wargame_ai.eval.benchmark import PHASE3_BENCHMARK_SEEDS
from solo_wargame_ai.eval.episode_runner import PHASE3_SMOKE_SEEDS, EpisodeResult, run_episodes
from solo_wargame_ai.eval.metrics import (
    EpisodeMetrics,
    EpisodeMetricsDelta,
    aggregate_episode_results,
    diff_episode_metrics,
    format_metrics_table,
)

PHASE6_RANDOM_ANCHOR_WINS = 11
PHASE6_HEURISTIC_ANCHOR_WINS = 157
PHASE6_LEARNED_BEST_WINS = 144
PHASE6_LEARNED_MEDIAN_WINS = 133


@dataclass(frozen=True, slots=True)
class Phase6AnchorReference:
    """Accepted preserved comparison anchors for the stronger baseline package."""

    random_wins: int = PHASE6_RANDOM_ANCHOR_WINS
    heuristic_wins: int = PHASE6_HEURISTIC_ANCHOR_WINS
    learned_best_wins: int = PHASE6_LEARNED_BEST_WINS
    learned_median_wins: int = PHASE6_LEARNED_MEDIAN_WINS


@dataclass(frozen=True, slots=True)
class Phase6BaselineRun:
    """One fixed-seed batch for a named Mission 1 baseline."""

    agent_name: str
    seeds: tuple[int, ...]
    episode_results: tuple[EpisodeResult, ...]
    metrics: EpisodeMetrics


@dataclass(frozen=True, slots=True)
class Phase6Comparison:
    """Comparison surface for the stronger baseline against preserved anchors."""

    seeds: tuple[int, ...]
    random_run: Phase6BaselineRun
    heuristic_run: Phase6BaselineRun
    rollout_run: Phase6BaselineRun
    anchors: Phase6AnchorReference
    rollout_vs_random: EpisodeMetricsDelta
    rollout_vs_heuristic: EpisodeMetricsDelta
    report_table: str


def run_phase6_baseline(
    mission: Mission,
    *,
    agent_name: str,
    seeds: tuple[int, ...],
) -> Phase6BaselineRun:
    """Run one fixed-seed batch for a supported Phase 6 baseline."""

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
    elif agent_name == RolloutSearchAgent.name:
        episode_runs = run_episodes(
            mission,
            agent_factory=lambda seed: RolloutSearchAgent(),
            seeds=seeds,
        )
    else:
        raise ValueError(f"Unsupported Phase 6 baseline agent: {agent_name!r}")

    episode_results = tuple(run.result for run in episode_runs)
    return Phase6BaselineRun(
        agent_name=agent_name,
        seeds=seeds,
        episode_results=episode_results,
        metrics=aggregate_episode_results(episode_results),
    )


def run_phase6_comparison(
    mission: Mission,
    *,
    seeds: tuple[int, ...] = PHASE3_BENCHMARK_SEEDS,
    anchors: Phase6AnchorReference = Phase6AnchorReference(),
) -> Phase6Comparison:
    """Run the stronger baseline against the preserved random and heuristic runs."""

    random_run = run_phase6_baseline(
        mission,
        agent_name=RandomAgent.name,
        seeds=seeds,
    )
    heuristic_run = run_phase6_baseline(
        mission,
        agent_name=HeuristicAgent.name,
        seeds=seeds,
    )
    rollout_run = run_phase6_baseline(
        mission,
        agent_name=RolloutSearchAgent.name,
        seeds=seeds,
    )

    return Phase6Comparison(
        seeds=seeds,
        random_run=random_run,
        heuristic_run=heuristic_run,
        rollout_run=rollout_run,
        anchors=anchors,
        rollout_vs_random=diff_episode_metrics(random_run.metrics, rollout_run.metrics),
        rollout_vs_heuristic=diff_episode_metrics(
            heuristic_run.metrics,
            rollout_run.metrics,
        ),
        report_table=format_metrics_table(
            (random_run.metrics, heuristic_run.metrics, rollout_run.metrics),
        ),
    )


def run_phase6_smoke_comparison(mission: Mission) -> Phase6Comparison:
    """Run the preserved 16-seed smoke comparison with the stronger baseline."""

    return run_phase6_comparison(
        mission,
        seeds=PHASE3_SMOKE_SEEDS,
    )


__all__ = [
    "PHASE6_HEURISTIC_ANCHOR_WINS",
    "PHASE6_LEARNED_BEST_WINS",
    "PHASE6_LEARNED_MEDIAN_WINS",
    "PHASE6_RANDOM_ANCHOR_WINS",
    "Phase6AnchorReference",
    "Phase6BaselineRun",
    "Phase6Comparison",
    "run_phase6_baseline",
    "run_phase6_comparison",
    "run_phase6_smoke_comparison",
]

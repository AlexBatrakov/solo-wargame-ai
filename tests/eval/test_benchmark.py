from __future__ import annotations

from pathlib import Path

from solo_wargame_ai.domain.state import TerminalOutcome
from solo_wargame_ai.eval.benchmark import (
    PHASE3_BENCHMARK_SEEDS,
    run_random_vs_heuristic_comparison,
    run_smoke_comparison,
)
from solo_wargame_ai.eval.episode_runner import PHASE3_SMOKE_SEEDS, EpisodeResult
from solo_wargame_ai.eval.metrics import aggregate_episode_results, diff_episode_metrics
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[2]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def test_benchmark_seed_surface_tracks_the_fixed_200_seed_range() -> None:
    assert PHASE3_BENCHMARK_SEEDS == tuple(range(200))


def test_aggregate_episode_results_reports_the_required_metrics() -> None:
    metrics = aggregate_episode_results(
        (
            EpisodeResult(
                agent_name="heuristic",
                seed=0,
                terminal_outcome=TerminalOutcome.VICTORY,
                terminal_turn=3,
                resolved_marker_count=1,
                removed_german_count=1,
                player_decision_count=7,
            ),
            EpisodeResult(
                agent_name="heuristic",
                seed=1,
                terminal_outcome=TerminalOutcome.DEFEAT,
                terminal_turn=4,
                resolved_marker_count=1,
                removed_german_count=0,
                player_decision_count=6,
            ),
        ),
    )

    assert metrics.agent_name == "heuristic"
    assert metrics.episode_count == 2
    assert metrics.victory_count == 1
    assert metrics.defeat_count == 1
    assert metrics.win_rate == 0.5
    assert metrics.defeat_rate == 0.5
    assert metrics.mean_terminal_turn == 3.5
    assert metrics.mean_resolved_marker_count == 1.0
    assert metrics.mean_removed_german_count == 0.5
    assert metrics.mean_player_decision_count == 6.5


def test_smoke_comparison_is_deterministic_on_the_fixed_16_seed_set() -> None:
    mission = load_mission(MISSION_PATH)

    first_comparison = run_smoke_comparison(mission)
    second_comparison = run_smoke_comparison(mission)

    assert first_comparison.seeds == PHASE3_SMOKE_SEEDS
    assert first_comparison.random_run.seeds == PHASE3_SMOKE_SEEDS
    assert first_comparison.heuristic_run.seeds == PHASE3_SMOKE_SEEDS
    assert (
        first_comparison.random_run.episode_results
        == second_comparison.random_run.episode_results
    )
    assert (
        first_comparison.heuristic_run.episode_results
        == second_comparison.heuristic_run.episode_results
    )
    assert first_comparison.metric_deltas == second_comparison.metric_deltas
    assert first_comparison.report_table == second_comparison.report_table


def test_full_comparison_surface_uses_identical_seed_sets_for_both_agents() -> None:
    mission = load_mission(MISSION_PATH)

    comparison = run_random_vs_heuristic_comparison(
        mission,
        seeds=PHASE3_SMOKE_SEEDS,
    )

    assert comparison.random_run.seeds == comparison.heuristic_run.seeds
    assert comparison.random_run.metrics.episode_count == len(PHASE3_SMOKE_SEEDS)
    assert comparison.heuristic_run.metrics.episode_count == len(PHASE3_SMOKE_SEEDS)
    assert comparison.metric_deltas.win_rate_delta > 0.0


def test_diff_episode_metrics_returns_signed_candidate_minus_baseline_deltas() -> None:
    baseline = aggregate_episode_results(
        (
            EpisodeResult(
                agent_name="random",
                seed=0,
                terminal_outcome=TerminalOutcome.DEFEAT,
                terminal_turn=4,
                resolved_marker_count=1,
                removed_german_count=0,
                player_decision_count=12,
            ),
        ),
    )
    candidate = aggregate_episode_results(
        (
            EpisodeResult(
                agent_name="heuristic",
                seed=0,
                terminal_outcome=TerminalOutcome.VICTORY,
                terminal_turn=3,
                resolved_marker_count=1,
                removed_german_count=1,
                player_decision_count=8,
            ),
        ),
    )

    deltas = diff_episode_metrics(baseline, candidate)

    assert deltas.episode_count_delta == 0
    assert deltas.victory_count_delta == 1
    assert deltas.defeat_count_delta == -1
    assert deltas.win_rate_delta == 1.0
    assert deltas.defeat_rate_delta == -1.0
    assert deltas.mean_terminal_turn_delta == -1.0
    assert deltas.mean_resolved_marker_count_delta == 0.0
    assert deltas.mean_removed_german_count_delta == 1.0
    assert deltas.mean_player_decision_count_delta == -4.0

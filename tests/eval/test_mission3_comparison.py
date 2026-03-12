from __future__ import annotations

from pathlib import Path

from solo_wargame_ai.eval.mission3_comparison import (
    MISSION3_BENCHMARK_SEEDS,
    MISSION3_SMOKE_SEEDS,
    run_mission3_comparison,
    run_mission3_random_floor_comparison,
    run_mission3_search_strengthening_comparison,
    run_mission3_smoke_comparison,
    run_mission3_strengthened_search_comparison,
)
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[2]
    / "configs"
    / "missions"
    / "mission_03_secure_the_building.toml"
)


def test_mission3_seed_aliases_track_the_fixed_local_ranges() -> None:
    assert MISSION3_SMOKE_SEEDS == tuple(range(16))
    assert MISSION3_BENCHMARK_SEEDS == tuple(range(200))


def test_mission3_smoke_random_floor_is_deterministic() -> None:
    mission = load_mission(MISSION_PATH)

    first_comparison = run_mission3_smoke_comparison(mission)
    second_comparison = run_mission3_smoke_comparison(mission)

    assert first_comparison.seeds == MISSION3_SMOKE_SEEDS
    assert tuple(run.agent_name for run in first_comparison.baseline_runs) == (
        "random",
        "heuristic",
        "rollout-search",
    )
    for first_run, second_run in zip(
        first_comparison.baseline_runs,
        second_comparison.baseline_runs,
        strict=True,
    ):
        assert first_run.seeds == MISSION3_SMOKE_SEEDS
        assert first_run.episode_results == second_run.episode_results
    assert first_comparison.report_table == second_comparison.report_table
    assert first_comparison.search_budget == second_comparison.search_budget


def test_mission3_benchmark_random_floor_uses_the_local_200_seed_alias() -> None:
    mission = load_mission(MISSION_PATH)

    comparison = run_mission3_random_floor_comparison(
        mission,
        seeds=MISSION3_BENCHMARK_SEEDS,
    )

    assert comparison.seeds == MISSION3_BENCHMARK_SEEDS
    assert len(comparison.baseline_runs) == 1
    assert comparison.baseline_runs[0].metrics.episode_count == 200
    assert comparison.baseline_runs[0].seeds == MISSION3_BENCHMARK_SEEDS


def test_mission3_full_comparison_reports_search_budget_policy() -> None:
    mission = load_mission(MISSION_PATH)

    comparison = run_mission3_comparison(
        mission,
        seeds=MISSION3_SMOKE_SEEDS,
    )

    assert tuple(run.agent_name for run in comparison.baseline_runs) == (
        "random",
        "heuristic",
        "rollout-search",
    )
    assert comparison.search_budget is not None
    assert comparison.search_budget.rollouts_per_action == 1
    assert comparison.search_budget.rollout_policy_depth == 0
    assert comparison.search_budget.rollout_depth_limit == 16


def test_mission3_strengthened_search_surface_is_deterministic() -> None:
    mission = load_mission(MISSION_PATH)

    first_comparison = run_mission3_strengthened_search_comparison(
        mission,
        seeds=MISSION3_SMOKE_SEEDS,
    )
    second_comparison = run_mission3_strengthened_search_comparison(
        mission,
        seeds=MISSION3_SMOKE_SEEDS,
    )

    assert first_comparison.seeds == MISSION3_SMOKE_SEEDS
    assert tuple(run.agent_name for run in first_comparison.baseline_runs) == (
        "rollout-search-strengthened",
    )
    assert first_comparison.baseline_runs[0].episode_results == (
        second_comparison.baseline_runs[0].episode_results
    )
    assert first_comparison.search_budget == second_comparison.search_budget
    assert first_comparison.search_budget is not None
    assert first_comparison.search_budget.rollout_policy_depth == 2
    assert first_comparison.search_budget.rollout_depth_limit == 24


def test_mission3_packet_comparison_preserves_historical_and_strengthened_surfaces() -> None:
    mission = load_mission(MISSION_PATH)

    comparison = run_mission3_search_strengthening_comparison(
        mission,
        seeds=MISSION3_SMOKE_SEEDS,
    )

    assert comparison.seeds == MISSION3_SMOKE_SEEDS
    assert tuple(
        run.agent_name for run in comparison.historical_comparison.baseline_runs
    ) == ("random", "heuristic", "rollout-search")
    assert tuple(
        run.agent_name for run in comparison.strengthened_comparison.baseline_runs
    ) == ("rollout-search-strengthened",)
    assert comparison.historical_comparison.search_budget is not None
    assert comparison.strengthened_comparison.search_budget is not None
    assert comparison.historical_comparison.search_budget.rollout_policy_depth == 0
    assert comparison.strengthened_comparison.search_budget.rollout_policy_depth == 2

    historical_rollout_wins = comparison.historical_comparison.baseline_runs[2].metrics
    strengthened_wins = comparison.strengthened_comparison.baseline_runs[0].metrics
    assert (
        comparison.strengthened_vs_historical_rollout_search.victory_count_delta
        == strengthened_wins.victory_count - historical_rollout_wins.victory_count
    )

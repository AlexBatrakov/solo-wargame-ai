from __future__ import annotations

from pathlib import Path

from solo_wargame_ai.eval.benchmark import PHASE3_BENCHMARK_SEEDS
from solo_wargame_ai.eval.episode_runner import PHASE3_SMOKE_SEEDS
from solo_wargame_ai.eval.rollout_baseline import (
    PHASE6_HEURISTIC_ANCHOR_WINS,
    PHASE6_LEARNED_BEST_WINS,
    PHASE6_LEARNED_MEDIAN_WINS,
    PHASE6_RANDOM_ANCHOR_WINS,
    run_phase6_comparison,
    run_phase6_smoke_comparison,
)
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[2]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def test_phase6_anchor_constants_preserve_the_accepted_comparison_references() -> None:
    assert PHASE6_RANDOM_ANCHOR_WINS == 11
    assert PHASE6_HEURISTIC_ANCHOR_WINS == 157
    assert PHASE6_LEARNED_BEST_WINS == 144
    assert PHASE6_LEARNED_MEDIAN_WINS == 133


def test_phase6_smoke_comparison_is_deterministic_on_the_fixed_16_seed_set() -> None:
    mission = load_mission(MISSION_PATH)

    first_comparison = run_phase6_smoke_comparison(mission)
    second_comparison = run_phase6_smoke_comparison(mission)

    assert first_comparison.seeds == PHASE3_SMOKE_SEEDS
    assert first_comparison.rollout_run.seeds == PHASE3_SMOKE_SEEDS
    assert (
        first_comparison.rollout_run.episode_results
        == second_comparison.rollout_run.episode_results
    )
    assert first_comparison.report_table == second_comparison.report_table


def test_phase6_smoke_comparison_reports_the_expected_rollout_headroom() -> None:
    mission = load_mission(MISSION_PATH)

    comparison = run_phase6_comparison(
        mission,
        seeds=PHASE3_SMOKE_SEEDS,
    )

    assert comparison.random_run.seeds == PHASE3_SMOKE_SEEDS
    assert comparison.heuristic_run.seeds == PHASE3_SMOKE_SEEDS
    assert comparison.rollout_run.seeds == PHASE3_SMOKE_SEEDS
    assert comparison.random_run.metrics.victory_count == 2
    assert comparison.heuristic_run.metrics.victory_count == 11
    assert comparison.rollout_run.metrics.victory_count == 16
    assert comparison.rollout_vs_heuristic.victory_count_delta == 5


def test_phase6_benchmark_surface_uses_the_preserved_200_seed_range() -> None:
    assert PHASE3_BENCHMARK_SEEDS == tuple(range(200))

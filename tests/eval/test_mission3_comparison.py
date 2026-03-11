from __future__ import annotations

from pathlib import Path

from solo_wargame_ai.eval.mission3_comparison import (
    MISSION3_BENCHMARK_SEEDS,
    MISSION3_SMOKE_SEEDS,
    run_mission3_random_floor_comparison,
    run_mission3_smoke_comparison,
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
    assert len(first_comparison.baseline_runs) == 1
    assert first_comparison.baseline_runs[0].agent_name == "random"
    assert first_comparison.baseline_runs[0].seeds == MISSION3_SMOKE_SEEDS
    assert (
        first_comparison.baseline_runs[0].episode_results
        == second_comparison.baseline_runs[0].episode_results
    )
    assert first_comparison.report_table == second_comparison.report_table


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

from __future__ import annotations

from pathlib import Path

from solo_wargame_ai.agents.mission3_rollout_search_agent import Mission3SearchBudget
from solo_wargame_ai.cli import mission3_comparison
from solo_wargame_ai.eval.metrics import EpisodeMetrics, format_metrics_table
from solo_wargame_ai.eval.mission3_comparison import (
    Mission3BaselineRun,
    Mission3Comparison,
)


def _comparison(seeds: tuple[int, ...]) -> Mission3Comparison:
    random_metrics = EpisodeMetrics(
        agent_name="random",
        episode_count=len(seeds),
        victory_count=2,
        defeat_count=len(seeds) - 2,
        win_rate=2 / len(seeds),
        defeat_rate=(len(seeds) - 2) / len(seeds),
        mean_terminal_turn=4.0,
        mean_resolved_marker_count=1.25,
        mean_removed_german_count=0.5,
        mean_player_decision_count=24.0,
    )
    heuristic_metrics = EpisodeMetrics(
        agent_name="heuristic",
        episode_count=len(seeds),
        victory_count=6,
        defeat_count=len(seeds) - 6,
        win_rate=6 / len(seeds),
        defeat_rate=(len(seeds) - 6) / len(seeds),
        mean_terminal_turn=5.0,
        mean_resolved_marker_count=2.0,
        mean_removed_german_count=1.25,
        mean_player_decision_count=52.0,
    )
    rollout_metrics = EpisodeMetrics(
        agent_name="rollout-search",
        episode_count=len(seeds),
        victory_count=8,
        defeat_count=len(seeds) - 8,
        win_rate=8 / len(seeds),
        defeat_rate=(len(seeds) - 8) / len(seeds),
        mean_terminal_turn=4.5,
        mean_resolved_marker_count=2.4,
        mean_removed_german_count=1.5,
        mean_player_decision_count=48.0,
    )
    return Mission3Comparison(
        seeds=seeds,
        baseline_runs=(
            Mission3BaselineRun(
                agent_name="random",
                seeds=seeds,
                episode_results=(),
                metrics=random_metrics,
            ),
            Mission3BaselineRun(
                agent_name="heuristic",
                seeds=seeds,
                episode_results=(),
                metrics=heuristic_metrics,
            ),
            Mission3BaselineRun(
                agent_name="rollout-search",
                seeds=seeds,
                episode_results=(),
                metrics=rollout_metrics,
            ),
        ),
        report_table=format_metrics_table(
            (random_metrics, heuristic_metrics, rollout_metrics),
        ),
        search_budget=Mission3SearchBudget(),
    )


def test_smoke_mode_prints_the_required_mission3_report_fields(
    monkeypatch,
    capsys,
) -> None:
    mission = object()
    comparison = _comparison(tuple(range(16)))

    def fake_load_mission(path: Path) -> object:
        assert path == mission3_comparison.MISSION_PATH
        return mission

    def fake_run_smoke_comparison(received_mission: object) -> Mission3Comparison:
        assert received_mission is mission
        return comparison

    monkeypatch.setattr(mission3_comparison, "load_mission", fake_load_mission)
    monkeypatch.setattr(
        mission3_comparison,
        "run_mission3_smoke_comparison",
        fake_run_smoke_comparison,
    )

    exit_code = mission3_comparison.main(["--mode", "smoke"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "mode: smoke" in output
    assert "comparison_scope: mission3_only" in output
    assert "seed_alias: mission3_smoke" in output
    assert "seed_set: 0..15 (16 seeds)" in output
    assert "Search budget policy:" in output
    assert "rollout_policy        mission3_heuristic(depth=0)" in output
    assert "Signed metric deltas (heuristic - random):" in output
    assert "Signed metric deltas (rollout-search - heuristic):" in output
    assert "mission3_agents_ready: random, heuristic, rollout-search" in output
    assert "mission1_anchor_surface: preserved separately" in output


def test_benchmark_mode_writes_the_same_plain_text_report(
    monkeypatch,
    tmp_path,
    capsys,
) -> None:
    mission = object()
    comparison = _comparison(tuple(range(200)))

    def fake_load_mission(path: Path) -> object:
        assert path == mission3_comparison.MISSION_PATH
        return mission

    def fake_run_benchmark(
        received_mission: object,
        *,
        seeds: tuple[int, ...],
    ) -> Mission3Comparison:
        assert received_mission is mission
        assert seeds == mission3_comparison.MISSION3_BENCHMARK_SEEDS
        return comparison

    monkeypatch.setattr(mission3_comparison, "load_mission", fake_load_mission)
    monkeypatch.setattr(
        mission3_comparison,
        "run_mission3_comparison",
        fake_run_benchmark,
    )

    output_path = tmp_path / "reports" / "mission3-benchmark.txt"

    exit_code = mission3_comparison.main(
        ["--mode", "benchmark", "--output", str(output_path)],
    )

    assert exit_code == 0
    stdout = capsys.readouterr().out
    assert "mode: benchmark" in stdout
    assert "seed_alias: mission3_benchmark" in stdout
    assert "seed_set: 0..199 (200 seeds)" in stdout
    assert output_path.read_text(encoding="utf-8") == stdout

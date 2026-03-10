from __future__ import annotations

from pathlib import Path

from solo_wargame_ai.cli import phase3_baselines
from solo_wargame_ai.eval.benchmark import BenchmarkComparison, BenchmarkRun
from solo_wargame_ai.eval.metrics import (
    EpisodeMetrics,
    diff_episode_metrics,
    format_metrics_table,
)


def _comparison(seeds: tuple[int, ...]) -> BenchmarkComparison:
    random_metrics = EpisodeMetrics(
        agent_name="random",
        episode_count=len(seeds),
        victory_count=1,
        defeat_count=3,
        win_rate=0.25,
        defeat_rate=0.75,
        mean_terminal_turn=4.5,
        mean_resolved_marker_count=1.0,
        mean_removed_german_count=0.25,
        mean_player_decision_count=11.0,
    )
    heuristic_metrics = EpisodeMetrics(
        agent_name="heuristic",
        episode_count=len(seeds),
        victory_count=3,
        defeat_count=1,
        win_rate=0.75,
        defeat_rate=0.25,
        mean_terminal_turn=3.5,
        mean_resolved_marker_count=1.5,
        mean_removed_german_count=0.75,
        mean_player_decision_count=8.0,
    )
    return BenchmarkComparison(
        seeds=seeds,
        random_run=BenchmarkRun(
            agent_name="random",
            seeds=seeds,
            episode_results=(),
            metrics=random_metrics,
        ),
        heuristic_run=BenchmarkRun(
            agent_name="heuristic",
            seeds=seeds,
            episode_results=(),
            metrics=heuristic_metrics,
        ),
        metric_deltas=diff_episode_metrics(random_metrics, heuristic_metrics),
        report_table=format_metrics_table((random_metrics, heuristic_metrics)),
    )


def test_smoke_mode_prints_the_required_report_fields(
    monkeypatch,
    capsys,
) -> None:
    mission = object()
    comparison = _comparison(tuple(range(16)))

    def fake_load_mission(path: Path) -> object:
        assert path == phase3_baselines.MISSION_PATH
        return mission

    def fake_run_smoke_comparison(received_mission: object) -> BenchmarkComparison:
        assert received_mission is mission
        return comparison

    monkeypatch.setattr(phase3_baselines, "load_mission", fake_load_mission)
    monkeypatch.setattr(
        phase3_baselines,
        "run_smoke_comparison",
        fake_run_smoke_comparison,
    )

    exit_code = phase3_baselines.main(["--mode", "smoke"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "mode: smoke" in output
    assert "seed_set: 0..15 (16 seeds)" in output
    assert "Metrics table:" in output
    assert "Signed metric deltas (heuristic - random):" in output
    assert "win_rate               +0.500" in output


def test_benchmark_mode_writes_the_same_plain_text_report(
    monkeypatch,
    tmp_path,
    capsys,
) -> None:
    mission = object()
    comparison = _comparison(tuple(range(200)))

    def fake_load_mission(path: Path) -> object:
        assert path == phase3_baselines.MISSION_PATH
        return mission

    def fake_run_benchmark(
        received_mission: object,
        *,
        seeds: tuple[int, ...],
    ) -> BenchmarkComparison:
        assert received_mission is mission
        assert seeds == phase3_baselines.PHASE3_BENCHMARK_SEEDS
        return comparison

    monkeypatch.setattr(phase3_baselines, "load_mission", fake_load_mission)
    monkeypatch.setattr(
        phase3_baselines,
        "run_random_vs_heuristic_comparison",
        fake_run_benchmark,
    )

    output_path = tmp_path / "reports" / "phase3-benchmark.txt"

    exit_code = phase3_baselines.main(
        ["--mode", "benchmark", "--output", str(output_path)],
    )

    assert exit_code == 0
    stdout = capsys.readouterr().out
    assert "mode: benchmark" in stdout
    assert "seed_set: 0..199 (200 seeds)" in stdout
    assert output_path.read_text(encoding="utf-8") == f"{stdout}"

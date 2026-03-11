from __future__ import annotations

from pathlib import Path

from solo_wargame_ai.cli import phase6_stronger_baseline
from solo_wargame_ai.eval.metrics import EpisodeMetrics, diff_episode_metrics, format_metrics_table
from solo_wargame_ai.eval.rollout_baseline import (
    Phase6AnchorReference,
    Phase6BaselineRun,
    Phase6Comparison,
)


def _comparison(seeds: tuple[int, ...]) -> Phase6Comparison:
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
    rollout_metrics = EpisodeMetrics(
        agent_name="rollout",
        episode_count=len(seeds),
        victory_count=4,
        defeat_count=0,
        win_rate=1.0,
        defeat_rate=0.0,
        mean_terminal_turn=3.0,
        mean_resolved_marker_count=1.5,
        mean_removed_german_count=1.0,
        mean_player_decision_count=7.0,
    )
    return Phase6Comparison(
        seeds=seeds,
        random_run=Phase6BaselineRun(
            agent_name="random",
            seeds=seeds,
            episode_results=(),
            metrics=random_metrics,
        ),
        heuristic_run=Phase6BaselineRun(
            agent_name="heuristic",
            seeds=seeds,
            episode_results=(),
            metrics=heuristic_metrics,
        ),
        rollout_run=Phase6BaselineRun(
            agent_name="rollout",
            seeds=seeds,
            episode_results=(),
            metrics=rollout_metrics,
        ),
        anchors=Phase6AnchorReference(),
        rollout_vs_random=diff_episode_metrics(random_metrics, rollout_metrics),
        rollout_vs_heuristic=diff_episode_metrics(heuristic_metrics, rollout_metrics),
        report_table=format_metrics_table(
            (random_metrics, heuristic_metrics, rollout_metrics),
        ),
    )


def test_smoke_mode_prints_the_required_phase6_report_fields(
    monkeypatch,
    capsys,
) -> None:
    mission = object()
    comparison = _comparison(tuple(range(16)))

    def fake_load_mission(path: Path) -> object:
        assert path == phase6_stronger_baseline.MISSION_PATH
        return mission

    def fake_run_smoke_comparison(received_mission: object) -> Phase6Comparison:
        assert received_mission is mission
        return comparison

    monkeypatch.setattr(phase6_stronger_baseline, "load_mission", fake_load_mission)
    monkeypatch.setattr(
        phase6_stronger_baseline,
        "run_phase6_smoke_comparison",
        fake_run_smoke_comparison,
    )

    exit_code = phase6_stronger_baseline.main(["--mode", "smoke"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "mode: smoke" in output
    assert "seed_set: 0..15 (16 seeds)" in output
    assert "budget_policy:" in output
    assert "Signed metric deltas (rollout - heuristic):" in output
    assert "Benchmark-anchor comparison is omitted in smoke mode." in output


def test_benchmark_mode_writes_the_same_plain_text_report(
    monkeypatch,
    tmp_path,
    capsys,
) -> None:
    mission = object()
    comparison = _comparison(tuple(range(200)))

    def fake_load_mission(path: Path) -> object:
        assert path == phase6_stronger_baseline.MISSION_PATH
        return mission

    def fake_run_benchmark(
        received_mission: object,
        *,
        seeds: tuple[int, ...],
    ) -> Phase6Comparison:
        assert received_mission is mission
        assert seeds == phase6_stronger_baseline.PHASE3_BENCHMARK_SEEDS
        return comparison

    monkeypatch.setattr(phase6_stronger_baseline, "load_mission", fake_load_mission)
    monkeypatch.setattr(
        phase6_stronger_baseline,
        "run_phase6_comparison",
        fake_run_benchmark,
    )

    output_path = tmp_path / "reports" / "phase6-benchmark.txt"

    exit_code = phase6_stronger_baseline.main(
        ["--mode", "benchmark", "--output", str(output_path)],
    )

    assert exit_code == 0
    stdout = capsys.readouterr().out
    assert "mode: benchmark" in stdout
    assert "seed_set: 0..199 (200 seeds)" in stdout
    assert "Comparison vs accepted anchors:" in stdout
    assert output_path.read_text(encoding="utf-8") == f"{stdout}"

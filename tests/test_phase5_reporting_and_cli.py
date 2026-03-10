from __future__ import annotations

import json
from pathlib import Path

from solo_wargame_ai.cli import phase5_learned_policy_eval, phase5_summary, phase5_train
from solo_wargame_ai.eval.metrics import EpisodeMetrics
from solo_wargame_ai.eval.phase5_reporting import (
    Phase5EvalCheckpointMetadata,
    build_phase5_anchor_comparison,
    format_phase5_eval_report,
)


def _metrics(
    *,
    wins: int,
    episodes: int,
    agent_name: str = "masked_actor_critic",
) -> EpisodeMetrics:
    return EpisodeMetrics(
        agent_name=agent_name,
        episode_count=episodes,
        victory_count=wins,
        defeat_count=episodes - wins,
        win_rate=wins / episodes,
        defeat_rate=(episodes - wins) / episodes,
        mean_terminal_turn=4.0,
        mean_resolved_marker_count=1.0,
        mean_removed_german_count=0.5,
        mean_player_decision_count=10.0,
    )


def test_phase5_eval_report_uses_preserved_phase3_anchor_wins() -> None:
    report = format_phase5_eval_report(
        mode="benchmark",
        checkpoint_path="outputs/phase5/example.pt",
        metrics=_metrics(wins=50, episodes=200),
        seeds=tuple(range(200)),
        checkpoint_metadata=Phase5EvalCheckpointMetadata(
            training_seed=101,
            checkpoint_episode=1750,
            checkpoint_step=43101,
            model_selection_seeds=tuple(range(2000, 2016)),
            checkpoint_selection_policy="best greedy masked win count",
        ),
    )

    comparison = build_phase5_anchor_comparison(
        mode="benchmark",
        metrics=_metrics(wins=50, episodes=200),
    )

    assert comparison.random_reference_wins == 11
    assert comparison.heuristic_reference_wins == 157
    assert comparison.wins_vs_random == 39
    assert comparison.wins_vs_heuristic == -107
    assert "training_seed: 101" in report
    assert "checkpoint_episode: 1750" in report
    assert "seed_set: 0..199 (200 seeds)" in report
    assert "wins_vs_random: +39" in report


def test_phase5_train_cli_prints_saved_training_summary(
    monkeypatch,
    capsys,
    tmp_path,
) -> None:
    mission = object()

    class FakeTrainingRun:
        def __init__(self) -> None:
            self.report_path = tmp_path / "report.txt"
            self.report_path.write_text("saved report\n", encoding="utf-8")

    def fake_load_mission(path: Path) -> object:
        assert path == phase5_train.MISSION_PATH
        return mission

    def fake_train_masked_actor_critic(
        received_mission,
        *,
        config,
        output_dir,
        overwrite_output_dir,
    ):
        assert received_mission is mission
        assert config.training_seed == 101
        assert config.total_episodes == 4
        assert config.checkpoint_interval == 2
        assert output_dir == tmp_path / "train"
        assert overwrite_output_dir is False
        return FakeTrainingRun()

    def fake_format_phase5_training_report(training_run) -> str:
        assert isinstance(training_run, FakeTrainingRun)
        return "Phase 5 training\nselected_checkpoint: outputs/phase5/example.pt"

    monkeypatch.setattr(phase5_train, "load_mission", fake_load_mission)
    monkeypatch.setattr(
        phase5_train,
        "train_masked_actor_critic",
        fake_train_masked_actor_critic,
    )
    monkeypatch.setattr(
        phase5_train,
        "format_phase5_training_report",
        fake_format_phase5_training_report,
    )

    exit_code = phase5_train.main(
        [
            "--training-seed",
            "101",
            "--episodes",
            "4",
            "--checkpoint-interval",
            "2",
            "--output-dir",
            str(tmp_path / "train"),
        ],
    )

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Phase 5 training" in output
    assert "selected_checkpoint:" in output


def test_phase5_train_cli_passes_explicit_overwrite_flag(
    monkeypatch,
    tmp_path,
) -> None:
    mission = object()

    class FakeTrainingRun:
        pass

    def fake_load_mission(path: Path) -> object:
        assert path == phase5_train.MISSION_PATH
        return mission

    def fake_train_masked_actor_critic(
        received_mission,
        *,
        config,
        output_dir,
        overwrite_output_dir,
    ):
        assert received_mission is mission
        assert config.training_seed == 101
        assert output_dir == tmp_path / "train"
        assert overwrite_output_dir is True
        return FakeTrainingRun()

    monkeypatch.setattr(phase5_train, "load_mission", fake_load_mission)
    monkeypatch.setattr(
        phase5_train,
        "train_masked_actor_critic",
        fake_train_masked_actor_critic,
    )
    monkeypatch.setattr(
        phase5_train,
        "format_phase5_training_report",
        lambda training_run: "ok",
    )

    assert (
        phase5_train.main(
            [
                "--training-seed",
                "101",
                "--episodes",
                "4",
                "--checkpoint-interval",
                "2",
                "--output-dir",
                str(tmp_path / "train"),
                "--overwrite-output-dir",
            ],
        )
        == 0
    )


def test_phase5_learned_eval_cli_prints_and_writes_plain_text_report(
    monkeypatch,
    capsys,
    tmp_path,
) -> None:
    mission = object()
    evaluation = type(
        "Evaluation",
        (),
        {
            "metrics": _metrics(wins=7, episodes=16),
            "seeds": tuple(range(16)),
        },
    )()
    loaded_checkpoint = type(
        "LoadedCheckpoint",
        (),
        {
            "adapter": object(),
            "model": object(),
            "training_seed": 101,
            "checkpoint_episode": 1750,
            "checkpoint_step": 43101,
            "model_selection_seeds": tuple(range(2000, 2016)),
            "checkpoint_selection_policy": "best greedy masked win count",
        },
    )()

    def fake_load_mission(path: Path) -> object:
        assert path == phase5_learned_policy_eval.MISSION_PATH
        return mission

    def fake_load_phase5_checkpoint(received_mission: object, checkpoint_path: Path):
        assert received_mission is mission
        assert checkpoint_path == tmp_path / "selected.pt"
        return loaded_checkpoint

    monkeypatch.setattr(phase5_learned_policy_eval, "load_mission", fake_load_mission)
    monkeypatch.setattr(
        phase5_learned_policy_eval,
        "load_phase5_checkpoint",
        fake_load_phase5_checkpoint,
    )
    monkeypatch.setattr(
        phase5_learned_policy_eval,
        "evaluate_phase5_smoke_policy",
        lambda received_mission, *, policy_factory, evaluation: evaluation_object,
    )
    evaluation_object = evaluation

    output_path = tmp_path / "reports" / "smoke.txt"
    json_output_path = tmp_path / "reports" / "smoke.json"
    exit_code = phase5_learned_policy_eval.main(
        [
            "--checkpoint",
            str(tmp_path / "selected.pt"),
            "--mode",
            "smoke",
            "--output",
            str(output_path),
            "--json-output",
            str(json_output_path),
        ],
    )

    assert exit_code == 0
    stdout = capsys.readouterr().out
    assert "Phase 5 learned-policy evaluation" in stdout
    assert "training_seed: 101" in stdout
    assert "seed_set: 0..15 (16 seeds)" in stdout
    assert output_path.read_text(encoding="utf-8") == stdout
    json_payload = json.loads(json_output_path.read_text(encoding="utf-8"))
    assert json_payload["checkpoint_metadata"]["training_seed"] == 101
    assert json_payload["metrics"]["victory_count"] == 7


def test_phase5_summary_cli_aggregates_existing_artifact_outputs(
    tmp_path,
    capsys,
) -> None:
    for training_seed, wins in ((101, 144), (202, 133), (303, 121)):
        artifact_dir = tmp_path / f"train_seed_{training_seed}"
        artifact_dir.mkdir()
        (artifact_dir / "training_summary.json").write_text(
            json.dumps(
                {
                    "training_seed": training_seed,
                    "selected_checkpoint_path": (
                        f"outputs/phase5/train_seed_{training_seed}_ep_2000/"
                        "checkpoints/selected_checkpoint.pt"
                    ),
                },
            )
            + "\n",
            encoding="utf-8",
        )
        (artifact_dir / "benchmark_eval_report.txt").write_text(
            "\n".join(
                (
                    "Phase 5 learned-policy evaluation",
                    "mode: benchmark",
                    "checkpoint: outputs/phase5/example.pt",
                    "seed_set: 0..199 (200 seeds)",
                    "",
                    "Metrics table:",
                    (
                        "agent       episodes wins defeats win_rate defeat_rate "
                        "mean_turn mean_markers mean_removed mean_decisions"
                    ),
                    (
                        f"masked_actor_critic     200  {wins}      {200 - wins}    "
                        f"{wins / 200:.3f}       {(200 - wins) / 200:.3f}     "
                        "2.665        1.000        0.720         22.555"
                    ),
                ),
            )
            + "\n",
            encoding="utf-8",
        )

    json_output_path = tmp_path / "reports" / "phase5-summary.json"
    exit_code = phase5_summary.main(
        [
            "--artifact-dir",
            str(tmp_path / "train_seed_101"),
            "--artifact-dir",
            str(tmp_path / "train_seed_202"),
            "--artifact-dir",
            str(tmp_path / "train_seed_303"),
            "--json-output",
            str(json_output_path),
        ],
    )

    assert exit_code == 0
    stdout = capsys.readouterr().out
    assert "best_benchmark_wins: 144" in stdout
    assert "median_benchmark_wins: 133" in stdout
    assert "package_c_recommendation: Package C not recommended" in stdout
    json_payload = json.loads(json_output_path.read_text(encoding="utf-8"))
    assert json_payload["best_benchmark_wins"] == 144
    assert json_payload["median_benchmark_wins"] == 133
    assert json_payload["minimum_success_verdict"] == "met"

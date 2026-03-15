from __future__ import annotations

import json
from pathlib import Path

from solo_wargame_ai.cli import (
    mission3_learned_policy_eval,
    mission3_summary,
    mission3_train,
)
from solo_wargame_ai.eval.metrics import EpisodeMetrics
from solo_wargame_ai.eval.mission3_learned_policy_seeds import (
    MISSION3_LEARNING_BENCHMARK_EVAL_SEEDS,
    MISSION3_LEARNING_FEATURE_ADAPTER_SEED,
    MISSION3_LEARNING_MODEL_SELECTION_SEEDS,
    MISSION3_LEARNING_SMOKE_EVAL_SEEDS,
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


def test_mission3_train_cli_uses_local_seed_policy_and_artifact_root(
    monkeypatch,
    capsys,
    tmp_path,
) -> None:
    mission = object()

    class FakeTrainingRun:
        def __init__(self) -> None:
            self.report_path = tmp_path / "train" / "training_report.txt"
            self.report_path.parent.mkdir(parents=True, exist_ok=True)

    def fake_load_mission(path: Path) -> object:
        assert path == mission3_train.MISSION_PATH
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
        assert config.feature_adapter_seed == MISSION3_LEARNING_FEATURE_ADAPTER_SEED
        assert config.model_selection_seeds == MISSION3_LEARNING_MODEL_SELECTION_SEEDS
        assert output_dir == (
            Path("outputs") / "mission3_learning" / "train_seed_101_ep_4"
        )
        assert overwrite_output_dir is False
        return FakeTrainingRun()

    monkeypatch.setattr(mission3_train, "load_mission", fake_load_mission)
    monkeypatch.setattr(
        mission3_train,
        "train_masked_actor_critic",
        fake_train_masked_actor_critic,
    )
    monkeypatch.setattr(
        mission3_train,
        "format_mission3_training_report",
        lambda training_run, *, artifact_root: (
            "Mission 3 learned-policy training\n"
            f"artifact_root_policy: {artifact_root}"
        ),
    )

    exit_code = mission3_train.main(
        [
            "--training-seed",
            "101",
            "--episodes",
            "4",
            "--checkpoint-interval",
            "2",
        ],
    )

    assert exit_code == 0
    stdout = capsys.readouterr().out
    assert "Mission 3 learned-policy training" in stdout
    assert "artifact_root_policy: outputs/mission3_learning" in stdout
    assert (
        tmp_path / "train" / "training_report.txt"
    ).read_text(encoding="utf-8") == stdout


def test_mission3_eval_cli_prints_and_writes_report_and_json(
    monkeypatch,
    capsys,
    tmp_path,
) -> None:
    mission = object()
    evaluation = type(
        "Evaluation",
        (),
        {
            "metrics": _metrics(wins=9, episodes=16),
            "seeds": MISSION3_LEARNING_SMOKE_EVAL_SEEDS,
        },
    )()
    loaded_checkpoint = type(
        "LoadedCheckpoint",
        (),
        {
            "adapter": object(),
            "model": object(),
            "training_seed": 101,
            "checkpoint_episode": 250,
            "checkpoint_step": 6123,
            "model_selection_seeds": MISSION3_LEARNING_MODEL_SELECTION_SEEDS,
            "checkpoint_selection_policy": "best greedy masked win count",
        },
    )()

    def fake_load_mission(path: Path) -> object:
        assert path == mission3_learned_policy_eval.MISSION_PATH
        return mission

    def fake_load_phase5_checkpoint(received_mission: object, checkpoint_path: Path):
        assert received_mission is mission
        assert checkpoint_path == tmp_path / "selected.pt"
        return loaded_checkpoint

    def fake_evaluate_learned_policy(
        received_mission,
        *,
        policy_factory,
        seeds,
        evaluation,
    ):
        assert received_mission is mission
        assert seeds == MISSION3_LEARNING_SMOKE_EVAL_SEEDS
        assert evaluation is True
        assert policy_factory() is not None
        return evaluation_object

    evaluation_object = evaluation
    monkeypatch.setattr(
        mission3_learned_policy_eval,
        "load_mission",
        fake_load_mission,
    )
    monkeypatch.setattr(
        mission3_learned_policy_eval,
        "load_phase5_checkpoint",
        fake_load_phase5_checkpoint,
    )
    monkeypatch.setattr(
        mission3_learned_policy_eval,
        "evaluate_learned_policy",
        fake_evaluate_learned_policy,
    )

    output_path = tmp_path / "reports" / "smoke_eval_report.txt"
    json_output_path = tmp_path / "reports" / "smoke_eval.json"
    exit_code = mission3_learned_policy_eval.main(
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
    assert "Mission 3 learned-policy evaluation" in stdout
    assert "historical_reference_qualification:" in stdout
    assert "oracle-style or branch-clairvoyant" in stdout
    assert "wins_vs_rollout_search_reference: +1" in stdout
    assert output_path.read_text(encoding="utf-8") == stdout
    json_payload = json.loads(json_output_path.read_text(encoding="utf-8"))
    assert json_payload["checkpoint_metadata"]["training_seed"] == 101
    assert json_payload["metrics"]["victory_count"] == 9
    assert json_payload["preserved_historical_references"]["heuristic_wins"] == 7


def test_mission3_summary_cli_aggregates_artifact_dirs(
    tmp_path,
    capsys,
) -> None:
    for training_seed, wins in ((101, 60), (202, 55), (303, 40)):
        artifact_dir = tmp_path / f"train_seed_{training_seed}"
        artifact_dir.mkdir()
        (artifact_dir / "training_summary.json").write_text(
            json.dumps(
                {
                    "training_seed": training_seed,
                    "selected_checkpoint_path": (
                        "outputs/mission3_learning/"
                        f"train_seed_{training_seed}_ep_2000/"
                        "checkpoints/selected_checkpoint.pt"
                    ),
                },
            )
            + "\n",
            encoding="utf-8",
        )
        (artifact_dir / "benchmark_eval.json").write_text(
            json.dumps(
                {
                    "mode": "benchmark",
                    "metrics": {
                        "agent_name": "masked_actor_critic",
                        "episode_count": len(MISSION3_LEARNING_BENCHMARK_EVAL_SEEDS),
                        "victory_count": wins,
                        "defeat_count": 200 - wins,
                        "win_rate": wins / 200,
                        "defeat_rate": (200 - wins) / 200,
                        "mean_terminal_turn": 4.0,
                        "mean_resolved_marker_count": 1.0,
                        "mean_removed_german_count": 0.5,
                        "mean_player_decision_count": 10.0,
                    },
                },
            )
            + "\n",
            encoding="utf-8",
        )

    json_output_path = tmp_path / "reports" / "mission3-summary.json"
    exit_code = mission3_summary.main(
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
    assert "Mission 3 learned-policy aggregate summary" in stdout
    assert "best_wins: 60" in stdout
    assert "median_wins: 55" in stdout
    assert "historical_reference_qualification:" in stdout
    assert "rollout_search_wins: 105" in stdout
    json_payload = json.loads(json_output_path.read_text(encoding="utf-8"))
    assert json_payload["best_wins"] == 60
    assert json_payload["median_wins"] == 55
    assert (
        json_payload["transfer_signal_vs_preserved_random_reference"]
        == "median_provided_run_above_preserved_random_reference"
    )

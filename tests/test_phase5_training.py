from __future__ import annotations

from pathlib import Path

import pytest

from solo_wargame_ai.agents.phase5_training import (
    PHASE5_CHECKPOINT_SELECTION_POLICY,
    Phase5TrainingConfig,
    build_phase5_policy_factory,
    load_phase5_checkpoint,
    train_masked_actor_critic,
)
from solo_wargame_ai.eval.phase5_seed_policy import (
    PHASE5_BENCHMARK_EVAL_SEEDS,
    PHASE5_FEATURE_ADAPTER_SEED,
    PHASE5_MODEL_SELECTION_SEEDS,
    PHASE5_SMOKE_EVAL_SEEDS,
    PHASE5_TRAINING_SEEDS,
    training_rollout_seed,
)
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def test_phase5_training_run_writes_a_selected_checkpoint_and_summary(tmp_path) -> None:
    mission = load_mission(MISSION_PATH)
    config = Phase5TrainingConfig(
        training_seed=PHASE5_TRAINING_SEEDS[0],
        total_episodes=2,
        checkpoint_interval=1,
    )

    training_run = train_masked_actor_critic(
        mission,
        config=config,
        output_dir=tmp_path / "phase5-train",
    )

    assert training_run.total_env_steps > 0
    assert training_run.invalid_action_count == 0
    assert training_run.selected_checkpoint_path.exists()
    assert training_run.summary_path.exists()
    assert training_run.report_path.exists()
    assert len(training_run.checkpoints) == 2
    assert training_run.selected_checkpoint_episode in {1, 2}
    assert training_run.selected_model_selection_metrics.episode_count == len(
        PHASE5_MODEL_SELECTION_SEEDS,
    )


def test_phase5_checkpoint_loader_and_policy_factory_reuse_saved_assets(tmp_path) -> None:
    mission = load_mission(MISSION_PATH)
    config = Phase5TrainingConfig(
        training_seed=PHASE5_TRAINING_SEEDS[0],
        total_episodes=1,
        checkpoint_interval=1,
    )
    training_run = train_masked_actor_critic(
        mission,
        config=config,
        output_dir=tmp_path / "phase5-load",
    )

    loaded_checkpoint = load_phase5_checkpoint(mission, training_run.selected_checkpoint_path)
    policy_factory = build_phase5_policy_factory(
        mission,
        training_run.selected_checkpoint_path,
    )
    policy = policy_factory()

    assert loaded_checkpoint.training_seed == PHASE5_TRAINING_SEEDS[0]
    assert loaded_checkpoint.feature_adapter_seed == PHASE5_FEATURE_ADAPTER_SEED
    assert loaded_checkpoint.checkpoint_step == training_run.selected_checkpoint_step
    assert loaded_checkpoint.model_selection_seeds == PHASE5_MODEL_SELECTION_SEEDS
    assert loaded_checkpoint.checkpoint_selection_policy == PHASE5_CHECKPOINT_SELECTION_POLICY
    assert policy.name == "masked_actor_critic"


def test_phase5_seed_roles_remain_disjoint() -> None:
    rollout_seeds = {
        training_rollout_seed(training_seed, episode_index)
        for training_seed in PHASE5_TRAINING_SEEDS
        for episode_index in range(3)
    }

    assert set(PHASE5_MODEL_SELECTION_SEEDS).isdisjoint(PHASE5_SMOKE_EVAL_SEEDS)
    assert set(PHASE5_MODEL_SELECTION_SEEDS).isdisjoint(PHASE5_BENCHMARK_EVAL_SEEDS)
    assert rollout_seeds.isdisjoint(PHASE5_MODEL_SELECTION_SEEDS)


def test_phase5_training_refuses_to_write_into_a_non_empty_artifact_dir(tmp_path) -> None:
    mission = load_mission(MISSION_PATH)
    artifact_dir = tmp_path / "phase5-nonempty"
    artifact_dir.mkdir()
    (artifact_dir / "stale.txt").write_text("stale\n", encoding="utf-8")
    config = Phase5TrainingConfig(
        training_seed=PHASE5_TRAINING_SEEDS[0],
        total_episodes=1,
        checkpoint_interval=1,
    )

    with pytest.raises(FileExistsError, match="not empty"):
        train_masked_actor_critic(
            mission,
            config=config,
            output_dir=artifact_dir,
        )


def test_phase5_training_allows_explicit_output_dir_overwrite(tmp_path) -> None:
    mission = load_mission(MISSION_PATH)
    artifact_dir = tmp_path / "phase5-overwrite"
    artifact_dir.mkdir()
    stale_path = artifact_dir / "stale.txt"
    stale_path.write_text("stale\n", encoding="utf-8")
    config = Phase5TrainingConfig(
        training_seed=PHASE5_TRAINING_SEEDS[0],
        total_episodes=1,
        checkpoint_interval=1,
    )

    training_run = train_masked_actor_critic(
        mission,
        config=config,
        output_dir=artifact_dir,
        overwrite_output_dir=True,
    )

    assert not stale_path.exists()
    assert training_run.selected_checkpoint_path.exists()


def test_phase5_training_config_rejects_duplicate_or_eval_overlapping_model_selection_seeds(
) -> None:
    with pytest.raises(ValueError, match="duplicates"):
        Phase5TrainingConfig(
            training_seed=PHASE5_TRAINING_SEEDS[0],
            total_episodes=1,
            checkpoint_interval=1,
            model_selection_seeds=(2000, 2000),
        )

    with pytest.raises(ValueError, match="smoke eval seeds"):
        Phase5TrainingConfig(
            training_seed=PHASE5_TRAINING_SEEDS[0],
            total_episodes=1,
            checkpoint_interval=1,
            model_selection_seeds=(0, 2000),
        )

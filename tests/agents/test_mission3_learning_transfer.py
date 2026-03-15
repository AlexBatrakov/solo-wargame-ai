from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from solo_wargame_ai.agents.feature_adapter import Mission3ObservationFeatureAdapter
from solo_wargame_ai.agents.masked_actor_critic_training import (
    Phase5TrainingConfig,
    build_phase5_policy_factory,
    load_phase5_checkpoint,
    train_masked_actor_critic,
)
from solo_wargame_ai.env.mission3_env import Mission3Env
from solo_wargame_ai.eval.learned_policy_eval import evaluate_learned_policy
from solo_wargame_ai.eval.learned_policy_seeds import PHASE5_TRAINING_SEEDS
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[2]
    / "configs"
    / "missions"
    / "mission_03_secure_the_building.toml"
)


def test_mission3_feature_adapter_is_deterministic_and_ignores_non_contract_noise() -> None:
    mission = load_mission(MISSION_PATH)
    env = Mission3Env(mission)
    observation, _ = env.reset(seed=0)
    adapter = Mission3ObservationFeatureAdapter.from_initial_observation(observation)

    repeated_observation, _ = env.reset(seed=0)
    noisy_observation = deepcopy(observation)
    noisy_observation["debug_rng_state"] = {"rolls": [1, 2, 3]}
    noisy_observation["decision"]["ignored_debug_field"] = "noise"

    feature_vector = adapter.encode(observation)
    repeated_vector = adapter.encode(repeated_observation)
    noisy_vector = adapter.encode(noisy_observation)

    assert feature_vector == repeated_vector == noisy_vector
    assert feature_vector.size == adapter.feature_size


def test_mission3_feature_adapter_tracks_step_observations_deterministically() -> None:
    mission = load_mission(MISSION_PATH)
    first_env = Mission3Env(mission)
    second_env = Mission3Env(mission)

    first_observation, first_info = first_env.reset(seed=0)
    second_observation, second_info = second_env.reset(seed=0)
    adapter = Mission3ObservationFeatureAdapter.from_initial_observation(first_observation)
    action_id = int(first_info["legal_action_ids"][0])

    first_step_observation, _, _, _, _ = first_env.step(action_id)
    second_step_observation, _, _, _, _ = second_env.step(action_id)

    assert first_observation == second_observation
    assert first_info["legal_action_ids"] == second_info["legal_action_ids"]
    assert adapter.encode(first_step_observation) == adapter.encode(second_step_observation)


def test_phase5_style_training_and_checkpoint_loading_support_mission3(tmp_path) -> None:
    mission = load_mission(MISSION_PATH)
    config = Phase5TrainingConfig(
        training_seed=PHASE5_TRAINING_SEEDS[0],
        total_episodes=1,
        checkpoint_interval=1,
        model_selection_seeds=(3_000,),
    )

    training_run = train_masked_actor_critic(
        mission,
        config=config,
        output_dir=tmp_path / "mission3-train",
    )
    loaded_checkpoint = load_phase5_checkpoint(mission, training_run.selected_checkpoint_path)
    policy_factory = build_phase5_policy_factory(
        mission,
        training_run.selected_checkpoint_path,
    )
    evaluation = evaluate_learned_policy(
        mission,
        policy_factory=policy_factory,
        seeds=(0,),
        evaluation=True,
    )

    assert training_run.total_env_steps > 0
    assert training_run.invalid_action_count == 0
    assert training_run.selected_checkpoint_path.exists()
    assert training_run.summary_path.exists()
    assert training_run.report_path.exists()
    assert len(training_run.checkpoints) == 1
    assert loaded_checkpoint.mission_id == mission.mission_id
    assert loaded_checkpoint.action_count == Mission3Env(mission).action_space_size == 49
    assert loaded_checkpoint.model_selection_seeds == (3_000,)
    assert loaded_checkpoint.adapter.feature_size > 0
    assert evaluation.metrics.agent_name == "masked_actor_critic"
    assert evaluation.metrics.episode_count == 1
    assert evaluation.seeds == (0,)

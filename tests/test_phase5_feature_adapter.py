from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from solo_wargame_ai.agents.feature_adapter import ObservationFeatureAdapter
from solo_wargame_ai.domain.actions import SelectBritishUnitAction
from solo_wargame_ai.env import Mission1Env
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def test_feature_adapter_is_deterministic_and_ignores_non_contract_noise() -> None:
    mission = load_mission(MISSION_PATH)
    env = Mission1Env(mission)
    observation, _ = env.reset(seed=0)
    adapter = ObservationFeatureAdapter.from_initial_observation(observation)

    repeated_observation, _ = env.reset(seed=0)
    noisy_observation = deepcopy(observation)
    noisy_observation["debug_rng_state"] = {"rolls": [1, 2, 3]}
    noisy_observation["decision"]["ignored_debug_field"] = "noise"

    feature_vector = adapter.encode(observation)
    repeated_vector = adapter.encode(repeated_observation)
    noisy_vector = adapter.encode(noisy_observation)

    assert feature_vector == repeated_vector == noisy_vector
    assert feature_vector.size == adapter.feature_size


def test_feature_adapter_tracks_step_observations_deterministically() -> None:
    mission = load_mission(MISSION_PATH)
    first_env = Mission1Env(mission)
    second_env = Mission1Env(mission)

    first_observation, _ = first_env.reset(seed=0)
    second_observation, _ = second_env.reset(seed=0)
    adapter = ObservationFeatureAdapter.from_initial_observation(first_observation)
    action_id = first_env.action_catalog.encode(
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
    )

    first_step_observation, _, _, _, _ = first_env.step(action_id)
    second_step_observation, _, _, _, _ = second_env.step(action_id)

    assert first_observation == second_observation
    assert adapter.encode(first_step_observation) == adapter.encode(second_step_observation)

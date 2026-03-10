from __future__ import annotations

from pathlib import Path

import torch

MISSION_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def test_agents_package_lazy_exports_resolve_torch_backed_classes() -> None:
    from solo_wargame_ai import agents

    assert agents.MaskedActorCriticNetwork.__name__ == "MaskedActorCriticNetwork"
    assert agents.MaskedActorCriticPolicy.__name__ == "MaskedActorCriticPolicy"
    assert "MaskedActorCriticNetwork" in dir(agents)


def test_torch_backed_actor_critic_policy_step_returns_a_legal_action_id() -> None:
    from solo_wargame_ai.agents.feature_adapter import ObservationFeatureAdapter
    from solo_wargame_ai.agents.masked_actor_critic import (
        MaskedActorCriticNetwork,
        MaskedActorCriticPolicy,
    )
    from solo_wargame_ai.env import Mission1Env
    from solo_wargame_ai.io.mission_loader import load_mission

    mission = load_mission(MISSION_PATH)
    env = Mission1Env(mission)
    observation, info = env.reset(seed=0)
    adapter = ObservationFeatureAdapter.from_initial_observation(observation)
    model = MaskedActorCriticNetwork(
        input_dim=adapter.feature_size,
        action_count=env.action_space_size,
    )
    policy = MaskedActorCriticPolicy(adapter, model, seed=7)

    record = policy.policy_step(observation, info, evaluation=True)

    assert record.action_id in info["legal_action_ids"]
    assert isinstance(record.log_prob, float)
    assert isinstance(record.entropy, float)
    assert isinstance(record.value_estimate, float)


def test_torch_network_forward_matches_the_feature_and_action_dimensions() -> None:
    from solo_wargame_ai.agents.feature_adapter import ObservationFeatureAdapter
    from solo_wargame_ai.agents.masked_actor_critic import MaskedActorCriticNetwork
    from solo_wargame_ai.env import Mission1Env
    from solo_wargame_ai.io.mission_loader import load_mission

    mission = load_mission(MISSION_PATH)
    env = Mission1Env(mission)
    observation, _ = env.reset(seed=0)
    adapter = ObservationFeatureAdapter.from_initial_observation(observation)
    model = MaskedActorCriticNetwork(
        input_dim=adapter.feature_size,
        action_count=env.action_space_size,
    )

    policy_logits, values = model.forward(adapter.encode(observation).values)

    assert isinstance(policy_logits, torch.Tensor)
    assert isinstance(values, torch.Tensor)
    assert tuple(policy_logits.shape) == (1, env.action_space_size)
    assert tuple(values.shape) == (1,)

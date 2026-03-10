from __future__ import annotations

from pathlib import Path

import torch

MISSION_PATH = (
    Path(__file__).resolve().parents[2]
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


def test_learned_policy_evaluation_runs_under_torch_inference_mode() -> None:
    from solo_wargame_ai.eval.learned_policy_eval import evaluate_learned_policy
    from solo_wargame_ai.io.mission_loader import load_mission

    mission = load_mission(MISSION_PATH)
    observed_flags: list[tuple[bool, bool]] = []

    class TorchAwareFirstLegalPolicy:
        name = "torch_aware_first_legal"

        def reset(self) -> None:
            return None

        def select_action(
            self,
            observation: object,
            info: dict[str, object],
            *,
            evaluation: bool,
        ) -> int:
            del observation, evaluation
            observed_flags.append(
                (torch.is_grad_enabled(), torch.is_inference_mode_enabled()),
            )
            return int(info["legal_action_ids"][0])

    evaluation = evaluate_learned_policy(
        mission,
        policy_factory=TorchAwareFirstLegalPolicy,
        seeds=(0,),
        evaluation=True,
    )

    assert evaluation.metrics.episode_count == 1
    assert observed_flags
    assert all(grad_enabled is False for grad_enabled, _ in observed_flags)
    assert all(inference_enabled is True for _, inference_enabled in observed_flags)

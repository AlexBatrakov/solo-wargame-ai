"""Agent, learned-policy, and action-selection surfaces."""

from importlib import import_module
from typing import Any

from .base import Agent, AgentFactory
from .exact_guided_heuristic_agent import ExactGuidedHeuristicAgent
from .feature_adapter import FeatureVector, ObservationFeatureAdapter
from .heuristic_agent import HeuristicAgent
from .learned_policy import (
    LearnedPolicy,
    LearnedPolicyFactory,
    PolicyActionRecord,
    legal_action_ids_from_info,
    legal_action_mask_from_info,
    policy_name,
)
from .masked_action_selection import (
    ActionMaskError,
    MaskedActionSelection,
    select_masked_action,
)
from .random_agent import RandomAgent
from .rollout_search_agent import RolloutEvaluation, RolloutSearchAgent

_LAZY_MASKED_EXPORTS = {
    "ActorCriticActionRecord",
    "MaskedActorCriticNetwork",
    "MaskedActorCriticPolicy",
}


def __getattr__(name: str) -> Any:
    if name in _LAZY_MASKED_EXPORTS:
        module = import_module("solo_wargame_ai.agents.masked_actor_critic")
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(__all__)


__all__ = [
    "ActionMaskError",
    "ActorCriticActionRecord",
    "Agent",
    "AgentFactory",
    "ExactGuidedHeuristicAgent",
    "FeatureVector",
    "HeuristicAgent",
    "LearnedPolicy",
    "LearnedPolicyFactory",
    "MaskedActionSelection",
    "MaskedActorCriticNetwork",
    "MaskedActorCriticPolicy",
    "ObservationFeatureAdapter",
    "PolicyActionRecord",
    "RandomAgent",
    "RolloutEvaluation",
    "RolloutSearchAgent",
    "legal_action_ids_from_info",
    "legal_action_mask_from_info",
    "policy_name",
    "select_masked_action",
]

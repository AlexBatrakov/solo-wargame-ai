"""Masked actor-critic policy boundary for the first Phase 5 learner."""

from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import TYPE_CHECKING

from solo_wargame_ai.env.observation import Observation

from .feature_adapter import ObservationFeatureAdapter
from .learned_policy import (
    LearnedPolicy,
    legal_action_mask_from_info,
)
from .masked_action_selection import (
    ActionMaskError,
    MaskedActionSelection,
    select_masked_action,
)

try:
    import torch
    from torch import nn
except ModuleNotFoundError:  # pragma: no cover - exercised only without torch installed.
    torch = None
    nn = None

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


@dataclass(frozen=True, slots=True)
class ActorCriticActionRecord:
    """One actor-critic action selection plus the current value estimate."""

    action_id: int
    log_prob: float
    entropy: float
    value_estimate: float
class MaskedActorCriticNetwork(nn.Module if nn is not None else object):
    """Small shared-body actor-critic network for the first masked learner."""

    def __init__(
        self,
        *,
        input_dim: int,
        action_count: int,
        hidden_dim: int = 128,
    ) -> None:
        if nn is None:
            raise ModuleNotFoundError(
                "MaskedActorCriticNetwork requires the optional torch dependency",
            )

        super().__init__()
        self._body = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
        )
        self._policy_head = nn.Linear(hidden_dim, action_count)
        self._value_head = nn.Linear(hidden_dim, 1)

    def forward(self, features):
        """Return flat action logits and scalar value estimates for a feature batch."""

        if torch is None:
            raise ModuleNotFoundError(
                "MaskedActorCriticNetwork requires the optional torch dependency",
            )

        feature_tensor = (
            features
            if isinstance(features, torch.Tensor)
            else torch.tensor(features, dtype=torch.float32)
        )
        if feature_tensor.ndim == 1:
            feature_tensor = feature_tensor.unsqueeze(0)

        hidden = self._body(feature_tensor)
        return self._policy_head(hidden), self._value_head(hidden).squeeze(-1)

    def policy_step(
        self,
        features: Sequence[float],
        legal_action_mask: Sequence[bool],
        *,
        evaluation: bool,
        rng: Random | None = None,
    ) -> ActorCriticActionRecord:
        """Run one policy/value forward pass and choose one masked action id."""

        policy_logits, values = self.forward(features)
        logits = tuple(float(logit) for logit in policy_logits[0].detach().tolist())
        selection = select_masked_action(
            logits,
            legal_action_mask,
            evaluation=evaluation,
            rng=rng,
        )
        return ActorCriticActionRecord(
            action_id=selection.action_id,
            log_prob=selection.log_prob,
            entropy=selection.entropy,
            value_estimate=float(values[0].detach().item()),
        )


class MaskedActorCriticPolicy(LearnedPolicy):
    """Observation-to-action wrapper over the feature adapter and torch model."""

    name = "masked_actor_critic"

    def __init__(
        self,
        adapter: ObservationFeatureAdapter,
        model: MaskedActorCriticNetwork,
        *,
        seed: int | None = None,
    ) -> None:
        self._adapter = adapter
        self._model = model
        self._rng = Random(seed)

    def reset(self) -> None:
        """The first learner is feed-forward and keeps no episode-local state."""

    def select_action(
        self,
        observation: Observation,
        info: Mapping[str, object],
        *,
        evaluation: bool = True,
    ) -> int:
        """Select one legal action id using the accepted observation/info seam."""

        return self.policy_step(
            observation,
            info,
            evaluation=evaluation,
        ).action_id

    def policy_step(
        self,
        observation: Observation,
        info: Mapping[str, object],
        *,
        evaluation: bool,
    ) -> ActorCriticActionRecord:
        """Return the full actor-critic decision record for one env step."""

        features = self._adapter.encode(observation)
        return self._model.policy_step(
            features.values,
            legal_action_mask_from_info(info),
            evaluation=evaluation,
            rng=self._rng,
        )
__all__ = [
    "ActionMaskError",
    "ActorCriticActionRecord",
    "MaskedActionSelection",
    "MaskedActorCriticNetwork",
    "MaskedActorCriticPolicy",
    "select_masked_action",
]

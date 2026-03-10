"""Learning-side policy contracts over the accepted env observation surface."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Protocol, TypeAlias

from solo_wargame_ai.env.observation import Observation


@dataclass(frozen=True, slots=True)
class PolicyActionRecord:
    """One policy decision plus optional training-side diagnostics."""

    action_id: int
    log_prob: float | None = None
    entropy: float | None = None
    value_estimate: float | None = None


class LearnedPolicy(Protocol):
    """Select one legal action id from the accepted env observation/info pair."""

    name: str

    def reset(self) -> None:
        """Reset any episode-local policy state."""

    def select_action(
        self,
        observation: Observation,
        info: Mapping[str, object],
        *,
        evaluation: bool = True,
    ) -> int:
        """Return one action id that is legal under ``info``."""


LearnedPolicyFactory: TypeAlias = Callable[[], LearnedPolicy]


def policy_name(policy: LearnedPolicy) -> str:
    """Return a stable name for learned-policy reporting."""

    return str(getattr(policy, "name", type(policy).__name__))


def legal_action_ids_from_info(info: Mapping[str, object]) -> tuple[int, ...]:
    """Read the accepted legal-action id list from env info."""

    return tuple(int(action_id) for action_id in info["legal_action_ids"])


def legal_action_mask_from_info(info: Mapping[str, object]) -> tuple[bool, ...]:
    """Read the accepted legal-action mask from env info."""

    return tuple(bool(is_legal) for is_legal in info["legal_action_mask"])


__all__ = [
    "LearnedPolicy",
    "LearnedPolicyFactory",
    "PolicyActionRecord",
    "legal_action_ids_from_info",
    "legal_action_mask_from_info",
    "policy_name",
]

"""Shared env-layer normalization over the accepted resolver facade."""

from __future__ import annotations

from dataclasses import dataclass

from solo_wargame_ai.domain.actions import GameAction
from solo_wargame_ai.domain.resolver import get_legal_actions, resolve_automatic_progression
from solo_wargame_ai.domain.state import GameState


@dataclass(frozen=True, slots=True)
class NormalizedEnvState:
    """One resolver-normalized decision state plus its current legal actions."""

    state: GameState
    legal_actions: tuple[GameAction, ...]


def normalize_env_state(state: GameState) -> NormalizedEnvState:
    """Normalize raw runtime state to the env-facing decision boundary."""

    progressed_state = resolve_automatic_progression(state)
    return NormalizedEnvState(
        state=progressed_state,
        legal_actions=get_legal_actions(progressed_state),
    )


__all__ = ["NormalizedEnvState", "normalize_env_state"]

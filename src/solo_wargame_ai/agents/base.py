"""Minimal Phase 3 agent contract over the accepted resolver facade.

The stable Package A contract is:

- harness code owns mission loading and initial state construction
- the gameplay loop uses ``resolver.get_legal_actions`` and ``resolver.apply_action``
- agents receive the current ``GameState`` plus the current legal ``GameAction`` tuple
- agents return exactly one action from that legal tuple
- agents do not mutate ``GameState`` directly and do not depend on
  ``domain/legal_actions.py`` or replay helpers
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, TypeAlias

from solo_wargame_ai.domain.actions import GameAction
from solo_wargame_ai.domain.state import GameState


class Agent(Protocol):
    """Select one legal domain action for the current decision state."""

    def select_action(
        self,
        state: GameState,
        legal_actions: tuple[GameAction, ...],
    ) -> GameAction:
        """Return one action from the provided legal tuple."""


AgentFactory: TypeAlias = Callable[[int | None], Agent]


__all__ = ["Agent", "AgentFactory"]

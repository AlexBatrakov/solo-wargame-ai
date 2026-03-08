"""Random baseline agent for the accepted Phase 3 action contract."""

from __future__ import annotations

from random import Random

from solo_wargame_ai.domain.actions import GameAction
from solo_wargame_ai.domain.state import GameState


class RandomAgent:
    """Choose uniformly from the provided legal action tuple."""

    name = "random"

    def __init__(self, *, seed: int | None = None) -> None:
        self.seed = seed
        self._rng = Random(seed)

    def select_action(
        self,
        state: GameState,
        legal_actions: tuple[GameAction, ...],
    ) -> GameAction:
        del state

        if not legal_actions:
            raise ValueError("RandomAgent requires at least one legal action")
        return self._rng.choice(legal_actions)


__all__ = ["RandomAgent"]

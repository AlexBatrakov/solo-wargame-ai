from __future__ import annotations

from typing import cast

import pytest

from solo_wargame_ai.agents.random_agent import RandomAgent
from solo_wargame_ai.domain.actions import (
    AdvanceAction,
    DiscardActivationRollAction,
    TakeCoverAction,
)
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.state import GameState


def test_random_agent_selects_only_from_the_provided_legal_actions() -> None:
    legal_actions = (
        AdvanceAction(destination=HexCoord(0, 2)),
        TakeCoverAction(),
        DiscardActivationRollAction(),
    )
    agent_a = RandomAgent(seed=7)
    agent_b = RandomAgent(seed=7)

    selections_a = [
        agent_a.select_action(cast(GameState, object()), legal_actions)
        for _ in range(8)
    ]
    selections_b = [
        agent_b.select_action(cast(GameState, object()), legal_actions)
        for _ in range(8)
    ]

    assert selections_a == selections_b
    assert all(selection in legal_actions for selection in selections_a)


def test_random_agent_rejects_empty_legal_action_sets() -> None:
    agent = RandomAgent(seed=0)

    with pytest.raises(ValueError, match="at least one legal action"):
        agent.select_action(cast(GameState, object()), ())

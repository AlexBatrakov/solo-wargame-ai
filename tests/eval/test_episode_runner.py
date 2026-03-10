from __future__ import annotations

from collections import deque
from pathlib import Path

import pytest

from solo_wargame_ai.agents.random_agent import RandomAgent
from solo_wargame_ai.domain.actions import (
    AdvanceAction,
    ChooseOrderExecutionAction,
    DiscardActivationRollAction,
    DoubleChoiceOption,
    FireAction,
    GameAction,
    OrderExecutionChoice,
    ResolveDoubleChoiceAction,
    SelectActivationDieAction,
    SelectBritishUnitAction,
    SelectGermanUnitAction,
)
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.state import TerminalOutcome
from solo_wargame_ai.eval.episode_runner import PHASE3_SMOKE_SEEDS, run_episode, run_smoke_episodes
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[2]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def _victory_actions() -> tuple[GameAction, ...]:
    return (
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
        ResolveDoubleChoiceAction(choice=DoubleChoiceOption.KEEP),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
        SelectActivationDieAction(die_value=2),
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.FIRST_ORDER_ONLY),
        AdvanceAction(destination=HexCoord(0, 2)),
        SelectGermanUnitAction(unit_id="qm_1"),
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
        SelectActivationDieAction(die_value=5),
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.BOTH_ORDERS),
        FireAction(target_unit_id="qm_1"),
    )


def _defeat_actions() -> tuple[GameAction, ...]:
    return (
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
        DiscardActivationRollAction(),
    )


class ScriptedAgent:
    name = "scripted"

    def __init__(self, actions: tuple[GameAction, ...]) -> None:
        self._actions = deque(actions)

    def select_action(
        self,
        state: object,
        legal_actions: tuple[GameAction, ...],
    ) -> GameAction:
        del state, legal_actions
        return self._actions.popleft()


class IllegalAgent:
    name = "illegal"

    def select_action(
        self,
        state: object,
        legal_actions: tuple[GameAction, ...],
    ) -> GameAction:
        del state, legal_actions
        return SelectGermanUnitAction(unit_id="qm_1")


@pytest.mark.parametrize(
    ("seed", "actions", "expected_outcome"),
    [
        (0, _victory_actions(), TerminalOutcome.VICTORY),
        (3, _defeat_actions(), TerminalOutcome.DEFEAT),
    ],
    ids=["victory", "defeat"],
)
def test_run_episode_reaches_terminal_states_through_gameplay_flow(
    seed: int,
    actions: tuple[GameAction, ...],
    expected_outcome: TerminalOutcome,
) -> None:
    mission = load_mission(MISSION_PATH)

    run = run_episode(mission, ScriptedAgent(actions), seed=seed)

    assert run.result.terminal_outcome is expected_outcome
    assert run.final_state.terminal_outcome is expected_outcome
    assert run.result.player_decision_count == len(actions)


def test_run_episode_rejects_illegal_agent_actions() -> None:
    mission = load_mission(MISSION_PATH)

    with pytest.raises(ValueError, match="illegal action"):
        run_episode(mission, IllegalAgent(), seed=0)


def test_run_smoke_episodes_is_deterministic_on_the_fixed_16_seed_set() -> None:
    mission = load_mission(MISSION_PATH)

    first_runs = run_smoke_episodes(
        mission,
        agent_factory=lambda seed: RandomAgent(seed=seed),
    )
    second_runs = run_smoke_episodes(
        mission,
        agent_factory=lambda seed: RandomAgent(seed=seed),
    )

    assert tuple(run.result.seed for run in first_runs) == PHASE3_SMOKE_SEEDS
    assert tuple(run.result for run in first_runs) == tuple(run.result for run in second_runs)
    assert all(run.result.terminal_outcome in TerminalOutcome for run in first_runs)

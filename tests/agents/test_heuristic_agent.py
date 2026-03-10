from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from solo_wargame_ai.agents.heuristic_agent import HeuristicAgent
from solo_wargame_ai.domain.actions import (
    AdvanceAction,
    DoubleChoiceOption,
    ResolveDoubleChoiceAction,
    SelectActivationDieAction,
    SelectBritishUnitAction,
)
from solo_wargame_ai.domain.decision_context import (
    ChooseActivationDieContext,
    ChooseDoubleChoiceContext,
    ChooseOrderParameterContext,
)
from solo_wargame_ai.domain.enums import HexDirection
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.mission import OrderName
from solo_wargame_ai.domain.resolver import get_legal_actions
from solo_wargame_ai.domain.state import (
    CurrentActivation,
    create_initial_game_state,
    validate_game_state,
)
from solo_wargame_ai.domain.units import GermanUnitStatus, RevealedGermanUnitState
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[2]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def test_heuristic_agent_selects_only_from_the_provided_legal_actions() -> None:
    mission = load_mission(MISSION_PATH)
    state = create_initial_game_state(mission, seed=0)
    legal_actions = get_legal_actions(state)
    agent = HeuristicAgent()

    first_choice = agent.select_action(state, legal_actions)
    second_choice = agent.select_action(state, legal_actions)

    assert first_choice == second_choice
    assert first_choice in legal_actions
    assert first_choice == SelectBritishUnitAction(unit_id="rifle_squad_a")


def test_heuristic_agent_rejects_empty_legal_action_sets() -> None:
    mission = load_mission(MISSION_PATH)
    state = create_initial_game_state(mission, seed=0)

    with pytest.raises(ValueError, match="at least one legal action"):
        HeuristicAgent().select_action(state, ())


def test_heuristic_agent_prefers_advancing_to_reveal_the_hidden_marker() -> None:
    mission = load_mission(MISSION_PATH)
    base_state = create_initial_game_state(mission, seed=0)
    state = replace(
        base_state,
        pending_decision=ChooseOrderParameterContext(
            order=OrderName.ADVANCE,
            order_index=0,
        ),
        current_activation=CurrentActivation(
            active_unit_id="rifle_squad_a",
            roll=(3, 3),
            selected_die=3,
            planned_orders=(OrderName.ADVANCE, OrderName.TAKE_COVER),
            next_order_index=0,
        ),
    )
    validate_game_state(state)

    legal_actions = get_legal_actions(state)
    selected_action = HeuristicAgent().select_action(state, legal_actions)

    assert selected_action == AdvanceAction(destination=HexCoord(0, 2))


def test_heuristic_agent_prefers_keep_when_a_double_gives_an_immediate_attack_row() -> None:
    mission = load_mission(MISSION_PATH)
    base_state = create_initial_game_state(mission, seed=0)
    state = replace(
        base_state,
        british_units={
            **base_state.british_units,
            "rifle_squad_a": replace(
                base_state.british_units["rifle_squad_a"],
                position=HexCoord(0, 2),
            ),
        },
        german_units={
            "qm_1": RevealedGermanUnitState(
                unit_id="qm_1",
                unit_class="light_machine_gun",
                position=HexCoord(0, 1),
                facing=HexDirection.DOWN,
                status=GermanUnitStatus.ACTIVE,
            ),
        },
        unresolved_markers={},
        pending_decision=ChooseDoubleChoiceContext(),
        current_activation=CurrentActivation(
            active_unit_id="rifle_squad_a",
            roll=(4, 4),
        ),
    )
    validate_game_state(state)

    legal_actions = get_legal_actions(state)
    selected_action = HeuristicAgent().select_action(state, legal_actions)

    assert selected_action == ResolveDoubleChoiceAction(choice=DoubleChoiceOption.KEEP)


def test_heuristic_agent_prefers_the_attack_die_when_already_adjacent_to_a_german_unit() -> None:
    mission = load_mission(MISSION_PATH)
    base_state = create_initial_game_state(mission, seed=0)
    state = replace(
        base_state,
        british_units={
            **base_state.british_units,
            "rifle_squad_a": replace(
                base_state.british_units["rifle_squad_a"],
                position=HexCoord(0, 2),
            ),
        },
        german_units={
            "qm_1": RevealedGermanUnitState(
                unit_id="qm_1",
                unit_class="light_machine_gun",
                position=HexCoord(0, 1),
                facing=HexDirection.DOWN,
                status=GermanUnitStatus.ACTIVE,
            ),
        },
        unresolved_markers={},
        pending_decision=ChooseActivationDieContext(),
        current_activation=CurrentActivation(
            active_unit_id="rifle_squad_a",
            roll=(3, 4),
        ),
    )
    validate_game_state(state)

    legal_actions = get_legal_actions(state)
    selected_action = HeuristicAgent().select_action(state, legal_actions)

    assert selected_action == SelectActivationDieAction(die_value=4)

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from solo_wargame_ai.agents.mission3_heuristic_agent import Mission3HeuristicAgent
from solo_wargame_ai.domain.actions import AdvanceAction, ScoutAction, SelectBritishUnitAction
from solo_wargame_ai.domain.combat import german_fire_zone_hexes
from solo_wargame_ai.domain.decision_context import ChooseOrderParameterContext
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.mission import OrderName
from solo_wargame_ai.domain.resolver import get_legal_actions
from solo_wargame_ai.domain.state import (
    CurrentActivation,
    create_initial_game_state,
    validate_game_state,
)
from solo_wargame_ai.domain.units import BritishMorale, GermanUnitStatus, RevealedGermanUnitState
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[2]
    / "configs"
    / "missions"
    / "mission_03_secure_the_building.toml"
)


def test_mission3_heuristic_agent_selects_only_from_the_provided_legal_actions() -> None:
    mission = load_mission(MISSION_PATH)
    state = create_initial_game_state(mission, seed=0)
    legal_actions = get_legal_actions(state)
    agent = Mission3HeuristicAgent()

    first_choice = agent.select_action(state, legal_actions)
    second_choice = agent.select_action(state, legal_actions)

    assert first_choice == second_choice
    assert first_choice in legal_actions
    assert first_choice == SelectBritishUnitAction(unit_id="rifle_squad_a")


def test_mission3_heuristic_agent_rejects_empty_legal_action_sets() -> None:
    mission = load_mission(MISSION_PATH)
    state = create_initial_game_state(mission, seed=0)

    with pytest.raises(ValueError, match="at least one legal action"):
        Mission3HeuristicAgent().select_action(state, ())


def test_mission3_heuristic_prefers_advancing_to_reveal_all_three_markers() -> None:
    mission = load_mission(MISSION_PATH)
    base_state = create_initial_game_state(mission, seed=0)
    state = replace(
        base_state,
        british_units={
            **base_state.british_units,
            "rifle_squad_a": replace(
                base_state.british_units["rifle_squad_a"],
                position=HexCoord(0, 3),
                morale=BritishMorale.NORMAL,
            ),
            "rifle_squad_b": replace(
                base_state.british_units["rifle_squad_b"],
                position=HexCoord(-2, 4),
            ),
            "rifle_squad_c": replace(
                base_state.british_units["rifle_squad_c"],
                position=HexCoord(0, 4),
            ),
        },
        pending_decision=ChooseOrderParameterContext(
            order=OrderName.ADVANCE,
            order_index=0,
        ),
        current_activation=CurrentActivation(
            active_unit_id="rifle_squad_a",
            roll=(6, 2),
            selected_die=2,
            planned_orders=(OrderName.ADVANCE,),
            next_order_index=0,
        ),
    )
    validate_game_state(state)

    legal_actions = get_legal_actions(state)
    selected_action = Mission3HeuristicAgent().select_action(state, legal_actions)

    assert selected_action == AdvanceAction(destination=HexCoord(0, 2))


def test_mission3_heuristic_prefers_the_safest_building_scout_facing() -> None:
    mission = load_mission(MISSION_PATH)
    base_state = create_initial_game_state(mission, seed=0)
    state = replace(
        base_state,
        british_units={
            **base_state.british_units,
            "rifle_squad_a": replace(
                base_state.british_units["rifle_squad_a"],
                position=HexCoord(0, 3),
            ),
            "rifle_squad_b": replace(
                base_state.british_units["rifle_squad_b"],
                position=HexCoord(0, 2),
            ),
            "rifle_squad_c": replace(
                base_state.british_units["rifle_squad_c"],
                position=HexCoord(1, 2),
            ),
        },
        unresolved_markers={
            "qm_2": base_state.unresolved_markers["qm_2"],
        },
        pending_decision=ChooseOrderParameterContext(
            order=OrderName.SCOUT,
            order_index=0,
        ),
        current_activation=CurrentActivation(
            active_unit_id="rifle_squad_a",
            roll=(2, 2),
            selected_die=2,
            planned_orders=(OrderName.SCOUT,),
            next_order_index=0,
        ),
    )
    validate_game_state(state)

    legal_actions = get_legal_actions(state)
    scout_actions = tuple(action for action in legal_actions if isinstance(action, ScoutAction))
    expected_action = min(
        scout_actions,
        key=lambda action: (
            sum(
                1
                for unit in state.british_units.values()
                if unit.position
                in german_fire_zone_hexes(
                    state.mission,
                    RevealedGermanUnitState(
                        unit_id="qm_2",
                        unit_class="light_machine_gun",
                        position=state.unresolved_markers["qm_2"].position,
                        facing=action.facing,
                        status=GermanUnitStatus.ACTIVE,
                    ),
                )
            ),
            action.facing.value,
        ),
    )
    selected_action = Mission3HeuristicAgent().select_action(state, legal_actions)

    assert selected_action == expected_action

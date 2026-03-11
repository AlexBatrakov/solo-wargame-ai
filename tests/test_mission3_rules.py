from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from solo_wargame_ai.domain.combat import calculate_fire_threshold
from solo_wargame_ai.domain.decision_context import (
    ChooseGermanUnitContext,
    ChooseOrderParameterContext,
)
from solo_wargame_ai.domain.enums import HexDirection
from solo_wargame_ai.domain.german_fire import calculate_german_fire_threshold
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.mission import OrderName
from solo_wargame_ai.domain.state import (
    CurrentActivation,
    GamePhase,
    create_initial_game_state,
)
from solo_wargame_ai.domain.units import BritishMorale, GermanUnitStatus, RevealedGermanUnitState
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_03_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_03_secure_the_building.toml"
)


def test_mission_03_initial_state_stacks_three_british_units_on_the_single_start_hex() -> None:
    mission = load_mission(MISSION_03_PATH)
    state = create_initial_game_state(mission, seed=0)

    assert tuple(state.british_units) == (
        "rifle_squad_a",
        "rifle_squad_b",
        "rifle_squad_c",
    )
    assert {unit.position for unit in state.british_units.values()} == {HexCoord(0, 4)}


def test_mission_03_fire_threshold_includes_building_and_hill_modifiers() -> None:
    state = _stage_british_fire_state(
        attacker_position=HexCoord(0, 2),
        defender_unit_id="qm_2",
        defender_position=HexCoord(0, 1),
        defender_facing=HexDirection.DOWN,
    )

    threshold = calculate_fire_threshold(
        state.mission,
        attacker=state.british_units["rifle_squad_a"],
        defender=state.german_units["qm_2"],
        british_units=state.british_units,
    )

    assert threshold == 9


def test_mission_03_wooded_hill_counts_as_woods_when_targeted() -> None:
    state = _stage_british_fire_state(
        attacker_position=HexCoord(0, 1),
        defender_unit_id="qm_1",
        defender_position=HexCoord(1, 0),
        defender_facing=HexDirection.DOWN_LEFT,
    )

    threshold = calculate_fire_threshold(
        state.mission,
        attacker=state.british_units["rifle_squad_a"],
        defender=state.german_units["qm_1"],
        british_units=state.british_units,
    )

    assert threshold == 9


def test_mission_03_wooded_hill_counts_as_hill_when_attacking() -> None:
    wooded_hill_state = _stage_british_fire_state(
        attacker_position=HexCoord(1, 0),
        defender_unit_id="qm_3",
        defender_position=HexCoord(1, 1),
        defender_facing=HexDirection.UP,
    )
    clear_state = _stage_british_fire_state(
        attacker_position=HexCoord(1, 2),
        defender_unit_id="qm_3",
        defender_position=HexCoord(1, 1),
        defender_facing=HexDirection.DOWN,
    )

    wooded_hill_threshold = calculate_fire_threshold(
        wooded_hill_state.mission,
        attacker=wooded_hill_state.british_units["rifle_squad_a"],
        defender=wooded_hill_state.german_units["qm_3"],
        british_units=wooded_hill_state.british_units,
    )
    clear_threshold = calculate_fire_threshold(
        clear_state.mission,
        attacker=clear_state.british_units["rifle_squad_a"],
        defender=clear_state.german_units["qm_3"],
        british_units=clear_state.british_units,
    )

    assert wooded_hill_threshold == 7
    assert clear_threshold == 8


def test_mission_03_german_rifle_squad_uses_its_mission_attack_threshold() -> None:
    rifle_squad_state = _stage_german_fire_state(
        german_unit_class="german_rifle_squad",
        german_position=HexCoord(1, 1),
        british_position=HexCoord(0, 2),
    )
    light_machine_gun_state = _stage_german_fire_state(
        german_unit_class="light_machine_gun",
        german_position=HexCoord(1, 1),
        british_position=HexCoord(0, 2),
    )

    rifle_squad_threshold = calculate_german_fire_threshold(
        rifle_squad_state,
        attacker_unit_id="qm_3",
        target_unit_id="rifle_squad_a",
    )
    light_machine_gun_threshold = calculate_german_fire_threshold(
        light_machine_gun_state,
        attacker_unit_id="qm_3",
        target_unit_id="rifle_squad_a",
    )

    assert rifle_squad_threshold == 8
    assert light_machine_gun_threshold == 6


def _stage_british_fire_state(
    *,
    attacker_position: HexCoord,
    defender_unit_id: str,
    defender_position: HexCoord,
    defender_facing: HexDirection,
):
    mission = load_mission(MISSION_03_PATH)
    base_state = create_initial_game_state(mission, seed=0)
    british_units = dict(base_state.british_units)
    british_units["rifle_squad_a"] = replace(
        british_units["rifle_squad_a"],
        position=attacker_position,
        morale=BritishMorale.NORMAL,
    )
    british_units["rifle_squad_b"] = replace(
        british_units["rifle_squad_b"],
        position=HexCoord(-2, 4),
    )
    british_units["rifle_squad_c"] = replace(
        british_units["rifle_squad_c"],
        position=HexCoord(0, 4),
    )

    german_units = {
        defender_unit_id: _german_unit(
            defender_unit_id,
            defender_position,
            facing=defender_facing,
        ),
    }

    return replace(
        base_state,
        british_units=british_units,
        german_units=german_units,
        unresolved_markers={},
        current_activation=CurrentActivation(
            active_unit_id="rifle_squad_a",
            roll=(6, 1),
            selected_die=6,
            planned_orders=(OrderName.FIRE,),
            next_order_index=0,
        ),
        pending_decision=ChooseOrderParameterContext(
            order=OrderName.FIRE,
            order_index=0,
        ),
    )


def _stage_german_fire_state(
    *,
    german_unit_class: str,
    german_position: HexCoord,
    british_position: HexCoord,
):
    mission = load_mission(MISSION_03_PATH)
    base_state = create_initial_game_state(mission, seed=0)
    british_units = dict(base_state.british_units)
    british_units["rifle_squad_a"] = replace(
        british_units["rifle_squad_a"],
        position=british_position,
        cover=0,
    )

    return replace(
        base_state,
        phase=GamePhase.GERMAN,
        british_units=british_units,
        german_units={
            "qm_3": _german_unit(
                "qm_3",
                german_position,
                unit_class=german_unit_class,
                facing=HexDirection.DOWN_LEFT,
            ),
        },
        unresolved_markers={},
        activated_british_unit_ids=frozenset(base_state.british_units),
        pending_decision=ChooseGermanUnitContext(),
        current_activation=None,
    )


def _german_unit(
    unit_id: str,
    position: HexCoord,
    *,
    unit_class: str = "light_machine_gun",
    facing: HexDirection = HexDirection.DOWN,
    status: GermanUnitStatus = GermanUnitStatus.ACTIVE,
) -> RevealedGermanUnitState:
    return RevealedGermanUnitState(
        unit_id=unit_id,
        unit_class=unit_class,
        position=position,
        facing=facing,
        status=status,
    )

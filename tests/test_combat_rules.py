from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from solo_wargame_ai.domain.actions import AdvanceAction, FireAction, GrenadeAttackAction
from solo_wargame_ai.domain.combat import (
    calculate_fire_threshold,
    calculate_grenade_attack_threshold,
    degrade_british_morale,
)
from solo_wargame_ai.domain.decision_context import ChooseOrderParameterContext
from solo_wargame_ai.domain.enums import HexDirection
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.legal_actions import apply_action, get_legal_actions
from solo_wargame_ai.domain.mission import BritishUnitDefinition, HiddenMarker, OrderName
from solo_wargame_ai.domain.state import CurrentActivation, GamePhase, create_initial_game_state
from solo_wargame_ai.domain.units import BritishMorale, GermanUnitStatus, RevealedGermanUnitState
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def test_fire_legal_targets_are_only_adjacent_revealed_active_german_units() -> None:
    mission = _mission_with_hidden_markers(
        HiddenMarker(marker_id="qm_1", coord=HexCoord(0, 2)),
        HiddenMarker(marker_id="qm_2", coord=HexCoord(1, 2)),
        HiddenMarker(marker_id="qm_3", coord=HexCoord(0, 1)),
    )
    state = _stage_attack_state(
        mission=mission,
        order=OrderName.FIRE,
        german_units={
            "qm_1": _german_unit("qm_1", HexCoord(0, 2)),
            "qm_2": _german_unit(
                "qm_2",
                HexCoord(1, 2),
                status=GermanUnitStatus.REMOVED,
            ),
            "qm_3": _german_unit("qm_3", HexCoord(0, 1)),
        },
    )

    assert get_legal_actions(state) == (FireAction(target_unit_id="qm_1"),)


def test_grenade_attack_legal_targets_are_only_adjacent_revealed_active_german_units() -> None:
    mission = _mission_with_hidden_markers(
        HiddenMarker(marker_id="qm_1", coord=HexCoord(1, 2)),
        HiddenMarker(marker_id="qm_2", coord=HexCoord(-1, 2)),
        HiddenMarker(marker_id="qm_3", coord=HexCoord(0, 1)),
    )
    state = _stage_attack_state(
        mission=mission,
        order=OrderName.GRENADE_ATTACK,
        german_units={
            "qm_1": _german_unit("qm_1", HexCoord(1, 2)),
            "qm_2": _german_unit(
                "qm_2",
                HexCoord(-1, 2),
                status=GermanUnitStatus.REMOVED,
            ),
            "qm_3": _german_unit("qm_3", HexCoord(0, 1)),
        },
    )

    assert get_legal_actions(state) == (GrenadeAttackAction(target_unit_id="qm_1"),)


def test_fire_threshold_includes_woods_modifier_from_target_hex() -> None:
    mission = _mission_with_hidden_markers(
        HiddenMarker(marker_id="qm_1", coord=HexCoord(1, 2)),
    )
    state = _stage_attack_state(
        mission=mission,
        order=OrderName.FIRE,
        british_positions={"rifle_squad_b": HexCoord(0, 0)},
        german_units={"qm_1": _german_unit("qm_1", HexCoord(1, 2))},
    )

    threshold = calculate_fire_threshold(
        state.mission,
        attacker=state.british_units["rifle_squad_a"],
        defender=state.german_units["qm_1"],
        british_units=state.british_units,
    )

    assert threshold == 9


def test_fire_gets_flanking_modifier_when_attacker_is_outside_target_fire_zone() -> None:
    mission = _mission_with_hidden_markers(
        HiddenMarker(marker_id="qm_1", coord=HexCoord(0, 2)),
    )
    state = _stage_attack_state(
        mission=mission,
        order=OrderName.FIRE,
        active_position=HexCoord(-1, 2),
        british_positions={"rifle_squad_b": HexCoord(0, 0)},
        german_units={
            "qm_1": _german_unit(
                "qm_1",
                HexCoord(0, 2),
                facing=HexDirection.DOWN,
            ),
        },
    )

    threshold = calculate_fire_threshold(
        state.mission,
        attacker=state.british_units["rifle_squad_a"],
        defender=state.german_units["qm_1"],
        british_units=state.british_units,
    )

    assert threshold == 7


def test_fire_gets_support_modifier_for_each_other_adjacent_british_unit() -> None:
    mission = _mission_with_hidden_markers(
        HiddenMarker(marker_id="qm_1", coord=HexCoord(0, 2)),
        extra_british_units=1,
    )
    state = _stage_attack_state(
        mission=mission,
        order=OrderName.FIRE,
        german_units={"qm_1": _german_unit("qm_1", HexCoord(0, 2))},
        british_positions={
            "rifle_squad_b": HexCoord(-1, 2),
            "rifle_squad_extra_1": HexCoord(1, 2),
        },
    )

    threshold = calculate_fire_threshold(
        state.mission,
        attacker=state.british_units["rifle_squad_a"],
        defender=state.german_units["qm_1"],
        british_units=state.british_units,
    )

    assert threshold == 6


def test_fire_support_does_not_count_the_attacking_unit_itself() -> None:
    mission = _mission_with_hidden_markers(
        HiddenMarker(marker_id="qm_1", coord=HexCoord(0, 2)),
    )
    state = _stage_attack_state(
        mission=mission,
        order=OrderName.FIRE,
        british_positions={"rifle_squad_b": HexCoord(0, 0)},
        german_units={"qm_1": _german_unit("qm_1", HexCoord(0, 2))},
    )

    threshold = calculate_fire_threshold(
        state.mission,
        attacker=state.british_units["rifle_squad_a"],
        defender=state.german_units["qm_1"],
        british_units=state.british_units,
    )

    assert threshold == 8


def test_grenade_attack_ignores_woods_flanking_and_support_modifiers() -> None:
    mission = _mission_with_hidden_markers(
        HiddenMarker(marker_id="qm_1", coord=HexCoord(1, 2)),
        extra_british_units=1,
    )
    state = _stage_attack_state(
        mission=mission,
        order=OrderName.GRENADE_ATTACK,
        active_position=HexCoord(0, 3),
        german_units={
            "qm_1": _german_unit(
                "qm_1",
                HexCoord(1, 2),
                facing=HexDirection.UP,
            ),
        },
        british_positions={
            "rifle_squad_b": HexCoord(1, 1),
            "rifle_squad_extra_1": HexCoord(0, 0),
        },
    )

    threshold = calculate_grenade_attack_threshold(
        state.mission,
        attacker=state.british_units["rifle_squad_a"],
    )

    assert threshold == 6


def test_successful_fire_marks_the_german_target_removed() -> None:
    mission = _mission_with_hidden_markers(
        HiddenMarker(marker_id="qm_1", coord=HexCoord(0, 2)),
    )
    state = _stage_attack_state(
        mission=mission,
        order=OrderName.FIRE,
        seed=9,
        british_positions={"rifle_squad_b": HexCoord(0, 0)},
        german_units={"qm_1": _german_unit("qm_1", HexCoord(0, 2))},
    )

    next_state = apply_action(state, FireAction(target_unit_id="qm_1"))

    assert next_state.german_units["qm_1"].status is GermanUnitStatus.REMOVED
    assert next_state.rng_state != state.rng_state


def test_missed_fire_leaves_the_german_target_active() -> None:
    mission = _mission_with_hidden_markers(
        HiddenMarker(marker_id="qm_1", coord=HexCoord(0, 2)),
    )
    state = _stage_attack_state(
        mission=mission,
        order=OrderName.FIRE,
        seed=4,
        british_positions={"rifle_squad_b": HexCoord(0, 0)},
        german_units={"qm_1": _german_unit("qm_1", HexCoord(0, 2))},
    )

    next_state = apply_action(state, FireAction(target_unit_id="qm_1"))

    assert next_state.german_units["qm_1"].status is GermanUnitStatus.ACTIVE
    assert next_state.rng_state != state.rng_state


@pytest.mark.parametrize(
    ("seed", "expected_status"),
    [
        (1, GermanUnitStatus.REMOVED),
        (4, GermanUnitStatus.ACTIVE),
    ],
)
def test_grenade_attack_resolves_without_standard_modifiers(
    seed: int,
    expected_status: GermanUnitStatus,
) -> None:
    mission = _mission_with_hidden_markers(
        HiddenMarker(marker_id="qm_1", coord=HexCoord(1, 2)),
        extra_british_units=1,
    )
    state = _stage_attack_state(
        mission=mission,
        order=OrderName.GRENADE_ATTACK,
        seed=seed,
        german_units={
            "qm_1": _german_unit(
                "qm_1",
                HexCoord(1, 2),
                facing=HexDirection.UP,
            ),
        },
        british_positions={
            "rifle_squad_b": HexCoord(1, 1),
            "rifle_squad_extra_1": HexCoord(0, 0),
        },
    )

    next_state = apply_action(state, GrenadeAttackAction(target_unit_id="qm_1"))

    assert next_state.german_units["qm_1"].status is expected_status


def test_resolved_attack_either_stages_the_next_order_or_ends_the_activation() -> None:
    mission = _mission_with_hidden_markers(
        HiddenMarker(marker_id="qm_1", coord=HexCoord(0, 2)),
    )
    state = _stage_attack_state(
        mission=mission,
        order=OrderName.FIRE,
        planned_orders=(OrderName.FIRE, OrderName.ADVANCE),
        seed=9,
        british_positions={"rifle_squad_b": HexCoord(0, 0)},
        german_units={"qm_1": _german_unit("qm_1", HexCoord(0, 2))},
    )

    next_state = apply_action(state, FireAction(target_unit_id="qm_1"))

    assert isinstance(next_state.pending_decision, ChooseOrderParameterContext)
    assert next_state.pending_decision.order is OrderName.ADVANCE
    assert next_state.pending_decision.order_index == 1
    assert get_legal_actions(next_state) == (
        AdvanceAction(destination=HexCoord(-1, 3)),
        AdvanceAction(destination=HexCoord(0, 2)),
        AdvanceAction(destination=HexCoord(1, 2)),
    )

    advanced_state = apply_action(next_state, AdvanceAction(destination=HexCoord(0, 2)))

    assert advanced_state.british_units["rifle_squad_a"].position == HexCoord(0, 2)
    assert advanced_state.current_activation is None
    assert advanced_state.phase is GamePhase.BRITISH

    end_state = _stage_attack_state(
        mission=mission,
        order=OrderName.FIRE,
        seed=4,
        british_positions={"rifle_squad_b": HexCoord(0, 0)},
        german_units={"qm_1": _german_unit("qm_1", HexCoord(0, 2))},
    )

    end_state = apply_action(end_state, FireAction(target_unit_id="qm_1"))

    assert end_state.current_activation is None
    assert end_state.phase is GamePhase.BRITISH
    assert end_state.activated_british_unit_ids == frozenset({"rifle_squad_a"})


def test_british_morale_helper_enforces_normal_low_removed_ladder() -> None:
    assert degrade_british_morale(BritishMorale.NORMAL) is BritishMorale.LOW
    assert degrade_british_morale(BritishMorale.LOW) is BritishMorale.REMOVED
    assert degrade_british_morale(BritishMorale.REMOVED) is BritishMorale.REMOVED


def _mission_with_hidden_markers(
    *markers: HiddenMarker,
    extra_british_units: int = 0,
):
    mission = load_mission(MISSION_PATH)
    roster = mission.british.roster + tuple(
        BritishUnitDefinition(
            unit_id=f"rifle_squad_extra_{index + 1}",
            unit_class="rifle_squad",
        )
        for index in range(extra_british_units)
    )
    return replace(
        mission,
        map=replace(mission.map, hidden_markers=markers),
        british=replace(mission.british, roster=roster),
    )


def _stage_attack_state(
    *,
    mission=None,
    order: OrderName,
    seed: int = 0,
    active_unit_id: str = "rifle_squad_a",
    active_position: HexCoord = HexCoord(0, 3),
    planned_orders: tuple[OrderName, ...] | None = None,
    next_order_index: int = 0,
    german_units: dict[str, RevealedGermanUnitState],
    british_positions: dict[str, HexCoord] | None = None,
    british_morales: dict[str, BritishMorale] | None = None,
):
    if mission is None:
        mission = load_mission(MISSION_PATH)

    if planned_orders is None:
        planned_orders = (order,)

    base_state = create_initial_game_state(mission, seed=seed)
    british_units = dict(base_state.british_units)
    positions = {active_unit_id: active_position}
    if british_positions is not None:
        positions.update(british_positions)

    morales = {} if british_morales is None else british_morales
    for unit_id, unit_state in list(british_units.items()):
        british_units[unit_id] = replace(
            unit_state,
            position=positions.get(unit_id, unit_state.position),
            morale=morales.get(unit_id, unit_state.morale),
        )

    unresolved_markers = {
        marker_id: marker_state
        for marker_id, marker_state in base_state.unresolved_markers.items()
        if marker_id not in german_units
    }

    return replace(
        base_state,
        british_units=british_units,
        german_units=german_units,
        unresolved_markers=unresolved_markers,
        pending_decision=ChooseOrderParameterContext(
            order=planned_orders[next_order_index],
            order_index=next_order_index,
        ),
        current_activation=CurrentActivation(
            active_unit_id=active_unit_id,
            roll=(4, 1),
            selected_die=4,
            planned_orders=planned_orders,
            next_order_index=next_order_index,
        ),
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

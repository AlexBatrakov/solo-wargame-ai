from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from solo_wargame_ai.domain.actions import SelectGermanUnitAction
from solo_wargame_ai.domain.decision_context import ChooseGermanUnitContext, DecisionContextKind
from solo_wargame_ai.domain.enums import HexDirection
from solo_wargame_ai.domain.german_fire import calculate_german_fire_threshold
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.mission import BritishUnitDefinition, HiddenMarker
from solo_wargame_ai.domain.resolver import (
    apply_action,
    get_legal_actions,
    resolve_automatic_progression,
)
from solo_wargame_ai.domain.state import GamePhase, create_initial_game_state
from solo_wargame_ai.domain.units import BritishMorale, GermanUnitStatus, RevealedGermanUnitState
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def test_legal_german_choices_include_only_active_revealed_unactivated_units() -> None:
    mission = _mission_with_hidden_markers(
        HiddenMarker(marker_id="qm_1", coord=HexCoord(0, 1)),
        HiddenMarker(marker_id="qm_2", coord=HexCoord(1, 1)),
        HiddenMarker(marker_id="qm_3", coord=HexCoord(-1, 2)),
    )
    state = _german_phase_state(
        mission=mission,
        german_units={
            "qm_1": _german_unit("qm_1", HexCoord(0, 1)),
            "qm_2": _german_unit("qm_2", HexCoord(1, 1)),
            "qm_3": _german_unit(
                "qm_3",
                HexCoord(-1, 2),
                status=GermanUnitStatus.REMOVED,
            ),
        },
        activated_german_unit_ids=frozenset({"qm_2"}),
    )

    assert get_legal_actions(state) == (SelectGermanUnitAction(unit_id="qm_1"),)


def test_selecting_german_unit_automatically_attacks_adjacent_targets_in_fire_zone_only() -> None:
    mission = _mission_with_hidden_markers(
        HiddenMarker(marker_id="qm_1", coord=HexCoord(0, 1)),
        extra_british_units=2,
    )
    state = _german_phase_state(
        mission=mission,
        seed=3,
        british_positions={
            "rifle_squad_a": HexCoord(-1, 2),
            "rifle_squad_b": HexCoord(0, 2),
            "rifle_squad_extra_1": HexCoord(0, 0),
            "rifle_squad_extra_2": HexCoord(0, 3),
        },
        german_units={
            "qm_1": _german_unit(
                "qm_1",
                HexCoord(0, 1),
                unit_class="heavy_machine_gun",
                facing=HexDirection.DOWN,
            ),
        },
    )

    next_state = apply_action(state, SelectGermanUnitAction(unit_id="qm_1"))

    assert next_state.british_units["rifle_squad_a"].morale is BritishMorale.LOW
    assert next_state.british_units["rifle_squad_b"].morale is BritishMorale.LOW
    assert next_state.british_units["rifle_squad_extra_1"].morale is BritishMorale.NORMAL
    assert next_state.british_units["rifle_squad_extra_2"].morale is BritishMorale.NORMAL


def test_woods_and_cover_raise_german_attack_threshold() -> None:
    mission = _mission_with_hidden_markers(HiddenMarker(marker_id="qm_1", coord=HexCoord(0, 1)))
    state = _german_phase_state(
        mission=mission,
        british_positions={"rifle_squad_a": HexCoord(-1, 2)},
        british_cover={"rifle_squad_a": 2},
        german_units={
            "qm_1": _german_unit(
                "qm_1",
                HexCoord(0, 1),
                unit_class="heavy_machine_gun",
                facing=HexDirection.DOWN,
            ),
        },
    )

    threshold = calculate_german_fire_threshold(
        state,
        attacker_unit_id="qm_1",
        target_unit_id="rifle_squad_a",
    )

    assert threshold == 8


def test_german_hits_degrade_british_morale_along_stage_6a_ladder() -> None:
    mission = _mission_with_hidden_markers(HiddenMarker(marker_id="qm_1", coord=HexCoord(0, 1)))
    state = _german_phase_state(
        mission=mission,
        seed=3,
        british_positions={
            "rifle_squad_a": HexCoord(-1, 2),
            "rifle_squad_b": HexCoord(0, 2),
        },
        british_morales={"rifle_squad_b": BritishMorale.LOW},
        german_units={
            "qm_1": _german_unit(
                "qm_1",
                HexCoord(0, 1),
                unit_class="heavy_machine_gun",
                facing=HexDirection.DOWN,
            ),
        },
    )

    next_state = apply_action(state, SelectGermanUnitAction(unit_id="qm_1"))

    assert next_state.british_units["rifle_squad_a"].morale is BritishMorale.LOW
    assert next_state.british_units["rifle_squad_b"].morale is BritishMorale.REMOVED


def test_removed_british_units_are_not_retarged_by_later_german_fire_resolution() -> None:
    mission = _mission_with_hidden_markers(HiddenMarker(marker_id="qm_1", coord=HexCoord(0, 1)))
    state = _german_phase_state(
        mission=mission,
        seed=0,
        british_positions={
            "rifle_squad_a": HexCoord(-1, 2),
            "rifle_squad_b": HexCoord(0, 2),
        },
        british_morales={"rifle_squad_a": BritishMorale.REMOVED},
        german_units={
            "qm_1": _german_unit(
                "qm_1",
                HexCoord(0, 1),
                unit_class="heavy_machine_gun",
                facing=HexDirection.DOWN,
            ),
        },
    )

    next_state = apply_action(state, SelectGermanUnitAction(unit_id="qm_1"))

    assert next_state.british_units["rifle_squad_a"].morale is BritishMorale.REMOVED
    assert next_state.british_units["rifle_squad_b"].morale is BritishMorale.LOW


def test_activated_german_bookkeeping_updates_and_next_choice_remains_explicit() -> None:
    mission = _mission_with_hidden_markers(
        HiddenMarker(marker_id="qm_1", coord=HexCoord(0, 1)),
        HiddenMarker(marker_id="qm_2", coord=HexCoord(1, 1)),
    )
    state = _german_phase_state(
        mission=mission,
        seed=3,
        british_positions={"rifle_squad_a": HexCoord(0, 2)},
        german_units={
            "qm_1": _german_unit("qm_1", HexCoord(0, 1), facing=HexDirection.DOWN),
            "qm_2": _german_unit("qm_2", HexCoord(1, 1), facing=HexDirection.DOWN_LEFT),
        },
    )

    next_state = apply_action(state, SelectGermanUnitAction(unit_id="qm_1"))

    assert next_state.phase is GamePhase.GERMAN
    assert isinstance(next_state.pending_decision, ChooseGermanUnitContext)
    assert next_state.pending_decision.kind is DecisionContextKind.CHOOSE_GERMAN_UNIT
    assert next_state.current_activation is None
    assert next_state.activated_german_unit_ids == frozenset({"qm_1"})
    assert get_legal_actions(next_state) == (SelectGermanUnitAction(unit_id="qm_2"),)


def test_when_no_selectable_germans_remain_non_terminal_turn_rolls_over() -> None:
    mission = _mission_with_hidden_markers(HiddenMarker(marker_id="qm_1", coord=HexCoord(0, 1)))
    state = _german_phase_state(
        mission=mission,
        turn=1,
        german_units={},
        activated_british_unit_ids=frozenset({"rifle_squad_a", "rifle_squad_b"}),
        activated_german_unit_ids=frozenset(),
    )

    next_state = resolve_automatic_progression(state)

    assert next_state.turn == 2
    assert next_state.phase is GamePhase.BRITISH
    assert next_state.pending_decision.kind is DecisionContextKind.CHOOSE_BRITISH_UNIT
    assert next_state.current_activation is None
    assert next_state.activated_british_unit_ids == frozenset()
    assert next_state.activated_german_unit_ids == frozenset()


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


def _german_phase_state(
    *,
    mission=None,
    seed: int = 0,
    turn: int = 1,
    british_positions: dict[str, HexCoord] | None = None,
    british_cover: dict[str, int] | None = None,
    british_morales: dict[str, BritishMorale] | None = None,
    german_units: dict[str, RevealedGermanUnitState],
    activated_british_unit_ids: frozenset[str] | None = None,
    activated_german_unit_ids: frozenset[str] | None = None,
):
    if mission is None:
        mission = load_mission(MISSION_PATH)

    base_state = create_initial_game_state(mission, seed=seed)
    positions = {} if british_positions is None else british_positions
    cover_by_unit = {} if british_cover is None else british_cover
    morales = {} if british_morales is None else british_morales
    british_units = {
        unit_id: replace(
            unit_state,
            position=positions.get(unit_id, unit_state.position),
            cover=cover_by_unit.get(unit_id, unit_state.cover),
            morale=morales.get(unit_id, unit_state.morale),
        )
        for unit_id, unit_state in base_state.british_units.items()
    }
    unresolved_markers = {
        marker_id: marker_state
        for marker_id, marker_state in base_state.unresolved_markers.items()
        if marker_id not in german_units
    }

    return replace(
        base_state,
        turn=turn,
        phase=GamePhase.GERMAN,
        british_units=british_units,
        german_units=german_units,
        unresolved_markers=unresolved_markers,
        activated_british_unit_ids=(
            frozenset() if activated_british_unit_ids is None else activated_british_unit_ids
        ),
        activated_german_unit_ids=(
            frozenset() if activated_german_unit_ids is None else activated_german_unit_ids
        ),
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

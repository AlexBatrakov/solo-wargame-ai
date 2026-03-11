from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from solo_wargame_ai.domain.actions import (
    ChooseOrderExecutionAction,
    DoubleChoiceOption,
    OrderExecutionChoice,
    RallyAction,
    ResolveDoubleChoiceAction,
    SelectActivationDieAction,
    SelectBritishUnitAction,
    SelectGermanUnitAction,
)
from solo_wargame_ai.domain.decision_context import ChooseGermanUnitContext, DecisionContextKind
from solo_wargame_ai.domain.enums import HexDirection
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.resolver import (
    IllegalActionError,
    apply_action,
    get_legal_actions,
    resolve_automatic_progression,
)
from solo_wargame_ai.domain.state import GamePhase, TerminalOutcome, create_initial_game_state
from solo_wargame_ai.domain.units import (
    BritishMorale,
    GermanUnitStatus,
    RevealedGermanUnitState,
)
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def test_resolver_rejects_actions_that_are_illegal_for_the_current_pending_decision() -> None:
    state = _load_initial_state()

    with pytest.raises(IllegalActionError, match="choose_british_unit"):
        apply_action(state, SelectGermanUnitAction(unit_id="qm_1"))


def test_resolver_get_legal_actions_auto_rolls_over_nonterminal_german_end() -> None:
    state = _german_phase_state(seed=1, german_units={})

    assert get_legal_actions(state) == (
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
    )


def test_resolver_get_legal_actions_auto_advances_past_empty_british_phase() -> None:
    base_state = _load_initial_state(seed=0)
    state = replace(
        base_state,
        turn=4,
        british_units={
            unit_id: replace(unit_state, morale=BritishMorale.REMOVED)
            for unit_id, unit_state in base_state.british_units.items()
        },
        german_units={
            "qm_1": _german_unit("qm_1", HexCoord(0, 1)),
        },
        unresolved_markers={},
    )

    legal_actions = get_legal_actions(state)

    assert legal_actions == (SelectGermanUnitAction(unit_id="qm_1"),)


def test_resolver_apply_action_auto_rolls_over_before_applying_british_selection() -> None:
    state = _german_phase_state(seed=1, german_units={})

    next_state = apply_action(state, SelectBritishUnitAction(unit_id="rifle_squad_a"))

    assert next_state.turn == 2
    assert next_state.phase is GamePhase.BRITISH
    assert next_state.pending_decision.kind is DecisionContextKind.CHOOSE_ACTIVATION_DIE
    assert next_state.current_activation is not None
    assert next_state.current_activation.active_unit_id == "rifle_squad_a"
    assert next_state.current_activation.roll == (2, 5)
    assert next_state.current_activation.selected_die is None
    assert next_state.activated_british_unit_ids == frozenset()
    assert next_state.activated_german_unit_ids == frozenset()


def test_resolver_normalizes_terminal_like_states_to_no_actions_and_rejects_application() -> None:
    state = _german_phase_state(
        german_units={
            "qm_1": _german_unit(
                "qm_1",
                HexCoord(0, 1),
                status=GermanUnitStatus.REMOVED,
            ),
        },
        activated_german_unit_ids=frozenset(),
    )

    terminal_state = resolve_automatic_progression(state)

    assert terminal_state.terminal_outcome is TerminalOutcome.VICTORY
    assert terminal_state.phase is GamePhase.GERMAN
    assert terminal_state.pending_decision.kind is DecisionContextKind.CHOOSE_GERMAN_UNIT
    assert terminal_state.current_activation is None
    assert get_legal_actions(state) == ()

    with pytest.raises(IllegalActionError, match="terminal mission state"):
        apply_action(state, SelectBritishUnitAction(unit_id="rifle_squad_a"))

    with pytest.raises(IllegalActionError, match="terminal mission state"):
        apply_action(terminal_state, SelectBritishUnitAction(unit_id="rifle_squad_a"))


def test_resolver_finishes_activation_when_a_follow_up_order_has_no_legal_actions() -> None:
    state = _load_initial_state(seed=0)
    trace = (
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
        ResolveDoubleChoiceAction(choice=DoubleChoiceOption.REROLL),
        SelectActivationDieAction(die_value=1),
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.BOTH_ORDERS),
        RallyAction(),
    )

    for action in trace:
        state = apply_action(state, action)

    assert state.phase is GamePhase.BRITISH
    assert state.pending_decision.kind is DecisionContextKind.CHOOSE_BRITISH_UNIT
    assert state.current_activation is None
    assert state.activated_british_unit_ids == frozenset({"rifle_squad_b"})
    assert get_legal_actions(state) == (SelectBritishUnitAction(unit_id="rifle_squad_a"),)


def _load_initial_state(*, seed: int = 0):
    mission = load_mission(MISSION_PATH)
    return create_initial_game_state(mission, seed=seed)


def _german_phase_state(
    *,
    seed: int = 0,
    turn: int = 1,
    german_units: dict[str, RevealedGermanUnitState],
    activated_german_unit_ids: frozenset[str] | None = None,
):
    base_state = _load_initial_state(seed=seed)
    unresolved_markers = {
        marker_id: marker_state
        for marker_id, marker_state in base_state.unresolved_markers.items()
        if marker_id not in german_units
    }

    return replace(
        base_state,
        turn=turn,
        phase=GamePhase.GERMAN,
        german_units=german_units,
        unresolved_markers=unresolved_markers,
        activated_british_unit_ids=frozenset(base_state.british_units),
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

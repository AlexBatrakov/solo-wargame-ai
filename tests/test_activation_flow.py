from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from solo_wargame_ai.domain.actions import (
    ChooseOrderExecutionAction,
    DiscardActivationRollAction,
    DoubleChoiceOption,
    OrderExecutionChoice,
    ResolveDoubleChoiceAction,
    SelectActivationDieAction,
    SelectBritishUnitAction,
)
from solo_wargame_ai.domain.decision_context import DecisionContextKind
from solo_wargame_ai.domain.legal_actions import apply_action, get_legal_actions
from solo_wargame_ai.domain.state import GamePhase, create_initial_game_state
from solo_wargame_ai.domain.units import BritishMorale
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def test_choose_british_unit_lists_only_existing_non_removed_unactivated_units() -> None:
    state = _load_initial_state()

    assert get_legal_actions(state) == (
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
    )

    removed_unit = replace(
        state.british_units["rifle_squad_a"],
        morale=BritishMorale.REMOVED,
    )
    filtered_state = replace(
        state,
        british_units={**state.british_units, "rifle_squad_a": removed_unit},
        activated_british_unit_ids=frozenset({"rifle_squad_b"}),
    )

    assert get_legal_actions(filtered_state) == ()


def test_select_british_unit_rolls_activation_and_enters_double_choice_on_double() -> None:
    state = _load_initial_state(seed=0)
    initial_rng_state = state.rng_state

    next_state = apply_action(
        state,
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
    )

    assert next_state.pending_decision.kind is DecisionContextKind.CHOOSE_DOUBLE_CHOICE
    assert next_state.current_activation is not None
    assert next_state.current_activation.active_unit_id == "rifle_squad_a"
    assert next_state.current_activation.roll == (4, 4)
    assert next_state.current_activation.selected_die is None
    assert next_state.rng_state != initial_rng_state


def test_keep_double_advances_to_die_selection_without_rerolling() -> None:
    state = _state_after_selecting_first_british_unit(seed=0)
    pre_keep_rng_state = state.rng_state

    next_state = apply_action(
        state,
        ResolveDoubleChoiceAction(choice=DoubleChoiceOption.KEEP),
    )

    assert next_state.pending_decision.kind is DecisionContextKind.CHOOSE_ACTIVATION_DIE
    assert next_state.current_activation is not None
    assert next_state.current_activation.roll == (4, 4)
    assert next_state.rng_state == pre_keep_rng_state


def test_rerolling_a_double_updates_rng_and_reaches_die_selection_on_non_double() -> None:
    state = _state_after_selecting_first_british_unit(seed=0)
    pre_reroll_rng_state = state.rng_state

    next_state = apply_action(
        state,
        ResolveDoubleChoiceAction(choice=DoubleChoiceOption.REROLL),
    )

    assert next_state.pending_decision.kind is DecisionContextKind.CHOOSE_ACTIVATION_DIE
    assert next_state.current_activation is not None
    assert next_state.current_activation.roll == (1, 3)
    assert next_state.current_activation.selected_die is None
    assert next_state.rng_state != pre_reroll_rng_state


def test_non_double_path_reaches_order_execution_after_die_selection() -> None:
    state = _state_after_selecting_first_british_unit(seed=1)

    assert state.pending_decision.kind is DecisionContextKind.CHOOSE_ACTIVATION_DIE
    assert get_legal_actions(state) == (
        SelectActivationDieAction(die_value=2),
        SelectActivationDieAction(die_value=5),
        DiscardActivationRollAction(),
    )

    next_state = apply_action(
        state,
        SelectActivationDieAction(die_value=2),
    )

    assert next_state.pending_decision.kind is DecisionContextKind.CHOOSE_ORDER_EXECUTION
    assert next_state.current_activation is not None
    assert next_state.current_activation.roll == (2, 5)
    assert next_state.current_activation.selected_die == 2
    assert get_legal_actions(next_state) == (
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.FIRST_ORDER_ONLY),
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.SECOND_ORDER_ONLY),
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.BOTH_ORDERS),
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.NO_ACTION),
    )


def test_discarding_activation_roll_ends_activation_without_orders() -> None:
    state = _state_after_selecting_first_british_unit(seed=1)

    next_state = apply_action(state, DiscardActivationRollAction())

    assert next_state.phase is GamePhase.BRITISH
    assert next_state.pending_decision.kind is DecisionContextKind.CHOOSE_BRITISH_UNIT
    assert next_state.current_activation is None
    assert next_state.activated_british_unit_ids == frozenset({"rifle_squad_a"})
    assert get_legal_actions(next_state) == (
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
    )


def test_finishing_last_british_activation_transitions_to_german_phase() -> None:
    state = _state_after_selecting_first_british_unit(seed=1)
    state = apply_action(state, DiscardActivationRollAction())
    state = apply_action(
        state,
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
    )

    next_state = apply_action(state, DiscardActivationRollAction())

    assert next_state.phase is GamePhase.GERMAN
    assert next_state.pending_decision.kind is DecisionContextKind.CHOOSE_GERMAN_UNIT
    assert next_state.current_activation is None
    assert next_state.activated_british_unit_ids == frozenset(
        {"rifle_squad_a", "rifle_squad_b"},
    )
    assert get_legal_actions(next_state) == ()


def _load_initial_state(*, seed: int = 0):
    mission = load_mission(MISSION_PATH)
    return create_initial_game_state(mission, seed=seed)


def _state_after_selecting_first_british_unit(*, seed: int):
    state = _load_initial_state(seed=seed)
    return apply_action(
        state,
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
    )

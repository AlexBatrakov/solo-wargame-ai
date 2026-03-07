from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from solo_wargame_ai.domain.decision_context import (
    ChooseActivationDieContext,
    ChooseOrderParameterContext,
    DecisionContextKind,
    context_requires_current_activation,
)
from solo_wargame_ai.domain.mission import OrderName
from solo_wargame_ai.domain.state import (
    CurrentActivation,
    create_initial_game_state,
    validate_game_state,
)
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def test_stage_3b_declares_the_required_decision_context_kinds() -> None:
    assert set(DecisionContextKind) == {
        DecisionContextKind.CHOOSE_BRITISH_UNIT,
        DecisionContextKind.CHOOSE_DOUBLE_CHOICE,
        DecisionContextKind.CHOOSE_ACTIVATION_DIE,
        DecisionContextKind.CHOOSE_ORDER_EXECUTION,
        DecisionContextKind.CHOOSE_ORDER_PARAMETER,
        DecisionContextKind.CHOOSE_GERMAN_UNIT,
    }


def test_context_requires_current_activation_only_for_staged_british_substeps() -> None:
    assert not context_requires_current_activation(DecisionContextKind.CHOOSE_BRITISH_UNIT)
    assert context_requires_current_activation(DecisionContextKind.CHOOSE_DOUBLE_CHOICE)
    assert context_requires_current_activation(DecisionContextKind.CHOOSE_ACTIVATION_DIE)
    assert context_requires_current_activation(DecisionContextKind.CHOOSE_ORDER_EXECUTION)
    assert context_requires_current_activation(DecisionContextKind.CHOOSE_ORDER_PARAMETER)
    assert not context_requires_current_activation(DecisionContextKind.CHOOSE_GERMAN_UNIT)


def test_choose_activation_die_context_accepts_roll_payload_without_planned_orders() -> None:
    state = _load_valid_state()

    validate_game_state(
        replace(
            state,
            pending_decision=ChooseActivationDieContext(),
            current_activation=CurrentActivation(
                active_unit_id="rifle_squad_a",
                roll=(3, 5),
                selected_die=None,
                planned_orders=(),
                next_order_index=0,
            ),
        ),
    )


def test_choose_order_parameter_context_accepts_matching_staged_order_payload() -> None:
    state = _load_valid_state()

    validate_game_state(
        replace(
            state,
            pending_decision=ChooseOrderParameterContext(
                order=OrderName.FIRE,
                order_index=1,
            ),
            current_activation=CurrentActivation(
                active_unit_id="rifle_squad_a",
                roll=(6, 4),
                selected_die=6,
                planned_orders=(OrderName.ADVANCE, OrderName.FIRE),
                next_order_index=1,
            ),
        ),
    )


def _load_valid_state():
    mission = load_mission(MISSION_PATH)
    return create_initial_game_state(mission)

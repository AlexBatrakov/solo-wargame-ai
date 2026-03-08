from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from solo_wargame_ai.domain.actions import AdvanceAction, RallyAction, TakeCoverAction
from solo_wargame_ai.domain.decision_context import ChooseOrderParameterContext
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.legal_actions import apply_action, get_legal_actions
from solo_wargame_ai.domain.mission import OrderName
from solo_wargame_ai.domain.state import CurrentActivation, create_initial_game_state
from solo_wargame_ai.domain.units import BritishMorale
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def test_take_cover_increments_cover_by_one() -> None:
    state = _stage_order_state(planned_orders=(OrderName.TAKE_COVER,))

    next_state = apply_action(state, TakeCoverAction())

    assert next_state.british_units["rifle_squad_a"].cover == 1
    assert next_state.current_activation is None
    assert next_state.activated_british_unit_ids == frozenset({"rifle_squad_a"})


def test_repeated_take_cover_stacks_cover() -> None:
    state = _stage_order_state(
        planned_orders=(OrderName.TAKE_COVER, OrderName.TAKE_COVER),
    )

    state = apply_action(state, TakeCoverAction())

    assert isinstance(state.pending_decision, ChooseOrderParameterContext)
    assert state.pending_decision.order is OrderName.TAKE_COVER
    assert state.british_units["rifle_squad_a"].cover == 1

    state = apply_action(state, TakeCoverAction())

    assert state.british_units["rifle_squad_a"].cover == 2
    assert state.current_activation is None


def test_rally_changes_low_morale_to_normal() -> None:
    state = _stage_order_state(
        planned_orders=(OrderName.RALLY,),
        active_morale=BritishMorale.LOW,
    )

    next_state = apply_action(state, RallyAction())

    assert next_state.british_units["rifle_squad_a"].morale is BritishMorale.NORMAL
    assert next_state.current_activation is None
    assert next_state.activated_british_unit_ids == frozenset({"rifle_squad_a"})


def test_rally_on_normal_unit_finishes_if_follow_up_is_impossible() -> None:
    state = _stage_order_state(
        planned_orders=(OrderName.RALLY, OrderName.GRENADE_ATTACK),
    )

    assert get_legal_actions(state) == (RallyAction(),)

    next_state = apply_action(state, RallyAction())

    assert next_state.british_units["rifle_squad_a"].morale is BritishMorale.NORMAL
    assert next_state.current_activation is None
    assert next_state.activated_british_unit_ids == frozenset({"rifle_squad_a"})


def test_advancing_after_taking_cover_clears_accumulated_cover() -> None:
    state = _stage_order_state(
        planned_orders=(OrderName.TAKE_COVER, OrderName.ADVANCE),
    )

    state = apply_action(state, TakeCoverAction())

    assert state.british_units["rifle_squad_a"].cover == 1
    assert isinstance(state.pending_decision, ChooseOrderParameterContext)
    assert state.pending_decision.order is OrderName.ADVANCE

    state = apply_action(state, AdvanceAction(destination=HexCoord(1, 2)))

    assert state.british_units["rifle_squad_a"].position == HexCoord(1, 2)
    assert state.british_units["rifle_squad_a"].cover == 0
    assert state.current_activation is None


def _stage_order_state(
    *,
    seed: int = 0,
    planned_orders: tuple[OrderName, ...],
    active_morale: BritishMorale = BritishMorale.NORMAL,
):
    mission = load_mission(MISSION_PATH)
    base_state = create_initial_game_state(mission, seed=seed)
    british_units = dict(base_state.british_units)
    british_units["rifle_squad_a"] = replace(
        british_units["rifle_squad_a"],
        morale=active_morale,
    )

    return replace(
        base_state,
        british_units=british_units,
        pending_decision=ChooseOrderParameterContext(
            order=planned_orders[0],
            order_index=0,
        ),
        current_activation=CurrentActivation(
            active_unit_id="rifle_squad_a",
            roll=(6, 1),
            selected_die=6,
            planned_orders=planned_orders,
            next_order_index=0,
        ),
    )

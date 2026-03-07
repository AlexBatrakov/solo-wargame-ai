from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from solo_wargame_ai.domain.actions import AdvanceAction
from solo_wargame_ai.domain.decision_context import ChooseOrderParameterContext, DecisionContextKind
from solo_wargame_ai.domain.enums import HexDirection
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.legal_actions import apply_action, get_legal_actions
from solo_wargame_ai.domain.mission import OrderName
from solo_wargame_ai.domain.state import CurrentActivation, GamePhase, create_initial_game_state
from solo_wargame_ai.domain.units import GermanUnitStatus, RevealedGermanUnitState
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def test_advance_destinations_use_only_forward_playable_neighbors() -> None:
    state = _stage_advance_state()

    assert get_legal_actions(state) == (
        AdvanceAction(destination=HexCoord(-1, 3)),
        AdvanceAction(destination=HexCoord(0, 2)),
        AdvanceAction(destination=HexCoord(1, 2)),
    )


def test_advance_allows_british_stacking_but_blocks_revealed_german_destination() -> None:
    german_unit = RevealedGermanUnitState(
        unit_id="qm_1",
        unit_class="heavy_machine_gun",
        position=HexCoord(0, 1),
        facing=HexDirection.DOWN,
        status=GermanUnitStatus.ACTIVE,
    )
    state = _stage_advance_state(
        active_position=HexCoord(0, 2),
        rifle_b_position=HexCoord(-1, 2),
        german_units={"qm_1": german_unit},
        unresolved_markers={},
    )

    assert get_legal_actions(state) == (
        AdvanceAction(destination=HexCoord(-1, 2)),
        AdvanceAction(destination=HexCoord(1, 1)),
    )


def test_advance_moves_unit_resets_cover_and_stages_next_planned_order() -> None:
    state = _stage_advance_state(
        active_cover=2,
        planned_orders=(OrderName.ADVANCE, OrderName.FIRE),
    )

    next_state = apply_action(state, AdvanceAction(destination=HexCoord(0, 2)))

    assert next_state.british_units["rifle_squad_a"].position == HexCoord(0, 2)
    assert next_state.british_units["rifle_squad_a"].cover == 0
    assert isinstance(next_state.pending_decision, ChooseOrderParameterContext)
    assert next_state.pending_decision.order is OrderName.FIRE
    assert next_state.pending_decision.order_index == 1
    assert next_state.current_activation is not None
    assert next_state.current_activation.next_order_index == 1


def test_advance_with_no_remaining_orders_ends_activation_through_stage4_flow() -> None:
    state = _stage_advance_state(planned_orders=(OrderName.ADVANCE,))

    next_state = apply_action(state, AdvanceAction(destination=HexCoord(1, 2)))

    assert next_state.phase is GamePhase.BRITISH
    assert next_state.pending_decision.kind is DecisionContextKind.CHOOSE_BRITISH_UNIT
    assert next_state.current_activation is None
    assert next_state.activated_british_unit_ids == frozenset({"rifle_squad_a"})


def _stage_advance_state(
    *,
    seed: int = 0,
    active_position: HexCoord = HexCoord(0, 3),
    active_cover: int = 0,
    rifle_b_position: HexCoord | None = None,
    planned_orders: tuple[OrderName, ...] = (OrderName.ADVANCE,),
    german_units=None,
    unresolved_markers=None,
):
    mission = load_mission(MISSION_PATH)
    base_state = create_initial_game_state(mission, seed=seed)

    british_units = dict(base_state.british_units)
    british_units["rifle_squad_a"] = replace(
        british_units["rifle_squad_a"],
        position=active_position,
        cover=active_cover,
    )
    if rifle_b_position is not None:
        british_units["rifle_squad_b"] = replace(
            british_units["rifle_squad_b"],
            position=rifle_b_position,
        )

    return replace(
        base_state,
        british_units=british_units,
        german_units=base_state.german_units if german_units is None else german_units,
        unresolved_markers=(
            base_state.unresolved_markers if unresolved_markers is None else unresolved_markers
        ),
        pending_decision=ChooseOrderParameterContext(
            order=OrderName.ADVANCE,
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

from __future__ import annotations

from pathlib import Path

from solo_wargame_ai.domain.actions import (
    AdvanceAction,
    ChooseOrderExecutionAction,
    DiscardActivationRollAction,
    DoubleChoiceOption,
    OrderExecutionChoice,
    ResolveDoubleChoiceAction,
    SelectActivationDieAction,
    SelectBritishUnitAction,
    SelectGermanUnitAction,
    TakeCoverAction,
)
from solo_wargame_ai.domain.decision_context import DecisionContextKind
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.resolver import apply_action, get_legal_actions
from solo_wargame_ai.domain.state import GamePhase, create_initial_game_state
from solo_wargame_ai.domain.units import BritishMorale, GermanUnitStatus
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_03_PATH = (
    Path(__file__).resolve().parents[2]
    / "configs"
    / "missions"
    / "mission_03_secure_the_building.toml"
)


def test_fixed_seed_mission_3_trace_reveals_all_markers_and_rolls_over_after_german_phase() -> None:
    mission = load_mission(MISSION_03_PATH)
    state = create_initial_game_state(mission, seed=0)

    for action in _mission_3_reveal_trace_actions():
        assert action in get_legal_actions(state)
        state = apply_action(state, action)

    assert state.turn == 3
    assert state.phase is GamePhase.BRITISH
    assert state.pending_decision.kind is DecisionContextKind.CHOOSE_BRITISH_UNIT
    assert state.terminal_outcome is None
    assert state.unresolved_markers == {}
    assert state.activated_british_unit_ids == frozenset()
    assert state.activated_german_unit_ids == frozenset()
    assert state.british_units["rifle_squad_c"].position == HexCoord(0, 2)
    assert state.british_units["rifle_squad_c"].morale is BritishMorale.REMOVED
    assert state.german_units["qm_1"].unit_class == "german_rifle_squad"
    assert state.german_units["qm_1"].status is GermanUnitStatus.ACTIVE
    assert state.german_units["qm_2"].unit_class == "heavy_machine_gun"
    assert state.german_units["qm_2"].status is GermanUnitStatus.ACTIVE
    assert state.german_units["qm_3"].unit_class == "german_rifle_squad"
    assert state.german_units["qm_3"].status is GermanUnitStatus.ACTIVE
    assert get_legal_actions(state) == (
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
    )


def _mission_3_reveal_trace_actions() -> tuple[object, ...]:
    return (
        SelectBritishUnitAction(unit_id="rifle_squad_c"),
        ResolveDoubleChoiceAction(choice=DoubleChoiceOption.REROLL),
        SelectActivationDieAction(die_value=3),
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.BOTH_ORDERS),
        AdvanceAction(destination=HexCoord(0, 3)),
        TakeCoverAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_c"),
        SelectActivationDieAction(die_value=3),
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.BOTH_ORDERS),
        AdvanceAction(destination=HexCoord(0, 2)),
        TakeCoverAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
        DiscardActivationRollAction(),
        SelectGermanUnitAction(unit_id="qm_1"),
        SelectGermanUnitAction(unit_id="qm_2"),
        SelectGermanUnitAction(unit_id="qm_3"),
    )

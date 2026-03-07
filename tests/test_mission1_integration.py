from __future__ import annotations

from pathlib import Path

from solo_wargame_ai.domain.actions import (
    AdvanceAction,
    ChooseOrderExecutionAction,
    DiscardActivationRollAction,
    DoubleChoiceOption,
    FireAction,
    OrderExecutionChoice,
    ResolveDoubleChoiceAction,
    SelectActivationDieAction,
    SelectBritishUnitAction,
    SelectGermanUnitAction,
)
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.resolver import apply_action, get_legal_actions
from solo_wargame_ai.domain.state import TerminalOutcome, create_initial_game_state
from solo_wargame_ai.domain.units import GermanUnitStatus
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def test_fixed_seed_mission_1_trace_reaches_terminal_victory_using_only_legal_actions() -> None:
    mission = load_mission(MISSION_PATH)
    state = create_initial_game_state(mission, seed=0)

    trace = (
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
        ResolveDoubleChoiceAction(choice=DoubleChoiceOption.KEEP),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
        SelectActivationDieAction(die_value=2),
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.FIRST_ORDER_ONLY),
        AdvanceAction(destination=HexCoord(0, 2)),
        SelectGermanUnitAction(unit_id="qm_1"),
        SelectBritishUnitAction(unit_id="rifle_squad_a"),
        DiscardActivationRollAction(),
        SelectBritishUnitAction(unit_id="rifle_squad_b"),
        SelectActivationDieAction(die_value=5),
        ChooseOrderExecutionAction(choice=OrderExecutionChoice.BOTH_ORDERS),
        FireAction(target_unit_id="qm_1"),
    )

    for action in trace:
        assert action in get_legal_actions(state)
        state = apply_action(state, action)

    assert state.terminal_outcome is TerminalOutcome.VICTORY
    assert state.turn == 4
    assert state.unresolved_markers == {}
    assert state.german_units["qm_1"].status is GermanUnitStatus.REMOVED
    assert get_legal_actions(state) == ()

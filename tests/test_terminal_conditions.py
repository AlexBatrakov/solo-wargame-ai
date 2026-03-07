from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from solo_wargame_ai.domain.decision_context import ChooseGermanUnitContext, DecisionContextKind
from solo_wargame_ai.domain.enums import HexDirection
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.mission import HiddenMarker
from solo_wargame_ai.domain.resolver import evaluate_terminal_outcome, resolve_automatic_progression
from solo_wargame_ai.domain.state import GamePhase, TerminalOutcome, create_initial_game_state
from solo_wargame_ai.domain.units import GermanUnitStatus, RevealedGermanUnitState
from solo_wargame_ai.io.mission_loader import load_mission

MISSION_PATH = (
    Path(__file__).resolve().parents[1]
    / "configs"
    / "missions"
    / "mission_01_secure_the_woods_1.toml"
)


def test_victory_is_detected_when_all_markers_are_resolved_and_no_active_germans_remain() -> None:
    state = _german_phase_state(
        german_units={
            "qm_1": _german_unit("qm_1", HexCoord(0, 1), status=GermanUnitStatus.REMOVED),
        },
    )

    next_state = resolve_automatic_progression(state)

    assert evaluate_terminal_outcome(state) is TerminalOutcome.VICTORY
    assert next_state.terminal_outcome is TerminalOutcome.VICTORY


def test_no_false_victory_while_unresolved_marker_remains() -> None:
    state = _german_phase_state(german_units={})

    assert evaluate_terminal_outcome(state) is None
    assert resolve_automatic_progression(state).terminal_outcome is None


def test_no_false_victory_while_active_german_unit_remains() -> None:
    state = _german_phase_state(
        mission=_mission_with_hidden_markers(),
        german_units={"qm_1": _german_unit("qm_1", HexCoord(0, 1))},
    )

    assert evaluate_terminal_outcome(state) is None
    assert resolve_automatic_progression(state).terminal_outcome is None


def test_defeat_is_detected_only_after_final_turn_is_completed_without_victory() -> None:
    mission = load_mission(MISSION_PATH)
    state = _german_phase_state(
        mission=mission,
        turn=mission.turns.turn_limit,
        german_units={},
        activated_german_unit_ids=frozenset(),
    )

    next_state = resolve_automatic_progression(state)

    assert evaluate_terminal_outcome(state) is TerminalOutcome.DEFEAT
    assert next_state.terminal_outcome is TerminalOutcome.DEFEAT
    assert next_state.turn == mission.turns.turn_limit


def test_no_premature_defeat_before_final_turn_is_completed() -> None:
    mission = load_mission(MISSION_PATH)
    state = _german_phase_state(
        mission=mission,
        turn=mission.turns.turn_limit - 1,
        german_units={},
        activated_german_unit_ids=frozenset(),
    )

    next_state = resolve_automatic_progression(state)

    assert evaluate_terminal_outcome(state) is None
    assert next_state.terminal_outcome is None
    assert next_state.turn == mission.turns.turn_limit
    assert next_state.phase is GamePhase.BRITISH


def test_british_phase_victory_is_normalized_to_terminal_state_and_is_idempotent() -> None:
    mission = load_mission(MISSION_PATH)
    base_state = create_initial_game_state(mission, seed=0)
    state = replace(
        base_state,
        german_units={
            "qm_1": _german_unit(
                "qm_1",
                HexCoord(0, 1),
                status=GermanUnitStatus.REMOVED,
            ),
        },
        unresolved_markers={},
    )

    next_state = resolve_automatic_progression(state)

    assert next_state.phase is GamePhase.BRITISH
    assert next_state.pending_decision.kind is DecisionContextKind.CHOOSE_BRITISH_UNIT
    assert next_state.current_activation is None
    assert next_state.terminal_outcome is TerminalOutcome.VICTORY
    assert resolve_automatic_progression(next_state) == next_state


def test_nonterminal_rollover_normalization_is_idempotent() -> None:
    state = _german_phase_state(german_units={})

    next_state = resolve_automatic_progression(state)

    assert next_state.phase is GamePhase.BRITISH
    assert next_state.pending_decision.kind is DecisionContextKind.CHOOSE_BRITISH_UNIT
    assert next_state.current_activation is None
    assert resolve_automatic_progression(next_state) == next_state


def _mission_with_hidden_markers():
    mission = load_mission(MISSION_PATH)
    return replace(
        mission,
        map=replace(
            mission.map,
            hidden_markers=(HiddenMarker(marker_id="qm_1", coord=HexCoord(0, 1)),),
        ),
    )


def _german_phase_state(
    *,
    mission=None,
    turn: int = 1,
    german_units: dict[str, RevealedGermanUnitState],
    activated_german_unit_ids: frozenset[str] | None = None,
):
    if mission is None:
        mission = load_mission(MISSION_PATH)

    base_state = create_initial_game_state(mission, seed=0)
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
        pending_decision=ChooseGermanUnitContext(),
        activated_german_unit_ids=(
            frozenset() if activated_german_unit_ids is None else activated_german_unit_ids
        ),
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

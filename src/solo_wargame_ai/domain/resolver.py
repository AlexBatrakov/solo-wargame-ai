"""Thin public resolver path for Stage 6B automatic Mission 1 progression."""

from __future__ import annotations

from dataclasses import replace

from .actions import GameAction
from .decision_context import ChooseBritishUnitContext, ChooseGermanUnitContext
from .german_fire import selectable_german_unit_ids
from .legal_actions import IllegalActionError
from .legal_actions import apply_action as apply_legal_action
from .legal_actions import get_legal_actions as get_staged_legal_actions
from .state import GamePhase, GameState, TerminalOutcome, validate_game_state
from .units import GermanUnitStatus


def get_legal_actions(state: GameState) -> tuple[GameAction, ...]:
    """Return legal player actions after resolving automatic Stage 6B flow."""

    progressed_state = resolve_automatic_progression(state)
    if progressed_state.terminal_outcome is not None:
        return ()
    return get_staged_legal_actions(progressed_state)


def apply_action(state: GameState, action: GameAction) -> GameState:
    """Apply one player action, then resolve terminal checks and automatic flow."""

    progressed_state = resolve_automatic_progression(state)
    if progressed_state.terminal_outcome is not None:
        raise IllegalActionError("Cannot apply actions to a terminal Mission 1 state")

    next_state = apply_legal_action(progressed_state, action)
    return resolve_automatic_progression(next_state)


def resolve_automatic_progression(state: GameState) -> GameState:
    """Advance through zero-decision German flow, terminal checks, and rollover."""

    validate_game_state(state)
    progressed_state = state

    while progressed_state.terminal_outcome is None:
        outcome = evaluate_terminal_outcome(progressed_state)
        if outcome is not None:
            progressed_state = _mark_terminal_outcome(progressed_state, outcome)
            break

        if _is_empty_british_phase(progressed_state):
            progressed_state = _advance_to_german_phase(progressed_state)
            continue

        if (
            progressed_state.phase is GamePhase.GERMAN
            and not selectable_german_unit_ids(progressed_state)
        ):
            progressed_state = _rollover_to_next_british_turn(progressed_state)
            continue

        break

    validate_game_state(progressed_state)
    return progressed_state


def evaluate_terminal_outcome(state: GameState) -> TerminalOutcome | None:
    """Evaluate Mission 1 terminal conditions against the current runtime truth."""

    if state.terminal_outcome is not None:
        return state.terminal_outcome

    victory = not state.unresolved_markers and not any(
        unit.status is GermanUnitStatus.ACTIVE for unit in state.german_units.values()
    )
    if victory:
        return TerminalOutcome.VICTORY

    if (
        state.phase is GamePhase.GERMAN
        and not selectable_german_unit_ids(state)
        and state.turn >= state.mission.turns.turn_limit
    ):
        return TerminalOutcome.DEFEAT

    return None


def _mark_terminal_outcome(
    state: GameState,
    outcome: TerminalOutcome,
) -> GameState:
    pending_decision = (
        ChooseGermanUnitContext()
        if state.phase is GamePhase.GERMAN
        else ChooseBritishUnitContext()
    )
    return replace(
        state,
        pending_decision=pending_decision,
        current_activation=None,
        terminal_outcome=outcome,
    )


def _is_empty_british_phase(state: GameState) -> bool:
    return (
        state.phase is GamePhase.BRITISH
        and isinstance(state.pending_decision, ChooseBritishUnitContext)
        and state.current_activation is None
        and not get_staged_legal_actions(state)
    )


def _advance_to_german_phase(state: GameState) -> GameState:
    return replace(
        state,
        phase=GamePhase.GERMAN,
        activated_german_unit_ids=frozenset(),
        pending_decision=ChooseGermanUnitContext(),
        current_activation=None,
    )


def _rollover_to_next_british_turn(state: GameState) -> GameState:
    return replace(
        state,
        turn=state.turn + 1,
        phase=GamePhase.BRITISH,
        activated_british_unit_ids=frozenset(),
        activated_german_unit_ids=frozenset(),
        pending_decision=ChooseBritishUnitContext(),
        current_activation=None,
    )


__all__ = [
    "IllegalActionError",
    "apply_action",
    "evaluate_terminal_outcome",
    "get_legal_actions",
    "resolve_automatic_progression",
]

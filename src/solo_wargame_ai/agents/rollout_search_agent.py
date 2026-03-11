"""Deterministic Mission 1 rollout-search baseline over the accepted agent seam."""

from __future__ import annotations

from dataclasses import dataclass

from solo_wargame_ai.domain.actions import GameAction
from solo_wargame_ai.domain.resolver import apply_action, get_legal_actions
from solo_wargame_ai.domain.state import GameState, TerminalOutcome
from solo_wargame_ai.domain.units import GermanUnitStatus

from .base import Agent
from .heuristic_agent import HeuristicAgent


@dataclass(frozen=True, slots=True)
class RolloutEvaluation:
    """Terminal rollout summary used to rank one candidate root action."""

    terminal_outcome: TerminalOutcome
    terminal_turn: int
    resolved_marker_count: int
    removed_german_count: int
    player_decision_count: int


class RolloutSearchAgent:
    """Evaluate each legal action with one deterministic heuristic rollout."""

    name = "rollout"

    def __init__(self, *, rollout_policy: Agent | None = None) -> None:
        self._rollout_policy = rollout_policy or HeuristicAgent()

    def select_action(
        self,
        state: GameState,
        legal_actions: tuple[GameAction, ...],
    ) -> GameAction:
        if not legal_actions:
            raise ValueError("RolloutSearchAgent requires at least one legal action")

        return min(
            legal_actions,
            key=lambda action: self._selection_sort_key(
                action,
                self._evaluate_action_rollout(state, action),
            ),
        )

    def _evaluate_action_rollout(
        self,
        state: GameState,
        action: GameAction,
    ) -> RolloutEvaluation:
        next_state = apply_action(state, action)
        player_decision_count = 1

        while next_state.terminal_outcome is None:
            legal_actions = get_legal_actions(next_state)
            if not legal_actions:
                raise RuntimeError(
                    "Resolver returned no legal actions before reaching a terminal outcome",
                )
            rollout_action = self._rollout_policy.select_action(next_state, legal_actions)
            if rollout_action not in legal_actions:
                raise ValueError(
                    "Rollout policy returned an illegal action: "
                    f"{rollout_action!r}",
                )
            next_state = apply_action(next_state, rollout_action)
            player_decision_count += 1

        return RolloutEvaluation(
            terminal_outcome=next_state.terminal_outcome,
            terminal_turn=next_state.turn,
            resolved_marker_count=(
                len(next_state.mission.map.hidden_markers)
                - len(next_state.unresolved_markers)
            ),
            removed_german_count=sum(
                1
                for german_unit in next_state.german_units.values()
                if german_unit.status is GermanUnitStatus.REMOVED
            ),
            player_decision_count=player_decision_count,
        )

    def _selection_sort_key(
        self,
        action: GameAction,
        evaluation: RolloutEvaluation,
    ) -> tuple[int, int, int, int, int, str]:
        return (
            -int(evaluation.terminal_outcome is TerminalOutcome.VICTORY),
            -evaluation.removed_german_count,
            -evaluation.resolved_marker_count,
            evaluation.terminal_turn,
            evaluation.player_decision_count,
            repr(action),
        )

__all__ = ["RolloutEvaluation", "RolloutSearchAgent"]

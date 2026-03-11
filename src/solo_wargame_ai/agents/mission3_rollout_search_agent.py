"""Mission 3-local bounded rollout/search baseline for the active packet."""

from __future__ import annotations

from dataclasses import dataclass

from solo_wargame_ai.domain.actions import GameAction
from solo_wargame_ai.domain.resolver import apply_action, get_legal_actions
from solo_wargame_ai.domain.state import GameState, TerminalOutcome
from solo_wargame_ai.domain.units import GermanUnitStatus

from .base import Agent
from .mission3_heuristic_agent import Mission3HeuristicAgent, evaluate_mission3_state


@dataclass(frozen=True, slots=True)
class Mission3SearchBudget:
    """Explicit fixed-budget policy for the Mission 3 rollout/search baseline."""

    root_width_policy: str = "full_legal_width"
    rollouts_per_action: int = 1
    rollout_policy: str = "mission3_heuristic(depth=0)"
    rollout_depth_limit: int = 16
    terminal_policy: str = "stop_at_terminal_else_score_frontier_state"


DEFAULT_MISSION3_SEARCH_BUDGET = Mission3SearchBudget()


@dataclass(frozen=True, slots=True)
class Mission3RolloutEvaluation:
    """Frontier summary used to rank one Mission 3 root action."""

    terminal_outcome: TerminalOutcome | None
    terminal_turn: int
    resolved_marker_count: int
    removed_german_count: int
    player_decision_count: int
    frontier_score: float
    truncated: bool


class Mission3RolloutSearchAgent:
    """Evaluate each legal root action with one bounded deterministic rollout."""

    name = "rollout-search"

    def __init__(
        self,
        *,
        rollout_policy: Agent | None = None,
        budget: Mission3SearchBudget = DEFAULT_MISSION3_SEARCH_BUDGET,
    ) -> None:
        self._rollout_policy = rollout_policy or Mission3HeuristicAgent(lookahead_depth=0)
        self._budget = budget

    @property
    def budget(self) -> Mission3SearchBudget:
        """Expose the fixed budget for report formatting."""

        return self._budget

    def select_action(
        self,
        state: GameState,
        legal_actions: tuple[GameAction, ...],
    ) -> GameAction:
        if not legal_actions:
            raise ValueError("Mission3RolloutSearchAgent requires at least one legal action")

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
    ) -> Mission3RolloutEvaluation:
        next_state = apply_action(state, action)
        player_decision_count = 1
        truncated = False

        while (
            next_state.terminal_outcome is None
            and player_decision_count < self._budget.rollout_depth_limit
        ):
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

        if next_state.terminal_outcome is None:
            truncated = True

        return Mission3RolloutEvaluation(
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
            frontier_score=evaluate_mission3_state(next_state),
            truncated=truncated,
        )

    def _selection_sort_key(
        self,
        action: GameAction,
        evaluation: Mission3RolloutEvaluation,
    ) -> tuple[int, float, int, int, int, int, str]:
        terminal_rank = 0
        if evaluation.terminal_outcome is TerminalOutcome.VICTORY:
            terminal_rank = 2
        elif evaluation.terminal_outcome is TerminalOutcome.DEFEAT:
            terminal_rank = -2

        return (
            -terminal_rank,
            -evaluation.frontier_score,
            -evaluation.removed_german_count,
            -evaluation.resolved_marker_count,
            evaluation.terminal_turn,
            evaluation.player_decision_count,
            repr(action),
        )


__all__ = [
    "DEFAULT_MISSION3_SEARCH_BUDGET",
    "Mission3RolloutEvaluation",
    "Mission3RolloutSearchAgent",
    "Mission3SearchBudget",
]

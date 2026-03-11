"""Fixed-seed episode runner over the accepted resolver facade.

This module keeps the accepted baseline harness on the stable integration seam:

- mission loading happens outside the runner
- episode initialization uses ``create_initial_game_state``
- each decision step uses ``resolver.get_legal_actions`` then ``resolver.apply_action``
- agents only choose from the supplied legal action tuple
- replay helpers remain optional debugging adapters, not required dependencies
- preserved Phase 3 seed aliases stay local historical Mission 1 operator
  surfaces; later mission-local seed aliases should live beside their own
  comparison code
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from solo_wargame_ai.agents.base import Agent, AgentFactory
from solo_wargame_ai.domain.mission import Mission
from solo_wargame_ai.domain.resolver import (
    apply_action,
    get_legal_actions,
    resolve_automatic_progression,
)
from solo_wargame_ai.domain.state import GameState, TerminalOutcome, create_initial_game_state
from solo_wargame_ai.domain.units import GermanUnitStatus

PHASE3_SMOKE_SEEDS: tuple[int, ...] = tuple(range(16))


@dataclass(frozen=True, slots=True)
class EpisodeResult:
    """Per-episode data recorded by the accepted fixed-seed runner."""

    agent_name: str
    seed: int | None
    terminal_outcome: TerminalOutcome
    terminal_turn: int
    resolved_marker_count: int
    removed_german_count: int
    player_decision_count: int


@dataclass(frozen=True, slots=True)
class EpisodeRun:
    """Full single-episode run output for tests and later aggregation."""

    final_state: GameState
    result: EpisodeResult


def run_episode(
    mission: Mission,
    agent: Agent,
    *,
    seed: int | None,
) -> EpisodeRun:
    """Run one fixed-seed episode until a terminal outcome is reached."""

    state = create_initial_game_state(mission, seed=seed)
    initial_marker_count = len(state.unresolved_markers)
    player_decision_count = 0

    while state.terminal_outcome is None:
        legal_actions = get_legal_actions(state)
        if not legal_actions:
            state = resolve_automatic_progression(state)
            if state.terminal_outcome is not None:
                break
            raise RuntimeError(
                "Resolver returned no legal actions before reaching a terminal outcome",
            )

        action = agent.select_action(state, legal_actions)
        if action not in legal_actions:
            raise ValueError(
                f"Agent {agent_name(agent)!r} returned an illegal action: {action!r}",
            )

        state = apply_action(state, action)
        player_decision_count += 1

    return EpisodeRun(
        final_state=state,
        result=EpisodeResult(
            agent_name=agent_name(agent),
            seed=seed,
            terminal_outcome=state.terminal_outcome,
            terminal_turn=state.turn,
            resolved_marker_count=initial_marker_count - len(state.unresolved_markers),
            removed_german_count=sum(
                1
                for german_unit in state.german_units.values()
                if german_unit.status is GermanUnitStatus.REMOVED
            ),
            player_decision_count=player_decision_count,
        ),
    )


def run_episodes(
    mission: Mission,
    *,
    agent_factory: AgentFactory,
    seeds: Sequence[int | None],
) -> tuple[EpisodeRun, ...]:
    """Run a fixed seed set with one fresh agent instance per episode."""

    return tuple(
        run_episode(mission, agent_factory(seed), seed=seed)
        for seed in seeds
    )


def run_smoke_episodes(
    mission: Mission,
    *,
    agent_factory: AgentFactory,
) -> tuple[EpisodeRun, ...]:
    """Run the preserved 16-seed Phase 3 smoke set."""

    return run_episodes(mission, agent_factory=agent_factory, seeds=PHASE3_SMOKE_SEEDS)


def agent_name(agent: Agent) -> str:
    """Return a stable display name for per-episode reporting."""

    return str(getattr(agent, "name", type(agent).__name__))


__all__ = [
    "EpisodeResult",
    "EpisodeRun",
    "PHASE3_SMOKE_SEEDS",
    "agent_name",
    "run_episode",
    "run_episodes",
    "run_smoke_episodes",
]

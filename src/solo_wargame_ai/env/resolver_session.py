"""Shared resolver-backed env session lifecycle below mission-local wrappers."""

from __future__ import annotations

from dataclasses import dataclass

from solo_wargame_ai.domain.actions import GameAction
from solo_wargame_ai.domain.mission import Mission
from solo_wargame_ai.domain.resolver import apply_action
from solo_wargame_ai.domain.state import (
    DEFAULT_INITIAL_RNG_SEED,
    create_initial_game_state,
)

from .normalized_state import NormalizedEnvState, normalize_env_state


@dataclass(frozen=True, slots=True)
class ResolverSessionSnapshot:
    """Current resolver-normalized session state plus episode bookkeeping."""

    normalized_state: NormalizedEnvState
    seed: int
    decision_step_count: int
    terminated: bool
    truncated: bool
    episode_closed: bool
    truncation_reason: str | None = None


class ResolverEnvSession:
    """Own reset/step lifecycle for one resolver-backed env episode."""

    def __init__(
        self,
        mission: Mission,
        *,
        default_seed: int = DEFAULT_INITIAL_RNG_SEED,
        max_steps: int | None = None,
    ) -> None:
        if max_steps is not None and max_steps < 1:
            raise ValueError("max_steps must be positive when provided")

        self._mission = mission
        self._default_seed = default_seed
        self._max_steps = max_steps
        self._snapshot: ResolverSessionSnapshot | None = None

    @property
    def snapshot(self) -> ResolverSessionSnapshot:
        """Return the current session snapshot after reset or step."""

        if self._snapshot is None:
            raise RuntimeError("ResolverEnvSession has no active state; call reset() first")
        return self._snapshot

    def reset(self, *, seed: int | None = None) -> ResolverSessionSnapshot:
        """Reset to a deterministic resolver-normalized initial decision state."""

        chosen_seed = self._default_seed if seed is None else seed
        normalized_state = normalize_env_state(
            create_initial_game_state(self._mission, seed=chosen_seed),
        )
        self._snapshot = ResolverSessionSnapshot(
            normalized_state=normalized_state,
            seed=chosen_seed,
            decision_step_count=0,
            terminated=normalized_state.state.terminal_outcome is not None,
            truncated=False,
            episode_closed=normalized_state.state.terminal_outcome is not None,
        )
        return self._snapshot

    def step(self, action: GameAction) -> ResolverSessionSnapshot:
        """Apply one raw legal domain action and advance episode bookkeeping."""

        snapshot = self._snapshot
        if snapshot is None:
            raise RuntimeError("ResolverEnvSession.reset() must be called before step()")
        if snapshot.episode_closed:
            raise RuntimeError("ResolverEnvSession episode is closed; call reset() before step()")

        normalized_state = normalize_env_state(
            apply_action(snapshot.normalized_state.state, action),
        )
        decision_step_count = snapshot.decision_step_count + 1
        terminated = normalized_state.state.terminal_outcome is not None
        truncated = not terminated and self._has_reached_step_limit(decision_step_count)

        self._snapshot = ResolverSessionSnapshot(
            normalized_state=normalized_state,
            seed=snapshot.seed,
            decision_step_count=decision_step_count,
            terminated=terminated,
            truncated=truncated,
            episode_closed=terminated or truncated,
            truncation_reason="step_limit" if truncated else None,
        )
        return self._snapshot

    def _has_reached_step_limit(self, decision_step_count: int) -> bool:
        return self._max_steps is not None and decision_step_count >= self._max_steps


__all__ = ["ResolverEnvSession", "ResolverSessionSnapshot"]

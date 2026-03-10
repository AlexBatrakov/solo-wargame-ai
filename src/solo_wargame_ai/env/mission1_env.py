"""Thin Mission 1 RL wrapper over the accepted resolver facade."""

from __future__ import annotations

from typing import TypeAlias

from solo_wargame_ai.domain.mission import Mission
from solo_wargame_ai.domain.resolver import apply_action
from solo_wargame_ai.domain.state import (
    DEFAULT_INITIAL_RNG_SEED,
    TerminalOutcome,
    create_initial_game_state,
)

from .action_catalog import MISSION_1_ID, MissionActionCatalog, build_mission1_action_catalog
from .legal_action_mask import (
    IllegalActionIdError,
    InvalidActionIdError,
    build_legal_action_selection,
    decode_legal_action_id,
)
from .normalized_state import NormalizedEnvState, normalize_env_state
from .observation import Observation, build_observation

EnvInfo: TypeAlias = dict[str, object]
ResetResult: TypeAlias = tuple[Observation, EnvInfo]
StepResult: TypeAlias = tuple[Observation, float, bool, bool, EnvInfo]


def default_terminal_reward(terminal_outcome: TerminalOutcome | None) -> float:
    """Map Mission 1 terminal outcomes to the default env reward contract."""

    if terminal_outcome is TerminalOutcome.VICTORY:
        return 1.0
    if terminal_outcome is TerminalOutcome.DEFEAT:
        return -1.0
    return 0.0


class Mission1Env:
    """Dependency-free Mission 1 wrapper with Gym-style reset/step returns."""

    def __init__(
        self,
        mission: Mission,
        *,
        default_seed: int = DEFAULT_INITIAL_RNG_SEED,
        max_steps: int | None = None,
    ) -> None:
        if mission.mission_id != MISSION_1_ID:
            raise ValueError(
                "Mission1Env only supports the accepted Mission 1 wrapper contract; "
                f"got {mission.mission_id!r}",
            )
        if max_steps is not None and max_steps < 1:
            raise ValueError("max_steps must be positive when provided")

        self._mission = mission
        self._action_catalog = build_mission1_action_catalog(mission)
        self._default_seed = default_seed
        self._max_steps = max_steps
        self._normalized_state: NormalizedEnvState | None = None
        self._decision_step_count = 0
        self._episode_closed = False
        self._last_seed = default_seed

    @property
    def action_catalog(self) -> MissionActionCatalog:
        """Return the fixed Mission 1 action catalog used by the wrapper."""

        return self._action_catalog

    @property
    def action_space_size(self) -> int:
        """Return the fixed size of the Mission 1 action-id space."""

        return self._action_catalog.size

    def reset(self, *, seed: int | None = None) -> ResetResult:
        """Reset to a deterministic Mission 1 initial state and observation boundary."""

        chosen_seed = self._default_seed if seed is None else seed
        self._last_seed = chosen_seed
        self._decision_step_count = 0
        self._episode_closed = False
        self._normalized_state = normalize_env_state(
            create_initial_game_state(self._mission, seed=chosen_seed),
        )
        return self._build_reset_result()

    def step(self, action_id: int) -> StepResult:
        """Apply one legal action id and return the next wrapper boundary."""

        if self._normalized_state is None:
            raise RuntimeError("Mission1Env.reset() must be called before step()")
        if self._episode_closed:
            raise RuntimeError("Mission1Env episode is closed; call reset() before step()")

        action = decode_legal_action_id(self._normalized_state, self._action_catalog, action_id)
        next_state = apply_action(self._normalized_state.state, action)

        self._decision_step_count += 1
        self._normalized_state = normalize_env_state(next_state)

        terminated = self._normalized_state.state.terminal_outcome is not None
        truncated = not terminated and self._has_reached_step_limit()
        self._episode_closed = terminated or truncated

        info = self._build_info(
            truncation_reason="step_limit" if truncated else None,
        )
        return (
            build_observation(self._normalized_state),
            default_terminal_reward(self._normalized_state.state.terminal_outcome),
            terminated,
            truncated,
            info,
        )

    def _build_reset_result(self) -> ResetResult:
        if self._normalized_state is None:
            raise RuntimeError("Mission1Env has no active state; call reset() first")
        return build_observation(self._normalized_state), self._build_info()

    def _build_info(self, *, truncation_reason: str | None = None) -> EnvInfo:
        if self._normalized_state is None:
            raise RuntimeError("Mission1Env has no active state; call reset() first")

        legal_selection = build_legal_action_selection(
            self._normalized_state,
            self._action_catalog,
        )
        info: EnvInfo = {
            "seed": self._last_seed,
            "action_catalog_size": self._action_catalog.size,
            "decision_step_count": self._decision_step_count,
            "legal_action_ids": list(legal_selection.legal_action_ids),
            "legal_action_mask": list(legal_selection.legal_action_mask),
            "terminal_outcome": (
                None
                if self._normalized_state.state.terminal_outcome is None
                else self._normalized_state.state.terminal_outcome.value
            ),
        }
        if truncation_reason is not None:
            info["truncation_reason"] = truncation_reason
        return info

    def _has_reached_step_limit(self) -> bool:
        return self._max_steps is not None and self._decision_step_count >= self._max_steps


__all__ = [
    "EnvInfo",
    "IllegalActionIdError",
    "InvalidActionIdError",
    "Mission1Env",
    "ResetResult",
    "StepResult",
    "default_terminal_reward",
]

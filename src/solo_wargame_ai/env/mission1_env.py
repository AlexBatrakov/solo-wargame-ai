"""Thin Mission 1 RL wrapper over the accepted resolver facade."""

from __future__ import annotations

from typing import TypeAlias

from solo_wargame_ai.domain.mission import Mission
from solo_wargame_ai.domain.state import DEFAULT_INITIAL_RNG_SEED, TerminalOutcome

from .action_catalog import MISSION_1_ID, MissionActionCatalog, build_mission1_action_catalog
from .legal_action_mask import (
    IllegalActionIdError,
    InvalidActionIdError,
    build_legal_action_selection,
    decode_legal_action_id,
)
from .observation import Observation, build_observation
from .resolver_session import ResolverEnvSession, ResolverSessionSnapshot

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
        self._session = ResolverEnvSession(
            mission,
            default_seed=default_seed,
            max_steps=max_steps,
        )

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

        self._session.reset(seed=seed)
        return self._build_reset_result()

    def step(self, action_id: int) -> StepResult:
        """Apply one legal action id and return the next wrapper boundary."""

        snapshot = self._snapshot_for_step()
        if snapshot.episode_closed:
            raise RuntimeError("Mission1Env episode is closed; call reset() before step()")

        action = decode_legal_action_id(
            snapshot.normalized_state,
            self._action_catalog,
            action_id,
        )
        next_snapshot = self._session.step(action)
        info = self._build_info(next_snapshot)
        return (
            build_observation(next_snapshot.normalized_state),
            default_terminal_reward(next_snapshot.normalized_state.state.terminal_outcome),
            next_snapshot.terminated,
            next_snapshot.truncated,
            info,
        )

    def _build_reset_result(self) -> ResetResult:
        snapshot = self._snapshot_for_build()
        return build_observation(snapshot.normalized_state), self._build_info(snapshot)

    def _build_info(self, snapshot: ResolverSessionSnapshot) -> EnvInfo:
        legal_selection = build_legal_action_selection(
            snapshot.normalized_state,
            self._action_catalog,
        )
        info: EnvInfo = {
            "seed": snapshot.seed,
            "action_catalog_size": self._action_catalog.size,
            "decision_step_count": snapshot.decision_step_count,
            "legal_action_ids": list(legal_selection.legal_action_ids),
            "legal_action_mask": list(legal_selection.legal_action_mask),
            "terminal_outcome": (
                None
                if snapshot.normalized_state.state.terminal_outcome is None
                else snapshot.normalized_state.state.terminal_outcome.value
            ),
        }
        if snapshot.truncation_reason is not None:
            info["truncation_reason"] = snapshot.truncation_reason
        return info

    def _snapshot_for_step(self) -> ResolverSessionSnapshot:
        try:
            return self._session.snapshot
        except RuntimeError as exc:
            raise RuntimeError("Mission1Env.reset() must be called before step()") from exc

    def _snapshot_for_build(self) -> ResolverSessionSnapshot:
        try:
            return self._session.snapshot
        except RuntimeError as exc:
            raise RuntimeError("Mission1Env has no active state; call reset() first") from exc


__all__ = [
    "EnvInfo",
    "IllegalActionIdError",
    "InvalidActionIdError",
    "Mission1Env",
    "ResetResult",
    "StepResult",
    "default_terminal_reward",
]

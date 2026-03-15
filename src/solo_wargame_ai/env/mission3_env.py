"""Thin Mission 3 RL wrapper over the accepted resolver facade."""

from __future__ import annotations

from typing import TypeAlias

from solo_wargame_ai.domain.mission import Mission
from solo_wargame_ai.domain.state import DEFAULT_INITIAL_RNG_SEED, TerminalOutcome

from .legal_action_mask import (
    IllegalActionIdError,
    InvalidActionIdError,
    build_legal_action_selection,
    decode_legal_action_id,
)
from .mission3_action_catalog import (
    MISSION_3_ID,
    Mission3PublicActionCatalog,
    build_mission3_action_catalog,
    build_mission3_contact_handle_map,
    build_mission3_public_action_catalog,
)
from .mission3_observation import Mission3Observation, build_mission3_observation
from .resolver_session import ResolverEnvSession, ResolverSessionSnapshot

Mission3EnvInfo: TypeAlias = dict[str, object]
Mission3ResetResult: TypeAlias = tuple[Mission3Observation, Mission3EnvInfo]
Mission3StepResult: TypeAlias = tuple[Mission3Observation, float, bool, bool, Mission3EnvInfo]


def default_mission3_terminal_reward(terminal_outcome: TerminalOutcome | None) -> float:
    """Map Mission 3 terminal outcomes to the default env reward contract."""

    if terminal_outcome is TerminalOutcome.VICTORY:
        return 1.0
    if terminal_outcome is TerminalOutcome.DEFEAT:
        return -1.0
    return 0.0


class Mission3Env:
    """Dependency-free Mission 3 wrapper with Gym-style reset/step returns."""

    def __init__(
        self,
        mission: Mission,
        *,
        default_seed: int = DEFAULT_INITIAL_RNG_SEED,
        max_steps: int | None = None,
    ) -> None:
        if mission.mission_id != MISSION_3_ID:
            raise ValueError(
                "Mission3Env only supports the accepted Mission 3 wrapper contract; "
                f"got {mission.mission_id!r}",
            )
        if max_steps is not None and max_steps < 1:
            raise ValueError("max_steps must be positive when provided")

        self._mission = mission
        self._contact_handles = build_mission3_contact_handle_map(mission)
        self._raw_action_catalog = build_mission3_action_catalog(mission)
        self._action_catalog = build_mission3_public_action_catalog(
            self._raw_action_catalog,
            self._contact_handles,
        )
        self._session = ResolverEnvSession(
            mission,
            default_seed=default_seed,
            max_steps=max_steps,
        )

    @property
    def action_catalog(self) -> Mission3PublicActionCatalog:
        """Return the fixed public Mission 3 action catalog used by the wrapper."""

        return self._action_catalog

    @property
    def action_space_size(self) -> int:
        """Return the fixed size of the Mission 3 action-id space."""

        return self._action_catalog.size

    def reset(self, *, seed: int | None = None) -> Mission3ResetResult:
        """Reset to a deterministic Mission 3 initial state and observation boundary."""

        self._session.reset(seed=seed)
        return self._build_reset_result()

    def step(self, action_id: int) -> Mission3StepResult:
        """Apply one legal action id and return the next wrapper boundary."""

        snapshot = self._snapshot_for_step()
        if snapshot.episode_closed:
            raise RuntimeError("Mission3Env episode is closed; call reset() before step()")

        action = decode_legal_action_id(
            snapshot.normalized_state,
            self._raw_action_catalog,
            action_id,
        )
        next_snapshot = self._session.step(action)
        info = self._build_info(next_snapshot)
        return (
            build_mission3_observation(next_snapshot.normalized_state, self._contact_handles),
            default_mission3_terminal_reward(next_snapshot.normalized_state.state.terminal_outcome),
            next_snapshot.terminated,
            next_snapshot.truncated,
            info,
        )

    def _build_reset_result(self) -> Mission3ResetResult:
        snapshot = self._snapshot_for_build()
        return (
            build_mission3_observation(snapshot.normalized_state, self._contact_handles),
            self._build_info(snapshot),
        )

    def _build_info(self, snapshot: ResolverSessionSnapshot) -> Mission3EnvInfo:
        legal_selection = build_legal_action_selection(
            snapshot.normalized_state,
            self._raw_action_catalog,
        )
        info: Mission3EnvInfo = {
            "seed": snapshot.seed,
            "action_catalog_size": self._raw_action_catalog.size,
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
            raise RuntimeError("Mission3Env.reset() must be called before step()") from exc

    def _snapshot_for_build(self) -> ResolverSessionSnapshot:
        try:
            return self._session.snapshot
        except RuntimeError as exc:
            raise RuntimeError("Mission3Env has no active state; call reset() first") from exc


__all__ = [
    "IllegalActionIdError",
    "InvalidActionIdError",
    "Mission3Env",
    "Mission3EnvInfo",
    "Mission3ResetResult",
    "Mission3StepResult",
    "default_mission3_terminal_reward",
]

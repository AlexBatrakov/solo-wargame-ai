"""Private mission-dispatch helpers for the bounded masked actor-critic family."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from solo_wargame_ai.domain.mission import Mission
from solo_wargame_ai.env.action_catalog import MISSION_1_ID
from solo_wargame_ai.env.mission1_env import Mission1Env
from solo_wargame_ai.env.mission3_action_catalog import MISSION_3_ID
from solo_wargame_ai.env.mission3_env import Mission3Env

from .feature_adapter import (
    FeatureAdapter,
    Mission3ObservationFeatureAdapter,
    ObservationFeatureAdapter,
)


class LearningEnv(Protocol):
    """Shared reset/step seam required by the accepted learner family."""

    @property
    def action_space_size(self) -> int:
        """Return the fixed wrapper-local action-space size."""

    def reset(
        self,
        *,
        seed: int | None = None,
    ) -> tuple[Mapping[str, object], Mapping[str, object]]:
        """Reset the wrapper and return observation/info."""

    def step(
        self,
        action_id: int,
    ) -> tuple[Mapping[str, object], float, bool, bool, Mapping[str, object]]:
        """Apply one wrapper-local action id."""


def build_learning_env(mission: Mission) -> LearningEnv:
    """Build the accepted env wrapper for the requested learning mission."""

    if mission.mission_id == MISSION_1_ID:
        return Mission1Env(mission)
    if mission.mission_id == MISSION_3_ID:
        return Mission3Env(mission)
    raise ValueError(
        "The masked actor-critic learner supports only the accepted Mission 1 "
        f"and Mission 3 wrappers; got {mission.mission_id!r}",
    )


def build_learning_feature_adapter(
    mission: Mission,
    *,
    feature_adapter_seed: int,
) -> FeatureAdapter:
    """Build the mission-local feature adapter from a fixed dedicated reset seed."""

    env = build_learning_env(mission)
    initial_observation, _ = env.reset(seed=feature_adapter_seed)
    if mission.mission_id == MISSION_1_ID:
        return ObservationFeatureAdapter.from_initial_observation(initial_observation)
    if mission.mission_id == MISSION_3_ID:
        return Mission3ObservationFeatureAdapter.from_initial_observation(
            initial_observation,
        )
    raise AssertionError(f"Unsupported learning mission dispatch: {mission.mission_id!r}")


__all__ = [
    "LearningEnv",
    "build_learning_env",
    "build_learning_feature_adapter",
]

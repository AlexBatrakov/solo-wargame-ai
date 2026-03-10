"""Phase 4 env-layer foundations for Mission 1 observation/action contracts."""

from .action_catalog import (
    MISSION_1_ID,
    ActionCatalogError,
    InvalidActionIdError,
    MissionActionCatalog,
    build_mission1_action_catalog,
)
from .legal_action_mask import (
    IllegalActionIdError,
    LegalActionSelection,
    build_legal_action_selection,
    decode_legal_action_id,
)
from .mission1_env import (
    EnvInfo,
    Mission1Env,
    ResetResult,
    StepResult,
    default_terminal_reward,
)
from .normalized_state import NormalizedEnvState, normalize_env_state
from .observation import Observation, build_observation

__all__ = [
    "ActionCatalogError",
    "EnvInfo",
    "IllegalActionIdError",
    "InvalidActionIdError",
    "LegalActionSelection",
    "MISSION_1_ID",
    "Mission1Env",
    "MissionActionCatalog",
    "NormalizedEnvState",
    "Observation",
    "ResetResult",
    "StepResult",
    "build_legal_action_selection",
    "build_mission1_action_catalog",
    "build_observation",
    "default_terminal_reward",
    "decode_legal_action_id",
    "normalize_env_state",
]

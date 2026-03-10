"""Phase 4 env-layer foundations for Mission 1 observation/action contracts."""

from .action_catalog import (
    ActionCatalogError,
    InvalidActionIdError,
    MISSION_1_ID,
    MissionActionCatalog,
    build_mission1_action_catalog,
)
from .legal_action_mask import (
    IllegalActionIdError,
    LegalActionSelection,
    build_legal_action_selection,
    decode_legal_action_id,
)
from .normalized_state import NormalizedEnvState, normalize_env_state
from .observation import Observation, build_observation

__all__ = [
    "ActionCatalogError",
    "IllegalActionIdError",
    "InvalidActionIdError",
    "LegalActionSelection",
    "MISSION_1_ID",
    "MissionActionCatalog",
    "NormalizedEnvState",
    "Observation",
    "build_legal_action_selection",
    "build_mission1_action_catalog",
    "build_observation",
    "decode_legal_action_id",
    "normalize_env_state",
]

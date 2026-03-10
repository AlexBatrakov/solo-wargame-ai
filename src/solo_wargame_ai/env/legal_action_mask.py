"""Resolver-derived legal action ids and fixed-length mask helpers."""

from __future__ import annotations

from dataclasses import dataclass

from .action_catalog import InvalidActionIdError, MissionActionCatalog
from .normalized_state import NormalizedEnvState


class IllegalActionIdError(ValueError):
    """Raised when an in-range action id is illegal in the current state."""


@dataclass(frozen=True, slots=True)
class LegalActionSelection:
    """Canonical legal ids plus a fixed-length legal-action mask."""

    legal_action_ids: tuple[int, ...]
    legal_action_mask: tuple[bool, ...]


def build_legal_action_selection(
    normalized_state: NormalizedEnvState,
    catalog: MissionActionCatalog,
) -> LegalActionSelection:
    """Encode resolver-owned legality into ids and a fixed-length mask."""

    legal_action_id_set = {
        catalog.encode(action)
        for action in normalized_state.legal_actions
    }
    legal_action_mask = tuple(
        action_id in legal_action_id_set
        for action_id in range(catalog.size)
    )
    legal_action_ids = tuple(
        action_id
        for action_id, is_legal in enumerate(legal_action_mask)
        if is_legal
    )
    return LegalActionSelection(
        legal_action_ids=legal_action_ids,
        legal_action_mask=legal_action_mask,
    )


def decode_legal_action_id(
    normalized_state: NormalizedEnvState,
    catalog: MissionActionCatalog,
    action_id: int,
):
    """Decode one id only if it is legal in the current normalized state."""

    action = catalog.decode(action_id)
    if action not in normalized_state.legal_actions:
        raise IllegalActionIdError(f"Action id {action_id} is illegal in the current state")
    return action


__all__ = [
    "IllegalActionIdError",
    "InvalidActionIdError",
    "LegalActionSelection",
    "build_legal_action_selection",
    "decode_legal_action_id",
]

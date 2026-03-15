"""Mission 3-local player-visible observation builder."""

from __future__ import annotations

from typing import TypeAlias

from solo_wargame_ai.domain.decision_context import ChooseOrderParameterContext

from .mission3_action_catalog import Mission3ContactHandleMap
from .normalized_state import NormalizedEnvState

Mission3Observation: TypeAlias = dict[str, object]


def build_mission3_observation(
    normalized_state: NormalizedEnvState,
    contact_handles: Mission3ContactHandleMap,
) -> Mission3Observation:
    """Build the default Mission 3 player-visible observation boundary."""

    state = normalized_state.state
    return {
        "mission": {
            "mission_id": state.mission.mission_id,
            "name": state.mission.name,
            "coordinate_system": state.mission.map.coordinate_system.value,
            "turn_limit": state.mission.turns.turn_limit,
            "objective": {
                "kind": state.mission.objective.kind.value,
                "description": state.mission.objective.description,
            },
            "forward_directions": [
                direction.value
                for direction in state.mission.map.forward_directions
            ],
            "hexes": [
                {
                    "hex_id": hex_definition.hex_id,
                    "coord": _coord_payload(hex_definition.coord),
                    "terrain_features": [
                        terrain.value
                        for terrain in hex_definition.terrain_features
                    ],
                    "is_start_hex": hex_definition.coord in state.mission.map.start_hex_set,
                }
                for hex_definition in sorted(
                    state.mission.map.hexes,
                    key=lambda candidate: candidate.coord,
                )
            ],
        },
        "turn": state.turn,
        "phase": state.phase.value,
        "terminal_outcome": (
            None if state.terminal_outcome is None else state.terminal_outcome.value
        ),
        "decision": {
            "pending_kind": state.pending_decision.kind.value,
            "pending_order": _pending_order_payload(state.pending_decision),
            "current_activation": _current_activation_payload(state),
        },
        "british_units": [
            {
                "unit_id": unit_state.unit_id,
                "unit_class": unit_state.unit_class,
                "position": _coord_payload(unit_state.position),
                "morale": unit_state.morale.value,
                "cover": unit_state.cover,
                "activated_this_turn": unit_state.unit_id in state.activated_british_unit_ids,
            }
            for unit_state in _sorted_mapping_values(state.british_units)
        ],
        "revealed_german_units": [
            {
                "contact_id": contact_handles.to_contact_id(unit_state.unit_id),
                "unit_class": unit_state.unit_class,
                "position": _coord_payload(unit_state.position),
                "facing": unit_state.facing.value,
                "status": unit_state.status.value,
                "activated_this_phase": unit_state.unit_id in state.activated_german_unit_ids,
            }
            for unit_state in _sorted_mapping_values(state.german_units)
        ],
        "unresolved_markers": [
            {
                "contact_id": contact_handles.to_contact_id(marker_state.marker_id),
                "position": _coord_payload(marker_state.position),
            }
            for marker_state in _sorted_mapping_values(state.unresolved_markers)
        ],
    }


def _coord_payload(coord) -> dict[str, int]:
    return {"q": coord.q, "r": coord.r}


def _current_activation_payload(state) -> dict[str, object] | None:
    activation = state.current_activation
    if activation is None:
        return None

    return {
        "active_unit_id": activation.active_unit_id,
        "roll": None if activation.roll is None else list(activation.roll),
        "selected_die": activation.selected_die,
        "planned_orders": [order.value for order in activation.planned_orders],
        "next_order_index": activation.next_order_index,
        "active_order": None if activation.active_order is None else activation.active_order.value,
    }


def _pending_order_payload(pending_decision) -> dict[str, object] | None:
    if not isinstance(pending_decision, ChooseOrderParameterContext):
        return None

    return {
        "order": pending_decision.order.value,
        "order_index": pending_decision.order_index,
    }


def _sorted_mapping_values(mapping) -> list[object]:
    return [mapping[key] for key in sorted(mapping)]


__all__ = [
    "Mission3Observation",
    "build_mission3_observation",
]

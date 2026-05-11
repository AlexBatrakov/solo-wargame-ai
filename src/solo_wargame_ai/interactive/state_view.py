"""JSON-friendly state view for the local interactive session."""

from __future__ import annotations

from typing import Any

from solo_wargame_ai.domain.actions import GameAction
from solo_wargame_ai.domain.decision_context import ChooseOrderParameterContext
from solo_wargame_ai.domain.hexgrid import HexCoord
from solo_wargame_ai.domain.state import GameState

from .action_view import (
    UIActionView,
    build_activation_restrictions,
    build_activation_roll_options,
    build_ui_action_selection,
)

JsonDict = dict[str, Any]


def build_state_view(state: GameState, legal_actions: tuple[GameAction, ...]) -> JsonDict:
    """Convert a resolver-owned state and legal actions into a browser view."""

    action_selection = build_ui_action_selection(state, legal_actions)
    action_views = action_selection.action_views
    return {
        "mission": _mission_view(state),
        "turn": state.turn,
        "phase": state.phase.value,
        "pending_decision": _pending_decision_view(state),
        "current_activation": _current_activation_view(state),
        "terminal_outcome": (
            None if state.terminal_outcome is None else state.terminal_outcome.value
        ),
        "activated": {
            "british_unit_ids": sorted(state.activated_british_unit_ids),
            "german_unit_ids": sorted(state.activated_german_unit_ids),
        },
        "map": _map_view(state),
        "units": _units_view(state),
        "affordances": _affordances_view(state, action_views),
        "state_token": action_selection.state_token,
        "legal_actions": action_selection.to_list(),
    }


def _mission_view(state: GameState) -> JsonDict:
    return {
        "id": state.mission.mission_id,
        "name": state.mission.name,
        "objective": state.mission.objective.description,
        "turn_limit": state.mission.turns.turn_limit,
    }


def _map_view(state: GameState) -> JsonDict:
    return {
        "coordinate_system": state.mission.map.coordinate_system.value,
        "forward_directions": [
            direction.value for direction in state.mission.map.forward_directions
        ],
        "hexes": [
            {
                "id": hex_definition.hex_id,
                "coord": _coord_view(hex_definition.coord),
                "terrain": [
                    terrain.value for terrain in hex_definition.terrain_features
                ],
                "is_start": hex_definition.coord in state.mission.map.start_hex_set,
            }
            for hex_definition in state.mission.map.hexes
        ],
    }


def _units_view(state: GameState) -> JsonDict:
    return {
        "british": [
            {
                "id": unit_id,
                "unit_class": unit_state.unit_class,
                "display_name": _british_unit_label(state, unit_id),
                "counter_label": _unit_counter_label(unit_id, unit_state.unit_class),
                "coord": _coord_view(unit_state.position),
                "morale": unit_state.morale.value,
                "morale_label": _enum_label(unit_state.morale.value),
                "cover": unit_state.cover,
                "activated": unit_id in state.activated_british_unit_ids,
                "active": (
                    state.current_activation is not None
                    and state.current_activation.active_unit_id == unit_id
                ),
            }
            for unit_id, unit_state in sorted(state.british_units.items())
        ],
        "german": [
            {
                "id": unit_id,
                "unit_class": unit_state.unit_class,
                "display_name": _german_unit_label(state, unit_id),
                "counter_label": _german_counter_label(state, unit_id),
                "coord": _coord_view(unit_state.position),
                "facing": unit_state.facing.value,
                "facing_label": _enum_label(unit_state.facing.value),
                "status": unit_state.status.value,
                "activated": unit_id in state.activated_german_unit_ids,
            }
            for unit_id, unit_state in sorted(state.german_units.items())
        ],
        "unresolved_markers": [
            {
                "id": marker_id,
                "counter_label": _hidden_marker_counter_label(marker_id),
                "coord": _coord_view(marker_state.position),
            }
            for marker_id, marker_state in sorted(state.unresolved_markers.items())
        ],
    }


def _pending_decision_view(state: GameState) -> JsonDict:
    pending = state.pending_decision
    view: JsonDict = {
        "kind": pending.kind.value,
        "label": _decision_label(pending.kind.value),
    }

    if isinstance(pending, ChooseOrderParameterContext):
        view["order"] = pending.order.value
        view["order_label"] = _enum_label(pending.order.value)
        view["order_index"] = pending.order_index

    return view


def _current_activation_view(state: GameState) -> JsonDict | None:
    activation = state.current_activation
    if activation is None:
        return None

    active_unit = state.british_units.get(activation.active_unit_id)
    active_morale = None if active_unit is None else active_unit.morale.value
    return {
        "active_unit_id": activation.active_unit_id,
        "active_unit_label": _british_unit_label(state, activation.active_unit_id),
        "active_unit_morale": active_morale,
        "active_unit_morale_label": None if active_morale is None else _enum_label(active_morale),
        "restrictions": build_activation_restrictions(state),
        "roll": None if activation.roll is None else list(activation.roll),
        "roll_options": build_activation_roll_options(state),
        "selected_die": activation.selected_die,
        "planned_orders": [order.value for order in activation.planned_orders],
        "planned_order_labels": [
            _enum_label(order.value) for order in activation.planned_orders
        ],
        "next_order_index": activation.next_order_index,
        "active_order": (
            None if activation.active_order is None else activation.active_order.value
        ),
    }


def _affordances_view(state: GameState, action_views: tuple[UIActionView, ...]) -> JsonDict:
    british_units: dict[str, list[UIActionView]] = {}
    advance_destinations: dict[tuple[int, int], list[UIActionView]] = {}
    german_units: dict[str, list[UIActionView]] = {}
    hidden_markers: dict[str, list[UIActionView]] = {}

    for action_view in action_views:
        hints = action_view.hints
        if action_view.kind == "select_british_unit":
            british_units.setdefault(str(hints["unit_id"]), []).append(action_view)
        elif action_view.kind == "advance":
            coord = hints["target_coord"]
            advance_destinations.setdefault((coord["q"], coord["r"]), []).append(action_view)
        elif action_view.kind in {"fire", "grenade_attack"}:
            german_units.setdefault(str(hints["target_unit_id"]), []).append(action_view)
        elif action_view.kind == "select_german_unit":
            german_units.setdefault(str(hints["unit_id"]), []).append(action_view)
        elif action_view.kind == "scout":
            hidden_markers.setdefault(str(hints["marker_id"]), []).append(action_view)

    active_unit_id = (
        None if state.current_activation is None else state.current_activation.active_unit_id
    )
    return {
        "acting_side": state.phase.value,
        "active_british_unit_id": active_unit_id,
        "british_units": [
            _target_affordance(unit_id=unit_id, action_views=views)
            for unit_id, views in sorted(british_units.items())
        ],
        "advance_destinations": [
            _coord_affordance(coord=coord, action_views=views)
            for coord, views in sorted(advance_destinations.items())
        ],
        "german_units": [
            _target_affordance(unit_id=unit_id, action_views=views)
            for unit_id, views in sorted(german_units.items())
        ],
        "hidden_markers": [
            _marker_affordance(marker_id=marker_id, action_views=views)
            for marker_id, views in sorted(hidden_markers.items())
        ],
    }


def _coord_affordance(
    *,
    coord: tuple[int, int],
    action_views: list[UIActionView],
) -> JsonDict:
    return {
        "coord": {"q": coord[0], "r": coord[1]},
        **_action_group_affordance(action_views),
    }


def _target_affordance(*, unit_id: str, action_views: list[UIActionView]) -> JsonDict:
    return {
        "unit_id": unit_id,
        **_action_group_affordance(action_views),
    }


def _marker_affordance(*, marker_id: str, action_views: list[UIActionView]) -> JsonDict:
    return {
        "marker_id": marker_id,
        **_action_group_affordance(action_views),
    }


def _action_group_affordance(action_views: list[UIActionView]) -> JsonDict:
    return {
        "action_ids": [action_view.id for action_view in action_views],
        "kinds": [action_view.kind for action_view in action_views],
        "shortcut_action_id": action_views[0].id if len(action_views) == 1 else None,
    }


def _decision_label(kind: str) -> str:
    labels = {
        "choose_british_unit": "Choose a British unit",
        "choose_double_choice": "Resolve the double",
        "choose_activation_die": "Choose an activation die",
        "choose_order_execution": "Choose orders",
        "choose_order_parameter": "Choose order target",
        "choose_german_unit": "Choose a German unit",
    }
    return labels.get(kind, _enum_label(kind))


def _british_unit_label(state: GameState, unit_id: str) -> str:
    unit = state.british_units.get(unit_id)
    if unit is None:
        return _humanize_identifier(unit_id)

    unit_class = state.mission.british.unit_classes_by_name.get(unit.unit_class)
    class_label = unit_class.display_name if unit_class is not None else unit.unit_class
    prefix = f"{unit.unit_class}_"
    if unit_id.startswith(prefix):
        return f"{class_label} {unit_id.removeprefix(prefix).upper()}"
    return _humanize_identifier(unit_id)


def _german_unit_label(state: GameState, unit_id: str) -> str:
    unit = state.german_units.get(unit_id)
    if unit is None:
        return _humanize_identifier(unit_id)

    unit_class = state.mission.german.unit_classes_by_name.get(unit.unit_class)
    class_label = unit_class.display_name if unit_class is not None else unit.unit_class
    return f"{class_label} {_humanize_identifier(unit_id)}"


def _unit_counter_label(unit_id: str, unit_class: str) -> str:
    suffix = _unit_suffix(unit_id, unit_class)
    if suffix is not None:
        return suffix.upper()
    return _humanize_identifier(unit_id)


def _german_counter_label(state: GameState, unit_id: str) -> str:
    unit = state.german_units.get(unit_id)
    if unit is None:
        return _humanize_identifier(unit_id)

    unit_class = state.mission.german.unit_classes_by_name.get(unit.unit_class)
    class_label = unit_class.display_name if unit_class is not None else unit.unit_class
    id_suffix = _identifier_suffix(unit_id)
    if id_suffix is None:
        return _abbreviate_counter_label(class_label)
    return f"{_abbreviate_counter_label(class_label)} {id_suffix.upper()}"


def _hidden_marker_counter_label(marker_id: str) -> str:
    id_suffix = _identifier_suffix(marker_id)
    if id_suffix is None:
        return "?"
    return f"?{id_suffix.upper()}"


def _unit_suffix(unit_id: str, unit_class: str) -> str | None:
    prefix = f"{unit_class}_"
    if unit_id.startswith(prefix):
        return unit_id.removeprefix(prefix)
    return None


def _identifier_suffix(identifier: str) -> str | None:
    parts = identifier.split("_")
    if len(parts) < 2:
        return None
    return parts[-1]


def _abbreviate_counter_label(label: str) -> str:
    known_abbreviations = {
        "heavy_machine_gun": "HMG",
        "light_machine_gun": "LMG",
        "german_rifle_squad": "GRS",
        "Heavy machine gun": "HMG",
        "Light machine gun": "LMG",
        "German Rifle Squad": "GRS",
    }
    if label in known_abbreviations:
        return known_abbreviations[label]

    words = [part for part in label.replace("_", " ").split() if part]
    if not words:
        return label.upper()
    if len(words) == 1:
        return words[0][:3].upper()
    return "".join(word[0].upper() for word in words[:3])


def _coord_view(coord: HexCoord) -> JsonDict:
    return {"q": coord.q, "r": coord.r}


def _enum_label(value: str) -> str:
    return value.replace("_", " ").capitalize()


def _humanize_identifier(value: str) -> str:
    return " ".join(_humanize_part(part) for part in value.split("_"))


def _humanize_part(part: str) -> str:
    if part.isdigit():
        return part
    if len(part) <= 2 and part.isalpha():
        return part.upper()
    return part.capitalize()


__all__ = ["build_state_view"]

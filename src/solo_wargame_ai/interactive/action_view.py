"""Player-facing legal-action summaries for the interactive session."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from solo_wargame_ai.domain.actions import (
    AdvanceAction,
    ChooseOrderExecutionAction,
    DiscardActivationRollAction,
    DoubleChoiceOption,
    FireAction,
    GameAction,
    GrenadeAttackAction,
    OrderExecutionChoice,
    RallyAction,
    ResolveDoubleChoiceAction,
    ScoutAction,
    SelectActivationDieAction,
    SelectBritishUnitAction,
    SelectGermanUnitAction,
    TakeCoverAction,
)
from solo_wargame_ai.domain.mission import OrderName, OrdersChartRow
from solo_wargame_ai.domain.state import GameState
from solo_wargame_ai.domain.units import BritishMorale, BritishUnitState
from solo_wargame_ai.io.replay import serialize_action, summarize_state

JsonDict = dict[str, Any]

LOW_MORALE_RESTRICTION_MESSAGE = "Low morale: only the first order can be executed."


@dataclass(frozen=True, slots=True)
class UIActionView:
    """JSON-friendly view of one currently legal domain action."""

    id: str
    kind: str
    label: str
    payload: JsonDict
    hints: JsonDict

    def to_dict(self) -> JsonDict:
        """Return a plain JSON-friendly dictionary."""

        return {
            "id": self.id,
            "kind": self.kind,
            "label": self.label,
            "payload": self.payload,
            "hints": self.hints,
        }


@dataclass(frozen=True, slots=True)
class UIActionSelection:
    """Per-state action views plus the reverse map used by the session."""

    state_token: str
    action_views: tuple[UIActionView, ...]
    actions_by_id: Mapping[str, GameAction]

    def __post_init__(self) -> None:
        object.__setattr__(self, "action_views", tuple(self.action_views))
        object.__setattr__(
            self,
            "actions_by_id",
            MappingProxyType(dict(self.actions_by_id)),
        )

    def to_list(self) -> list[JsonDict]:
        """Return action views as a JSON-friendly list."""

        return [action_view.to_dict() for action_view in self.action_views]


def build_ui_action_selection(
    state: GameState,
    legal_actions: tuple[GameAction, ...],
) -> UIActionSelection:
    """Build stable per-state UI ids and labels for the current legal actions."""

    state_token = build_state_token(state, legal_actions)
    action_views: list[UIActionView] = []
    actions_by_id: dict[str, GameAction] = {}

    for index, action in enumerate(legal_actions):
        payload = serialize_action(action)
        action_id = f"{state_token}:{index}:{_stable_digest(payload, length=8)}"
        action_view = UIActionView(
            id=action_id,
            kind=str(payload["kind"]),
            label=label_action(action, state),
            payload=payload,
            hints=_action_hints(action, payload, state),
        )
        action_views.append(action_view)
        actions_by_id[action_id] = action

    return UIActionSelection(
        state_token=state_token,
        action_views=tuple(action_views),
        actions_by_id=actions_by_id,
    )


def build_state_token(state: GameState, legal_actions: tuple[GameAction, ...]) -> str:
    """Return a deterministic token for this state and its legal-action frontier."""

    payload = {
        "state": summarize_state(state).to_dict(),
        "rng_state": state.rng_state.to_dict(),
        "legal_actions": [serialize_action(action) for action in legal_actions],
    }
    return f"s{_stable_digest(payload, length=16)}"


def state_token_from_ui_action_id(action_id: str) -> str | None:
    """Extract the state-token prefix from a UI action id if it has this shape."""

    parts = action_id.split(":")
    if len(parts) != 3:
        return None
    token = parts[0]
    if not token.startswith("s") or len(token) < 2:
        return None
    return token


def label_action(action: GameAction, state: GameState) -> str:
    """Return a concise player-facing label for a domain action."""

    if isinstance(action, SelectBritishUnitAction):
        return f"Activate {_british_unit_label(state, action.unit_id)}"

    if isinstance(action, ResolveDoubleChoiceAction):
        if action.choice is DoubleChoiceOption.KEEP:
            activation = state.current_activation
            if activation is not None and activation.roll is not None:
                die_value = activation.roll[0]
                row = _orders_chart_row_for_die(state, die_value)
                if row is not None:
                    label = f"Keep double {die_value}: {_orders_label(row)}"
                    if _active_unit_has_low_morale(state):
                        label += f" ({_low_morale_order_restriction(row)['short_message']})"
                    return label
            return "Keep the double"
        return "Reroll the double"

    if isinstance(action, SelectActivationDieAction):
        row = _orders_chart_row_for_die(state, action.die_value)
        if row is not None:
            label = f"Use die {action.die_value}: {_orders_label(row)}"
            if _active_unit_has_low_morale(state):
                label += f" ({_low_morale_order_restriction(row)['short_message']})"
            return label
        return f"Use die {action.die_value}"

    if isinstance(action, DiscardActivationRollAction):
        return "Discard the roll"

    if isinstance(action, ChooseOrderExecutionAction):
        return _order_execution_label(action, state)

    if isinstance(action, AdvanceAction):
        return f"Advance to {_coord_label(action.destination.q, action.destination.r)}"

    if isinstance(action, FireAction):
        return f"Fire at {_german_unit_label(state, action.target_unit_id)}"

    if isinstance(action, GrenadeAttackAction):
        return f"Grenade attack {_german_unit_label(state, action.target_unit_id)}"

    if isinstance(action, TakeCoverAction):
        return "Take cover"

    if isinstance(action, RallyAction):
        return "Rally"

    if isinstance(action, ScoutAction):
        facing = "" if action.facing is None else f" facing {_enum_label(action.facing.value)}"
        return f"Scout marker {_humanize_identifier(action.marker_id)}{facing}"

    if isinstance(action, SelectGermanUnitAction):
        return f"Resolve German fire: {_german_unit_label(state, action.unit_id)}"

    return repr(action)


def build_activation_roll_options(state: GameState) -> list[JsonDict]:
    """Return Orders Chart summaries for the current activation roll, if available."""

    activation = state.current_activation
    if activation is None or activation.roll is None:
        return []

    roll_options: list[JsonDict] = []
    seen_die_values: set[int] = set()
    for die_value in activation.roll:
        if die_value in seen_die_values:
            continue
        seen_die_values.add(die_value)
        roll_options.append(_die_orders_hint(state, die_value))
    return roll_options


def _action_hints(action: GameAction, payload: JsonDict, state: GameState) -> JsonDict:
    hints: JsonDict = {"kind": payload["kind"]}

    if isinstance(action, AdvanceAction):
        hints["target_coord"] = payload["destination"]
    elif isinstance(action, (FireAction, GrenadeAttackAction)):
        hints["target_unit_id"] = action.target_unit_id
    elif isinstance(action, SelectBritishUnitAction):
        hints["unit_id"] = action.unit_id
    elif isinstance(action, SelectGermanUnitAction):
        hints["unit_id"] = action.unit_id
    elif isinstance(action, ScoutAction):
        hints["marker_id"] = action.marker_id
        if action.facing is not None:
            hints["facing"] = action.facing.value
    elif isinstance(action, ResolveDoubleChoiceAction):
        hints["choice"] = action.choice.value
        if action.choice is DoubleChoiceOption.KEEP:
            activation = state.current_activation
            if activation is not None and activation.roll is not None:
                hints.update(_die_orders_hint(state, activation.roll[0]))
    elif isinstance(action, ChooseOrderExecutionAction):
        hints["choice"] = action.choice.value
        if action.choice is OrderExecutionChoice.BOTH_ORDERS:
            row = _current_orders_row(state)
            if row is not None:
                hints["commitment"] = {
                    "kind": "both_orders",
                    "message": "Both orders are committed before resolving the first order.",
                    "order_labels": [_order_label(order) for order in row.orders],
                }
        restriction = _low_morale_order_execution_restriction(state)
        if restriction is not None:
            hints["restriction"] = restriction
    elif isinstance(action, SelectActivationDieAction):
        hints.update(_die_orders_hint(state, action.die_value))

    return hints


def _die_orders_hint(state: GameState, die_value: int) -> JsonDict:
    hint: JsonDict = {"die_value": die_value}
    row = _orders_chart_row_for_die(state, die_value)
    if row is not None:
        hint["orders"] = [order.value for order in row.orders]
        hint["order_labels"] = [_order_label(order) for order in row.orders]
        if _active_unit_has_low_morale(state):
            hint["restriction"] = _low_morale_order_restriction(row)
    return hint


def _order_execution_label(action: ChooseOrderExecutionAction, state: GameState) -> str:
    if action.choice is OrderExecutionChoice.NO_ACTION:
        return "Skip activation"

    row = _current_orders_row(state)
    if row is None:
        return _enum_label(action.choice.value)

    first_order = _order_label(row.first_order)
    second_order = _order_label(row.second_order)
    if action.choice is OrderExecutionChoice.FIRST_ORDER_ONLY:
        restriction = _low_morale_order_execution_restriction(state)
        if restriction is not None:
            return f"Execute only first order: {first_order}"
        return f"Execute first order: {first_order}"
    if action.choice is OrderExecutionChoice.SECOND_ORDER_ONLY:
        return f"Execute second order: {second_order}"
    if action.choice is OrderExecutionChoice.BOTH_ORDERS:
        return f"Commit to both orders: {first_order}, then {second_order}"
    return _enum_label(action.choice.value)


def _current_orders_row(state: GameState) -> OrdersChartRow | None:
    activation = state.current_activation
    if activation is None or activation.selected_die is None:
        return None

    return _orders_chart_row_for_die(state, activation.selected_die)


def _orders_chart_row_for_die(state: GameState, die_value: int) -> OrdersChartRow | None:
    active_unit = _active_british_unit(state)
    if active_unit is None:
        return None

    chart = state.mission.british.orders_charts_by_unit_class.get(active_unit.unit_class)
    if chart is None:
        return None
    return chart.rows_by_die_value.get(die_value)


def _orders_label(row: OrdersChartRow) -> str:
    return " + ".join(_order_label(order) for order in row.orders)


def _low_morale_order_execution_restriction(state: GameState) -> JsonDict | None:
    active_unit = _active_british_unit(state)
    row = _current_orders_row(state)
    if active_unit is None or row is None or active_unit.morale is not BritishMorale.LOW:
        return None

    return _low_morale_order_restriction(row)


def _low_morale_order_restriction(row: OrdersChartRow) -> JsonDict:
    return {
        "kind": "low_morale",
        "message": LOW_MORALE_RESTRICTION_MESSAGE,
        "short_message": f"low morale: only {_order_label(row.first_order)} available",
        "available_orders": [row.first_order.value],
        "available_order_labels": [_order_label(row.first_order)],
        "unavailable_orders": [row.second_order.value],
        "unavailable_order_labels": [_order_label(row.second_order)],
    }


def _active_unit_has_low_morale(state: GameState) -> bool:
    active_unit = _active_british_unit(state)
    return active_unit is not None and active_unit.morale is BritishMorale.LOW


def build_activation_restrictions(state: GameState) -> list[JsonDict]:
    """Return current activation restrictions that affect action availability."""

    if _active_unit_has_low_morale(state):
        return [
            {
                "kind": "low_morale",
                "message": LOW_MORALE_RESTRICTION_MESSAGE,
            },
        ]
    return []


def _active_british_unit(state: GameState) -> BritishUnitState | None:
    activation = state.current_activation
    if activation is None:
        return None
    return state.british_units.get(activation.active_unit_id)


def _british_unit_label(state: GameState, unit_id: str) -> str:
    unit = state.british_units.get(unit_id)
    if unit is None:
        return _humanize_identifier(unit_id)

    unit_class = state.mission.british.unit_classes_by_name.get(unit.unit_class)
    class_label = unit_class.display_name if unit_class is not None else unit.unit_class
    suffix = _unit_suffix(unit_id, unit.unit_class)
    if suffix is None:
        return _humanize_identifier(unit_id)
    return f"{class_label} {suffix.upper()}"


def _german_unit_label(state: GameState, unit_id: str) -> str:
    unit = state.german_units.get(unit_id)
    if unit is None:
        return _humanize_identifier(unit_id)

    unit_class = state.mission.german.unit_classes_by_name.get(unit.unit_class)
    class_label = unit_class.display_name if unit_class is not None else unit.unit_class
    id_suffix = _identifier_suffix(unit_id)
    if id_suffix is None:
        return _abbreviate_counter_label(class_label)
    return f"{_abbreviate_counter_label(class_label)} {id_suffix.upper()}"


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


def _order_label(order: OrderName) -> str:
    return _enum_label(order.value)


def _enum_label(value: str) -> str:
    return value.replace("_", " ").capitalize()


def _humanize_identifier(value: str) -> str:
    parts = value.split("_")
    return " ".join(_humanize_part(part) for part in parts)


def _humanize_part(part: str) -> str:
    if part.isdigit():
        return part
    if len(part) <= 2 and part.isalpha():
        return part.upper()
    return part.capitalize()


def _coord_label(q: int, r: int) -> str:
    return f"({q}, {r})"


def _stable_digest(payload: object, *, length: int) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


__all__ = [
    "UIActionSelection",
    "UIActionView",
    "LOW_MORALE_RESTRICTION_MESSAGE",
    "build_activation_roll_options",
    "build_activation_restrictions",
    "build_state_token",
    "build_ui_action_selection",
    "label_action",
    "state_token_from_ui_action_id",
]

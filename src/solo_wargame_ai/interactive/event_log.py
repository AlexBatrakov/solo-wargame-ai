"""Concise player-facing event summaries for interactive play."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from solo_wargame_ai.domain.actions import GameAction
from solo_wargame_ai.domain.mission import Mission
from solo_wargame_ai.domain.state import GameState
from solo_wargame_ai.io.replay import (
    ReplayEvent,
    ReplayEventKind,
    build_transition_events,
)

from .action_view import label_action

JsonDict = dict[str, Any]


@dataclass(frozen=True, slots=True)
class UIEventSummary:
    """One concise browser-facing event log entry."""

    id: str
    step: int
    kind: str
    message: str

    def to_dict(self) -> JsonDict:
        """Return a plain JSON-friendly dictionary."""

        return {
            "id": self.id,
            "step": self.step,
            "kind": self.kind,
            "message": self.message,
        }


def build_ui_event_summaries(
    *,
    mission: Mission,
    before_state: GameState,
    after_state: GameState,
    action: GameAction,
    step_index: int,
) -> tuple[UIEventSummary, ...]:
    """Build concise event summaries for one accepted resolver transition."""

    replay_events = build_transition_events(
        mission=mission,
        before_state=before_state,
        after_state=after_state,
        action=action,
        step_index=step_index,
    )
    summaries: list[UIEventSummary] = []

    for event in replay_events:
        message = _event_message(
            event,
            mission=mission,
            before_state=before_state,
            after_state=after_state,
            action=action,
        )
        if message is None:
            continue
        summaries.append(
            UIEventSummary(
                id=f"{step_index}:{len(summaries) + 1}",
                step=step_index,
                kind=event.kind.value,
                message=message,
            ),
        )

    return tuple(summaries)


def event_summaries_to_dicts(events: tuple[UIEventSummary, ...]) -> list[JsonDict]:
    """Return event summaries as plain dictionaries."""

    return [event.to_dict() for event in events]


def _event_message(
    event: ReplayEvent,
    *,
    mission: Mission,
    before_state: GameState,
    after_state: GameState,
    action: GameAction,
) -> str | None:
    details = event.details

    if event.kind is ReplayEventKind.ACTION_SELECTED:
        return f"Action: {label_action(action, before_state)}."

    if event.kind is ReplayEventKind.RANDOM_DRAW:
        return _random_draw_message(details, before_state)

    if event.kind is ReplayEventKind.REVEAL_RESOLVED:
        return (
            f"{_enum_label(details['method'])} reveal {_marker_label(details['marker_id'])}: "
            f"roll {details['roll']} -> "
            f"{_german_class_label(mission, details['unit_class'])} "
            f"facing {_enum_label(details['facing'])}."
        )

    if event.kind is ReplayEventKind.ATTACK_RESOLVED:
        return _attack_message(details, before_state, after_state)

    if event.kind is ReplayEventKind.MORALE_CHANGED:
        return (
            f"Morale: {_british_unit_label(before_state, details['unit_id'])} "
            f"{_enum_label(details['from_morale'])} -> "
            f"{_enum_label(details['to_morale'])}."
        )

    if event.kind is ReplayEventKind.UNIT_REMOVED:
        return f"Removed: {_removed_unit_label(details, before_state, after_state)}."

    if event.kind is ReplayEventKind.PHASE_ADVANCED:
        return (
            f"Phase: {_enum_label(details['from_phase'])} -> "
            f"{_enum_label(details['to_phase'])}."
        )

    if event.kind is ReplayEventKind.TURN_ADVANCED:
        return f"Turn: {details['from_turn']} -> {details['to_turn']}."

    if event.kind is ReplayEventKind.TERMINAL_OUTCOME_SET:
        return f"Outcome: {_enum_label(details['outcome'])}."

    return None


def _random_draw_message(details: JsonDict, state: GameState) -> str | None:
    purpose = details["purpose"]
    if purpose == "activation_roll":
        return (
            f"{_british_unit_label(state, details['unit_id'])} rolled "
            f"{_roll_values(details)} for activation."
        )
    if purpose == "activation_reroll":
        return (
            f"{_british_unit_label(state, details['unit_id'])} rerolled "
            f"{_roll_values(details)} for activation."
        )
    return None


def _attack_message(
    details: JsonDict,
    before_state: GameState,
    after_state: GameState,
) -> str:
    outcome = "hit" if details["hit"] else "miss"
    roll_text = f"roll {details['roll_total']} vs {details['threshold']}"

    if details["side"] == "british":
        attacker = _british_unit_label(before_state, details["attacker_unit_id"])
        target = _german_unit_label(before_state, after_state, details["target_unit_id"])
        if details["attack_kind"] == "grenade_attack":
            return f"{attacker} grenade attack on {target}: {roll_text} -> {outcome}."
        return f"{attacker} fires at {target}: {roll_text} -> {outcome}."

    attacker = _german_unit_label(before_state, after_state, details["attacker_unit_id"])
    target = _british_unit_label(before_state, details["target_unit_id"])
    return f"{attacker} fires at {target}: {roll_text} -> {outcome}."


def _removed_unit_label(
    details: JsonDict,
    before_state: GameState,
    after_state: GameState,
) -> str:
    if details["side"] == "british":
        return _british_unit_label(before_state, details["unit_id"])
    return _german_unit_label(before_state, after_state, details["unit_id"])


def _roll_values(details: JsonDict) -> str:
    return ", ".join(str(value) for value in details["values"])


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


def _german_unit_label(
    before_state: GameState,
    after_state: GameState,
    unit_id: str,
) -> str:
    unit = before_state.german_units.get(unit_id) or after_state.german_units.get(unit_id)
    if unit is None:
        return _humanize_identifier(unit_id)

    unit_class = before_state.mission.german.unit_classes_by_name.get(unit.unit_class)
    class_label = unit_class.display_name if unit_class is not None else unit.unit_class
    id_suffix = _identifier_suffix(unit_id)
    if id_suffix is None:
        return _abbreviate_counter_label(class_label)
    return f"{_abbreviate_counter_label(class_label)} {id_suffix.upper()}"


def _german_class_label(mission: Mission, unit_class: str) -> str:
    class_definition = mission.german.unit_classes_by_name.get(unit_class)
    if class_definition is not None:
        return class_definition.display_name
    return _enum_label(unit_class)


def _marker_label(marker_id: str) -> str:
    suffix = _identifier_suffix(marker_id)
    if suffix is None:
        return _humanize_identifier(marker_id)
    return f"?{suffix.upper()}"


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


__all__ = [
    "UIEventSummary",
    "build_ui_event_summaries",
    "event_summaries_to_dicts",
]

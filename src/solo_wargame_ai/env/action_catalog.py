"""Mission action-id catalog helpers for env wrappers."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

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
from solo_wargame_ai.domain.hexgrid import HexCoord, british_forward_neighbors
from solo_wargame_ai.domain.mission import Mission
from solo_wargame_ai.domain.reveal import legal_scout_facing_directions

MISSION_1_ID = "mission_01_secure_the_woods_1"


class ActionCatalogError(ValueError):
    """Raised when a domain action cannot be mapped through the catalog."""


class InvalidActionIdError(ActionCatalogError):
    """Raised when an action id falls outside the fixed catalog."""


_ORDER_EXECUTION_CHOICES = (
    OrderExecutionChoice.FIRST_ORDER_ONLY,
    OrderExecutionChoice.SECOND_ORDER_ONLY,
    OrderExecutionChoice.BOTH_ORDERS,
    OrderExecutionChoice.NO_ACTION,
)


@dataclass(frozen=True, slots=True)
class MissionActionCatalog:
    """One deterministic fixed action-id mapping for a mission-local env contract."""

    mission_id: str
    actions: tuple[GameAction, ...]
    _action_to_id: Mapping[GameAction, int] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        action_to_id: dict[GameAction, int] = {}
        for action_id, action in enumerate(self.actions):
            if action in action_to_id:
                raise ValueError(f"Duplicate action in catalog: {action!r}")
            action_to_id[action] = action_id

        object.__setattr__(self, "_action_to_id", MappingProxyType(action_to_id))

    @property
    def size(self) -> int:
        """Return the number of action ids in the catalog."""

        return len(self.actions)

    def encode(self, action: GameAction) -> int:
        """Encode one concrete staged domain action as a fixed action id."""

        action_id = self._action_to_id.get(action)
        if action_id is None:
            mission_label = _mission_catalog_label(self.mission_id)
            legacy_hint = "" if mission_label is None else f"; not in the {mission_label} catalog"
            raise ActionCatalogError(
                f"Action is not in the action catalog for {self.mission_id!r}{legacy_hint}: "
                f"{action!r}",
            )
        return action_id

    def decode(self, action_id: int) -> GameAction:
        """Decode one fixed action id into its staged domain action."""

        if action_id < 0 or action_id >= len(self.actions):
            mission_label = _mission_catalog_label(self.mission_id)
            legacy_hint = (
                ""
                if mission_label is None
                else f"; outside the {mission_label} catalog range"
            )
            raise InvalidActionIdError(
                f"Action id {action_id} is outside the action catalog range for "
                f"{self.mission_id!r}{legacy_hint}",
            )
        return self.actions[action_id]


def _mission_catalog_label(mission_id: str) -> str | None:
    parts = mission_id.split("_", 2)
    if len(parts) < 2 or not parts[1].isdigit():
        return None
    return f"Mission {int(parts[1])}"


def build_mission1_action_catalog(mission: Mission) -> MissionActionCatalog:
    """Build the canonical Mission 1 catalog from stable mission data."""

    if mission.mission_id != MISSION_1_ID:
        raise ValueError(
            "Mission 1 action catalog only supports the accepted Mission 1 env contract; "
            f"got {mission.mission_id!r}",
        )

    hidden_marker_ids = tuple(sorted(marker.marker_id for marker in mission.map.hidden_markers))
    actions: list[GameAction] = []

    actions.extend(
        SelectBritishUnitAction(unit_id=unit_id)
        for unit_id in sorted(unit.unit_id for unit in mission.british.roster)
    )
    actions.extend(
        (
            ResolveDoubleChoiceAction(choice=DoubleChoiceOption.KEEP),
            ResolveDoubleChoiceAction(choice=DoubleChoiceOption.REROLL),
        )
    )
    actions.extend(
        SelectActivationDieAction(die_value=die_value)
        for die_value in _activation_die_values(mission)
    )
    actions.append(DiscardActivationRollAction())
    actions.extend(
        ChooseOrderExecutionAction(choice=choice)
        for choice in _ORDER_EXECUTION_CHOICES
    )
    actions.extend(
        AdvanceAction(destination=destination)
        for destination in _canonical_advance_destinations(mission)
    )
    actions.extend(FireAction(target_unit_id=unit_id) for unit_id in hidden_marker_ids)
    actions.extend(GrenadeAttackAction(target_unit_id=unit_id) for unit_id in hidden_marker_ids)
    actions.append(TakeCoverAction())
    actions.append(RallyAction())

    for marker in sorted(mission.map.hidden_markers, key=lambda candidate: candidate.marker_id):
        for facing in legal_scout_facing_directions(mission, marker.coord):
            actions.append(ScoutAction(marker_id=marker.marker_id, facing=facing))

    actions.extend(SelectGermanUnitAction(unit_id=unit_id) for unit_id in hidden_marker_ids)

    return MissionActionCatalog(
        mission_id=mission.mission_id,
        actions=tuple(actions),
    )


def _activation_die_values(mission: Mission) -> tuple[int, ...]:
    return tuple(
        sorted(
            {
                row.die_value
                for orders_chart in mission.british.orders_charts
                for row in orders_chart.rows
            },
        ),
    )


def _canonical_advance_destinations(mission: Mission) -> tuple[HexCoord, ...]:
    return tuple(
        sorted(
            {
                destination
                for position in mission.map.playable_hexes
                for destination in british_forward_neighbors(
                    position,
                    forward_directions=mission.map.forward_directions,
                )
                if mission.map.is_playable_hex(destination)
            },
        ),
    )


__all__ = [
    "ActionCatalogError",
    "InvalidActionIdError",
    "MISSION_1_ID",
    "MissionActionCatalog",
    "build_mission1_action_catalog",
]

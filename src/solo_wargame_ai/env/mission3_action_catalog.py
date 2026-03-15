"""Mission 3-local private raw catalog plus public opaque-handle action view."""

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

from .action_catalog import ActionCatalogError, InvalidActionIdError, MissionActionCatalog

MISSION_3_ID = "mission_03_secure_the_building"

_ORDER_EXECUTION_CHOICES = (
    OrderExecutionChoice.FIRST_ORDER_ONLY,
    OrderExecutionChoice.SECOND_ORDER_ONLY,
    OrderExecutionChoice.BOTH_ORDERS,
    OrderExecutionChoice.NO_ACTION,
)


@dataclass(frozen=True, slots=True)
class Mission3ContactHandleMap:
    """Stable Mission 3-local mapping between raw marker ids and opaque handles."""

    mission_id: str
    raw_ids: tuple[str, ...]
    contact_ids: tuple[str, ...]
    _raw_to_contact: Mapping[str, str] = field(init=False, repr=False)
    _contact_to_raw: Mapping[str, str] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        raw_ids = tuple(self.raw_ids)
        contact_ids = tuple(self.contact_ids)
        if len(raw_ids) != len(contact_ids):
            raise ValueError("Mission3ContactHandleMap requires one contact handle per raw id")
        if len(raw_ids) != len(set(raw_ids)):
            raise ValueError("Mission3ContactHandleMap raw ids must be unique")
        if len(contact_ids) != len(set(contact_ids)):
            raise ValueError("Mission3ContactHandleMap contact ids must be unique")

        object.__setattr__(self, "raw_ids", raw_ids)
        object.__setattr__(self, "contact_ids", contact_ids)
        object.__setattr__(
            self,
            "_raw_to_contact",
            MappingProxyType(dict(zip(raw_ids, contact_ids, strict=True))),
        )
        object.__setattr__(
            self,
            "_contact_to_raw",
            MappingProxyType(dict(zip(contact_ids, raw_ids, strict=True))),
        )

    def to_contact_id(self, raw_id: str) -> str:
        """Return the stable opaque Mission 3 handle for one raw domain id."""

        return self._raw_to_contact[raw_id]

    def to_raw_id(self, contact_id: str) -> str:
        """Return the raw domain id for one opaque Mission 3 handle."""

        return self._contact_to_raw[contact_id]


@dataclass(frozen=True, slots=True)
class Mission3ActionView:
    """One Mission 3-local public action view with opaque contact handles."""

    kind: str
    unit_id: str | None = None
    contact_id: str | None = None
    die_value: int | None = None
    choice: str | None = None
    destination: HexCoord | None = None
    facing: str | None = None


@dataclass(frozen=True, slots=True)
class Mission3PublicActionCatalog:
    """Public Mission 3 action-id surface with no raw `qm_*` leakage."""

    mission_id: str
    actions: tuple[Mission3ActionView, ...]
    _action_to_id: Mapping[Mission3ActionView, int] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        action_to_id: dict[Mission3ActionView, int] = {}
        for action_id, action in enumerate(self.actions):
            if action in action_to_id:
                raise ValueError(f"Duplicate public Mission 3 action view: {action!r}")
            action_to_id[action] = action_id

        object.__setattr__(self, "_action_to_id", MappingProxyType(action_to_id))

    @property
    def size(self) -> int:
        """Return the number of public Mission 3 action ids."""

        return len(self.actions)

    def encode(self, action: Mission3ActionView) -> int:
        """Encode one public Mission 3 action view as a fixed action id."""

        action_id = self._action_to_id.get(action)
        if action_id is None:
            raise ActionCatalogError(
                "Action is not in the Mission 3 public action catalog: "
                f"{action!r}",
            )
        return action_id

    def decode(self, action_id: int) -> Mission3ActionView:
        """Decode one fixed Mission 3 action id into its public action view."""

        if action_id < 0 or action_id >= len(self.actions):
            raise InvalidActionIdError(
                f"Action id {action_id} is outside the Mission 3 public action catalog range",
            )
        return self.actions[action_id]


def build_mission3_contact_handle_map(mission: Mission) -> Mission3ContactHandleMap:
    """Build stable opaque handles for Mission 3 marker-backed German contacts."""

    if mission.mission_id != MISSION_3_ID:
        raise ValueError(
            "Mission3Env only supports the accepted Mission 3 contact-handle mapping; "
            f"got {mission.mission_id!r}",
        )

    raw_ids = tuple(sorted(marker.marker_id for marker in mission.map.hidden_markers))
    return Mission3ContactHandleMap(
        mission_id=mission.mission_id,
        raw_ids=raw_ids,
        contact_ids=tuple(f"contact_{index}" for index in range(len(raw_ids))),
    )


def build_mission3_action_catalog(mission: Mission) -> MissionActionCatalog:
    """Build the private raw-domain Mission 3 catalog used inside the wrapper."""

    if mission.mission_id != MISSION_3_ID:
        raise ValueError(
            "Mission3Env only supports the accepted Mission 3 action catalog; "
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
        ),
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


def build_mission3_public_action_catalog(
    raw_catalog: MissionActionCatalog,
    contact_handles: Mission3ContactHandleMap,
) -> Mission3PublicActionCatalog:
    """Build the public Mission 3 catalog view over the fixed raw action ids."""

    if raw_catalog.mission_id != contact_handles.mission_id:
        raise ValueError("Mission 3 public action catalog requires matching raw ids and handles")

    return Mission3PublicActionCatalog(
        mission_id=raw_catalog.mission_id,
        actions=tuple(
            _to_public_action_view(action, contact_handles)
            for action in raw_catalog.actions
        ),
    )


def _to_public_action_view(
    action: GameAction,
    contact_handles: Mission3ContactHandleMap,
) -> Mission3ActionView:
    if isinstance(action, SelectBritishUnitAction):
        return Mission3ActionView(kind=action.kind.value, unit_id=action.unit_id)
    if isinstance(action, ResolveDoubleChoiceAction):
        return Mission3ActionView(kind=action.kind.value, choice=action.choice.value)
    if isinstance(action, SelectActivationDieAction):
        return Mission3ActionView(kind=action.kind.value, die_value=action.die_value)
    if isinstance(action, DiscardActivationRollAction):
        return Mission3ActionView(kind=action.kind.value)
    if isinstance(action, ChooseOrderExecutionAction):
        return Mission3ActionView(kind=action.kind.value, choice=action.choice.value)
    if isinstance(action, AdvanceAction):
        return Mission3ActionView(kind=action.kind.value, destination=action.destination)
    if isinstance(action, FireAction):
        return Mission3ActionView(
            kind=action.kind.value,
            contact_id=contact_handles.to_contact_id(action.target_unit_id),
        )
    if isinstance(action, GrenadeAttackAction):
        return Mission3ActionView(
            kind=action.kind.value,
            contact_id=contact_handles.to_contact_id(action.target_unit_id),
        )
    if isinstance(action, TakeCoverAction):
        return Mission3ActionView(kind=action.kind.value)
    if isinstance(action, RallyAction):
        return Mission3ActionView(kind=action.kind.value)
    if isinstance(action, ScoutAction):
        return Mission3ActionView(
            kind=action.kind.value,
            contact_id=contact_handles.to_contact_id(action.marker_id),
            facing=None if action.facing is None else action.facing.value,
        )
    if isinstance(action, SelectGermanUnitAction):
        return Mission3ActionView(
            kind=action.kind.value,
            contact_id=contact_handles.to_contact_id(action.unit_id),
        )
    raise TypeError(f"Unsupported Mission 3 action view conversion: {action!r}")


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
    "MISSION_3_ID",
    "Mission3ActionView",
    "Mission3ContactHandleMap",
    "Mission3PublicActionCatalog",
    "build_mission3_action_catalog",
    "build_mission3_contact_handle_map",
    "build_mission3_public_action_catalog",
]

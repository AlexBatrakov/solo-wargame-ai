"""Deterministic learning-side feature extraction over the accepted observation."""

from __future__ import annotations

from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Mapping, Protocol

from solo_wargame_ai.env.observation import Observation

_PHASE_VALUES = ("british", "german")
_TERMINAL_OUTCOME_VALUES = ("victory", "defeat")
_PENDING_KIND_VALUES = (
    "choose_british_unit",
    "choose_double_choice",
    "choose_activation_die",
    "choose_order_execution",
    "choose_order_parameter",
    "choose_german_unit",
)
_ORDER_VALUES = ("advance", "fire", "grenade_attack", "take_cover", "rally", "scout")
_MORALE_VALUES = ("normal", "low", "removed")
_GERMAN_STATUS_VALUES = ("active", "removed")
_FACING_VALUES = (
    "up_left",
    "up",
    "up_right",
    "down_right",
    "down",
    "down_left",
)


@dataclass(frozen=True, slots=True)
class FeatureVector:
    """One fixed-size feature vector derived only from env observations."""

    values: tuple[float, ...]

    @property
    def size(self) -> int:
        return len(self.values)


class FeatureAdapter(Protocol):
    """Shared feature-encoding seam for the accepted masked actor-critic family."""

    feature_size: int

    def encode(self, observation: Mapping[str, object]) -> FeatureVector:
        """Encode one accepted structured env observation into a flat feature vector."""


@dataclass(frozen=True, slots=True)
class ObservationFeatureAdapter:
    """Mission-1 feature adapter over the accepted structured observation."""

    mission_id: str
    turn_limit: int
    british_unit_ids: tuple[str, ...]
    terrain_values: tuple[str, ...]
    max_revealed_german_units: int
    max_unresolved_markers: int
    feature_size: int
    _hex_index_by_coord: Mapping[tuple[int, int], int]
    _static_prefix: tuple[float, ...]

    @classmethod
    def from_initial_observation(cls, observation: Observation) -> ObservationFeatureAdapter:
        """Freeze deterministic slot ordering from the accepted reset observation."""

        mission = observation["mission"]
        mission_hexes = tuple(mission["hexes"])
        british_units = tuple(observation["british_units"])
        revealed_german_units = tuple(observation["revealed_german_units"])
        unresolved_markers = tuple(observation["unresolved_markers"])

        hex_index_by_coord = MappingProxyType(
            {
                _coord_key(hex_payload["coord"]): index
                for index, hex_payload in enumerate(mission_hexes)
            },
        )
        terrain_values = tuple(
            sorted({str(hex_payload["terrain"]) for hex_payload in mission_hexes}),
        )
        static_prefix = tuple(
            feature
            for hex_payload in mission_hexes
            for feature in (
                float(hex_payload["coord"]["q"]),
                float(hex_payload["coord"]["r"]),
                *_one_hot(str(hex_payload["terrain"]), terrain_values),
                1.0 if bool(hex_payload["is_start_hex"]) else 0.0,
            )
        )
        max_entity_slots = len(revealed_german_units) + len(unresolved_markers)
        adapter = cls(
            mission_id=str(mission["mission_id"]),
            turn_limit=int(mission["turn_limit"]),
            british_unit_ids=tuple(str(unit["unit_id"]) for unit in british_units),
            terrain_values=terrain_values,
            max_revealed_german_units=max_entity_slots,
            max_unresolved_markers=max_entity_slots,
            feature_size=0,
            _hex_index_by_coord=hex_index_by_coord,
            _static_prefix=static_prefix,
        )
        return replace(adapter, feature_size=adapter.encode(observation).size)

    def encode(self, observation: Mapping[str, object]) -> FeatureVector:
        """Encode the accepted observation into one deterministic flat vector."""

        mission = observation["mission"]
        if str(mission["mission_id"]) != self.mission_id:
            raise ValueError(
                "ObservationFeatureAdapter mission mismatch: "
                f"expected {self.mission_id!r}, got {mission['mission_id']!r}",
            )

        decision = observation["decision"]
        pending_order = decision["pending_order"]
        current_activation = decision["current_activation"]

        british_units = {
            str(unit["unit_id"]): unit for unit in observation["british_units"]
        }
        revealed_german_units = tuple(
            sorted(
                observation["revealed_german_units"],
                key=lambda unit: str(unit["unit_id"]),
            ),
        )
        unresolved_markers = tuple(
            sorted(
                observation["unresolved_markers"],
                key=lambda marker: str(marker["marker_id"]),
            ),
        )

        if tuple(british_units) != self.british_unit_ids:
            raise ValueError("ObservationFeatureAdapter requires stable British unit ids")
        if len(revealed_german_units) > self.max_revealed_german_units:
            raise ValueError("Observation exceeds the accepted revealed-German slot count")
        if len(unresolved_markers) > self.max_unresolved_markers:
            raise ValueError("Observation exceeds the accepted unresolved-marker slot count")

        features = list(self._static_prefix)
        features.append(float(int(observation["turn"])) / float(self.turn_limit))
        features.extend(_one_hot(str(observation["phase"]), _PHASE_VALUES))
        features.extend(
            _optional_one_hot(observation["terminal_outcome"], _TERMINAL_OUTCOME_VALUES),
        )
        features.extend(_one_hot(str(decision["pending_kind"]), _PENDING_KIND_VALUES))
        features.extend(
            _optional_one_hot(
                None if pending_order is None else str(pending_order["order"]),
                _ORDER_VALUES,
            ),
        )
        features.append(
            0.0 if pending_order is None else float(int(pending_order["order_index"]) + 1),
        )
        features.extend(
            _one_hot_with_none(
                None if current_activation is None else str(current_activation["active_unit_id"]),
                self.british_unit_ids,
            ),
        )
        features.extend(
            (
                (
                    0.0
                    if current_activation is None
                    else _normalize_die(current_activation["roll"], 0)
                ),
                (
                    0.0
                    if current_activation is None
                    else _normalize_die(current_activation["roll"], 1)
                ),
                (
                    0.0
                    if current_activation is None or current_activation["selected_die"] is None
                    else float(int(current_activation["selected_die"])) / 6.0
                ),
            ),
        )
        planned_orders = (
            ()
            if current_activation is None
            else tuple(current_activation["planned_orders"])
        )
        features.extend(
            _one_hot_with_none(
                None if len(planned_orders) < 1 else str(planned_orders[0]),
                _ORDER_VALUES,
            ),
        )
        features.extend(
            _one_hot_with_none(
                None if len(planned_orders) < 2 else str(planned_orders[1]),
                _ORDER_VALUES,
            ),
        )
        features.append(
            0.0
            if current_activation is None
            else float(int(current_activation["next_order_index"]) + 1),
        )
        features.extend(
            _one_hot_with_none(
                None if current_activation is None else current_activation["active_order"],
                _ORDER_VALUES,
            ),
        )

        for unit_id in self.british_unit_ids:
            unit = british_units[unit_id]
            features.extend(_position_one_hot(unit["position"], self._hex_index_by_coord))
            features.extend(_one_hot(str(unit["morale"]), _MORALE_VALUES))
            features.append(float(int(unit["cover"])))
            features.append(1.0 if bool(unit["activated_this_turn"]) else 0.0)

        for unit in revealed_german_units:
            features.append(1.0)
            features.extend(_position_one_hot(unit["position"], self._hex_index_by_coord))
            features.extend(_optional_one_hot(unit["facing"], _FACING_VALUES))
            features.extend(_one_hot(str(unit["status"]), _GERMAN_STATUS_VALUES))
            features.append(1.0 if bool(unit["activated_this_phase"]) else 0.0)
        for _ in range(self.max_revealed_german_units - len(revealed_german_units)):
            features.append(0.0)
            features.extend((0.0,) * len(self._hex_index_by_coord))
            features.extend((0.0,) * len(_FACING_VALUES))
            features.extend((0.0,) * len(_GERMAN_STATUS_VALUES))
            features.append(0.0)

        for marker in unresolved_markers:
            features.append(1.0)
            features.extend(_position_one_hot(marker["position"], self._hex_index_by_coord))
        for _ in range(self.max_unresolved_markers - len(unresolved_markers)):
            features.append(0.0)
            features.extend((0.0,) * len(self._hex_index_by_coord))

        return FeatureVector(values=tuple(features))


@dataclass(frozen=True, slots=True)
class Mission3ObservationFeatureAdapter:
    """Mission-3-local feature adapter over the accepted structured observation."""

    mission_id: str
    turn_limit: int
    british_unit_ids: tuple[str, ...]
    terrain_feature_values: tuple[str, ...]
    max_revealed_german_units: int
    max_unresolved_markers: int
    feature_size: int
    _hex_index_by_coord: Mapping[tuple[int, int], int]
    _static_prefix: tuple[float, ...]

    @classmethod
    def from_initial_observation(
        cls,
        observation: Mapping[str, object],
    ) -> Mission3ObservationFeatureAdapter:
        """Freeze deterministic slot ordering from the accepted Mission 3 reset observation."""

        mission = observation["mission"]
        mission_hexes = tuple(mission["hexes"])
        british_units = tuple(observation["british_units"])
        revealed_german_units = tuple(observation["revealed_german_units"])
        unresolved_markers = tuple(observation["unresolved_markers"])

        hex_index_by_coord = MappingProxyType(
            {
                _coord_key(hex_payload["coord"]): index
                for index, hex_payload in enumerate(mission_hexes)
            },
        )
        terrain_feature_values = tuple(
            sorted(
                {
                    str(terrain_value)
                    for hex_payload in mission_hexes
                    for terrain_value in hex_payload["terrain_features"]
                },
            ),
        )
        static_prefix = tuple(
            feature
            for hex_payload in mission_hexes
            for feature in (
                float(hex_payload["coord"]["q"]),
                float(hex_payload["coord"]["r"]),
                *_multi_hot(
                    tuple(
                        str(terrain_value)
                        for terrain_value in hex_payload["terrain_features"]
                    ),
                    terrain_feature_values,
                ),
                1.0 if bool(hex_payload["is_start_hex"]) else 0.0,
            )
        )
        max_entity_slots = len(revealed_german_units) + len(unresolved_markers)
        adapter = cls(
            mission_id=str(mission["mission_id"]),
            turn_limit=int(mission["turn_limit"]),
            british_unit_ids=tuple(str(unit["unit_id"]) for unit in british_units),
            terrain_feature_values=terrain_feature_values,
            max_revealed_german_units=max_entity_slots,
            max_unresolved_markers=max_entity_slots,
            feature_size=0,
            _hex_index_by_coord=hex_index_by_coord,
            _static_prefix=static_prefix,
        )
        return replace(adapter, feature_size=adapter.encode(observation).size)

    def encode(self, observation: Mapping[str, object]) -> FeatureVector:
        """Encode the accepted Mission 3 observation into one deterministic flat vector."""

        mission = observation["mission"]
        if str(mission["mission_id"]) != self.mission_id:
            raise ValueError(
                "Mission3ObservationFeatureAdapter mission mismatch: "
                f"expected {self.mission_id!r}, got {mission['mission_id']!r}",
            )

        decision = observation["decision"]
        pending_order = decision["pending_order"]
        current_activation = decision["current_activation"]

        british_units = {
            str(unit["unit_id"]): unit for unit in observation["british_units"]
        }
        revealed_german_units = tuple(
            sorted(
                observation["revealed_german_units"],
                key=lambda unit: str(unit["contact_id"]),
            ),
        )
        unresolved_markers = tuple(
            sorted(
                observation["unresolved_markers"],
                key=lambda marker: str(marker["contact_id"]),
            ),
        )

        if tuple(british_units) != self.british_unit_ids:
            raise ValueError(
                "Mission3ObservationFeatureAdapter requires stable British unit ids",
            )
        if len(revealed_german_units) > self.max_revealed_german_units:
            raise ValueError(
                "Observation exceeds the accepted Mission 3 revealed-contact slot count",
            )
        if len(unresolved_markers) > self.max_unresolved_markers:
            raise ValueError(
                "Observation exceeds the accepted Mission 3 unresolved-contact slot count",
            )

        features = list(self._static_prefix)
        features.append(float(int(observation["turn"])) / float(self.turn_limit))
        features.extend(_one_hot(str(observation["phase"]), _PHASE_VALUES))
        features.extend(
            _optional_one_hot(observation["terminal_outcome"], _TERMINAL_OUTCOME_VALUES),
        )
        features.extend(_one_hot(str(decision["pending_kind"]), _PENDING_KIND_VALUES))
        features.extend(
            _optional_one_hot(
                None if pending_order is None else str(pending_order["order"]),
                _ORDER_VALUES,
            ),
        )
        features.append(
            0.0 if pending_order is None else float(int(pending_order["order_index"]) + 1),
        )
        features.extend(
            _one_hot_with_none(
                None if current_activation is None else str(current_activation["active_unit_id"]),
                self.british_unit_ids,
            ),
        )
        features.extend(
            (
                (
                    0.0
                    if current_activation is None
                    else _normalize_die(current_activation["roll"], 0)
                ),
                (
                    0.0
                    if current_activation is None
                    else _normalize_die(current_activation["roll"], 1)
                ),
                (
                    0.0
                    if current_activation is None or current_activation["selected_die"] is None
                    else float(int(current_activation["selected_die"])) / 6.0
                ),
            ),
        )
        planned_orders = (
            ()
            if current_activation is None
            else tuple(current_activation["planned_orders"])
        )
        features.extend(
            _one_hot_with_none(
                None if len(planned_orders) < 1 else str(planned_orders[0]),
                _ORDER_VALUES,
            ),
        )
        features.extend(
            _one_hot_with_none(
                None if len(planned_orders) < 2 else str(planned_orders[1]),
                _ORDER_VALUES,
            ),
        )
        features.append(
            0.0
            if current_activation is None
            else float(int(current_activation["next_order_index"]) + 1),
        )
        features.extend(
            _one_hot_with_none(
                None if current_activation is None else current_activation["active_order"],
                _ORDER_VALUES,
            ),
        )

        for unit_id in self.british_unit_ids:
            unit = british_units[unit_id]
            features.extend(_position_one_hot(unit["position"], self._hex_index_by_coord))
            features.extend(_one_hot(str(unit["morale"]), _MORALE_VALUES))
            features.append(float(int(unit["cover"])))
            features.append(1.0 if bool(unit["activated_this_turn"]) else 0.0)

        for unit in revealed_german_units:
            features.append(1.0)
            features.extend(_position_one_hot(unit["position"], self._hex_index_by_coord))
            features.extend(_optional_one_hot(unit["facing"], _FACING_VALUES))
            features.extend(_one_hot(str(unit["status"]), _GERMAN_STATUS_VALUES))
            features.append(1.0 if bool(unit["activated_this_phase"]) else 0.0)
        for _ in range(self.max_revealed_german_units - len(revealed_german_units)):
            features.append(0.0)
            features.extend((0.0,) * len(self._hex_index_by_coord))
            features.extend((0.0,) * len(_FACING_VALUES))
            features.extend((0.0,) * len(_GERMAN_STATUS_VALUES))
            features.append(0.0)

        for marker in unresolved_markers:
            features.append(1.0)
            features.extend(_position_one_hot(marker["position"], self._hex_index_by_coord))
        for _ in range(self.max_unresolved_markers - len(unresolved_markers)):
            features.append(0.0)
            features.extend((0.0,) * len(self._hex_index_by_coord))

        return FeatureVector(values=tuple(features))


def _coord_key(coord_payload: dict[str, object]) -> tuple[int, int]:
    return int(coord_payload["q"]), int(coord_payload["r"])


def _normalize_die(roll: tuple[int, int] | list[int] | None, index: int) -> float:
    if roll is None or len(roll) <= index:
        return 0.0
    return float(int(roll[index])) / 6.0


def _position_one_hot(
    coord_payload: dict[str, object] | None,
    hex_index_by_coord: Mapping[tuple[int, int], int],
) -> tuple[float, ...]:
    if coord_payload is None:
        return (0.0,) * len(hex_index_by_coord)
    coord = _coord_key(coord_payload)
    if coord not in hex_index_by_coord:
        raise ValueError(f"Unknown hex coordinate in observation: {coord!r}")
    return tuple(
        1.0 if index == hex_index_by_coord[coord] else 0.0
        for index in range(len(hex_index_by_coord))
    )


def _optional_one_hot(
    value: object | None,
    ordered_values: tuple[str, ...],
) -> tuple[float, ...]:
    if value is None:
        return (0.0,) * len(ordered_values)
    return _one_hot(str(value), ordered_values)


def _one_hot_with_none(
    value: object | None,
    ordered_values: tuple[str, ...],
) -> tuple[float, ...]:
    values = ordered_values + ("__none__",)
    encoded_value = "__none__" if value is None else str(value)
    return _one_hot(encoded_value, values)


def _one_hot(value: str, ordered_values: tuple[str, ...]) -> tuple[float, ...]:
    if value not in ordered_values:
        raise ValueError(f"Unknown categorical value {value!r} for {ordered_values!r}")
    return tuple(1.0 if candidate == value else 0.0 for candidate in ordered_values)


def _multi_hot(
    values: tuple[str, ...],
    ordered_values: tuple[str, ...],
) -> tuple[float, ...]:
    value_set = frozenset(values)
    unknown_values = tuple(
        candidate for candidate in value_set if candidate not in ordered_values
    )
    if unknown_values:
        raise ValueError(
            "Unknown categorical values "
            f"{unknown_values!r} for {ordered_values!r}",
        )
    return tuple(1.0 if candidate in value_set else 0.0 for candidate in ordered_values)


__all__ = [
    "FeatureAdapter",
    "FeatureVector",
    "Mission3ObservationFeatureAdapter",
    "ObservationFeatureAdapter",
]

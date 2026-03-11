"""British combat helpers for the current mission slice."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping

from .enums import HexDirection
from .hexgrid import ALL_DIRECTIONS, HexCoord, are_adjacent, neighbor
from .mission import AttackProfile, Mission, OrderName
from .rng import DeterministicRNG, RNGState
from .state import GameState
from .terrain import TerrainType
from .units import (
    BritishMorale,
    BritishUnitState,
    GermanUnitStatus,
    RevealedGermanUnitState,
)


@dataclass(frozen=True, slots=True)
class BritishAttackOutcome:
    """Result of resolving one British attack order."""

    target_unit_id: str
    attack_profile: AttackProfile
    threshold: int
    roll: tuple[int, int]
    hit: bool
    german_units: dict[str, RevealedGermanUnitState]
    rng_state: RNGState

    @property
    def roll_total(self) -> int:
        """Return the summed 2d6 total used to resolve the attack."""

        return sum(self.roll)


def lookup_british_attack_profile(
    mission: Mission,
    *,
    unit_class: str,
    attack_id: str,
) -> AttackProfile:
    """Return the Mission attack profile for one British unit class and attack id."""

    british_unit_class = mission.british.unit_classes_by_name.get(unit_class)
    if british_unit_class is None:
        raise ValueError(f"Mission has no British unit class {unit_class!r}")

    attack_profile = british_unit_class.attacks_by_id.get(attack_id)
    if attack_profile is None:
        raise ValueError(
            f"Mission has no British attack profile {attack_id!r} for unit class {unit_class!r}",
        )
    return attack_profile


def german_fire_zone_hexes(
    mission: Mission,
    german_unit: RevealedGermanUnitState,
) -> tuple[HexCoord, ...]:
    """Return the target's Fire Zone hexes if that German class uses one."""

    german_unit_class = mission.german.unit_classes_by_name[german_unit.unit_class]
    if not german_unit_class.uses_fire_zone:
        return ()

    return tuple(
        neighbor(german_unit.position, direction)
        for direction in _fire_zone_directions(german_unit.facing)
    )


def is_outside_german_fire_zone(
    mission: Mission,
    *,
    attacker_position: HexCoord,
    defender: RevealedGermanUnitState,
) -> bool:
    """Return whether the attacker is outside the defender's Fire Zone."""

    fire_zone_hexes = german_fire_zone_hexes(mission, defender)
    if not fire_zone_hexes:
        return False
    return attacker_position not in fire_zone_hexes


def count_other_adjacent_british_units(
    *,
    attacker_unit_id: str,
    target_position: HexCoord,
    british_units: Mapping[str, BritishUnitState],
) -> int:
    """Count other non-removed British units adjacent to the German target."""

    return sum(
        1
        for unit_id, unit_state in british_units.items()
        if unit_id != attacker_unit_id
        and unit_state.morale is not BritishMorale.REMOVED
        and are_adjacent(unit_state.position, target_position)
    )


def calculate_defender_terrain_modifier(
    mission: Mission,
    *,
    defender_position: HexCoord,
) -> int:
    """Return terrain-based defense modifiers for the defender's current hex."""

    target_hex = mission.map.hex_at(defender_position)
    if target_hex is None:
        return 0

    modifier = 0
    if target_hex.has_terrain(TerrainType.WOODS):
        modifier += mission.combat_modifiers.defender_in_woods
    if target_hex.has_terrain(TerrainType.BUILDING):
        modifier += mission.combat_modifiers.defender_in_building
    return modifier


def calculate_hill_attack_modifier(
    mission: Mission,
    *,
    attacker_position: HexCoord,
) -> int:
    """Return the hill-based attack modifier for the attacker's current hex."""

    attacker_hex = mission.map.hex_at(attacker_position)
    if attacker_hex is None or not attacker_hex.has_terrain(TerrainType.HILL):
        return 0
    return mission.combat_modifiers.attacker_from_hill


def calculate_fire_threshold(
    mission: Mission,
    *,
    attacker: BritishUnitState,
    defender: RevealedGermanUnitState,
    british_units: Mapping[str, BritishUnitState],
) -> int:
    """Return the final 2d6 threshold for a British `fire` attack."""

    attack_profile = lookup_british_attack_profile(
        mission,
        unit_class=attacker.unit_class,
        attack_id=OrderName.FIRE.value,
    )
    threshold = attack_profile.base_to_hit
    threshold += calculate_defender_terrain_modifier(
        mission,
        defender_position=defender.position,
    )
    threshold += calculate_hill_attack_modifier(
        mission,
        attacker_position=attacker.position,
    )

    if is_outside_german_fire_zone(
        mission,
        attacker_position=attacker.position,
        defender=defender,
    ):
        threshold += mission.combat_modifiers.attacker_outside_target_fire_zone

    support_count = count_other_adjacent_british_units(
        attacker_unit_id=attacker.unit_id,
        target_position=defender.position,
        british_units=british_units,
    )
    threshold += (
        support_count * mission.combat_modifiers.per_other_british_unit_adjacent_to_target
    )
    return threshold


def calculate_grenade_attack_threshold(
    mission: Mission,
    *,
    attacker: BritishUnitState,
) -> int:
    """Return the final 2d6 threshold for a British `grenade_attack`."""

    attack_profile = lookup_british_attack_profile(
        mission,
        unit_class=attacker.unit_class,
        attack_id=OrderName.GRENADE_ATTACK.value,
    )
    return attack_profile.base_to_hit


def resolve_british_attack(
    state: GameState,
    *,
    attack_order: OrderName,
    target_unit_id: str,
) -> BritishAttackOutcome:
    """Resolve one British `fire` or `grenade_attack` order against a German target."""

    if state.current_activation is None:
        raise AssertionError("British attack resolution requires current_activation")

    attacker = state.british_units[state.current_activation.active_unit_id]
    defender = state.german_units[target_unit_id]

    if attack_order is OrderName.FIRE:
        attack_profile = lookup_british_attack_profile(
            state.mission,
            unit_class=attacker.unit_class,
            attack_id=attack_order.value,
        )
        threshold = calculate_fire_threshold(
            state.mission,
            attacker=attacker,
            defender=defender,
            british_units=state.british_units,
        )
    elif attack_order is OrderName.GRENADE_ATTACK:
        attack_profile = lookup_british_attack_profile(
            state.mission,
            unit_class=attacker.unit_class,
            attack_id=attack_order.value,
        )
        threshold = calculate_grenade_attack_threshold(
            state.mission,
            attacker=attacker,
        )
    else:
        raise ValueError(f"Unsupported British attack order {attack_order!r}")

    rng = DeterministicRNG.from_state(state.rng_state)
    roll = rng.roll_nd6(2)
    hit = sum(roll) >= threshold

    german_units = dict(state.german_units)
    if hit:
        german_units[target_unit_id] = replace(defender, status=GermanUnitStatus.REMOVED)

    return BritishAttackOutcome(
        target_unit_id=target_unit_id,
        attack_profile=attack_profile,
        threshold=threshold,
        roll=roll,
        hit=hit,
        german_units=german_units,
        rng_state=rng.snapshot(),
    )


def degrade_british_morale(morale: BritishMorale) -> BritishMorale:
    """Advance one British morale step down the current ladder."""

    if morale is BritishMorale.NORMAL:
        return BritishMorale.LOW
    if morale is BritishMorale.LOW:
        return BritishMorale.REMOVED
    return BritishMorale.REMOVED


def _fire_zone_directions(facing: HexDirection) -> tuple[HexDirection, ...]:
    directions = ALL_DIRECTIONS
    facing_index = directions.index(facing)
    return (
        directions[facing_index - 1],
        directions[facing_index],
        directions[(facing_index + 1) % len(directions)],
    )


__all__ = [
    "BritishAttackOutcome",
    "calculate_defender_terrain_modifier",
    "calculate_fire_threshold",
    "calculate_grenade_attack_threshold",
    "calculate_hill_attack_modifier",
    "count_other_adjacent_british_units",
    "degrade_british_morale",
    "german_fire_zone_hexes",
    "is_outside_german_fire_zone",
    "lookup_british_attack_profile",
    "resolve_british_attack",
]

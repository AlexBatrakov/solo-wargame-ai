"""Stage 6B German fire helpers for Mission 1."""

from __future__ import annotations

from dataclasses import replace

from .combat import degrade_british_morale, german_fire_zone_hexes
from .decision_context import ChooseGermanUnitContext
from .hexgrid import are_adjacent
from .rng import DeterministicRNG
from .state import GameState, validate_game_state
from .terrain import TerrainType
from .units import BritishMorale, GermanUnitStatus


def selectable_german_unit_ids(state: GameState) -> tuple[str, ...]:
    """Return active revealed German units that have not activated this phase."""

    return tuple(
        unit_id
        for unit_id, unit_state in sorted(state.german_units.items())
        if unit_state.status is GermanUnitStatus.ACTIVE
        and unit_id not in state.activated_german_unit_ids
    )


def german_fire_target_ids(
    state: GameState,
    *,
    attacker_unit_id: str,
) -> tuple[str, ...]:
    """Return adjacent British targets inside the selected German unit's Fire Zone."""

    attacker = state.german_units[attacker_unit_id]
    fire_zone_hexes = frozenset(german_fire_zone_hexes(state.mission, attacker))

    return tuple(
        unit_id
        for unit_id, unit_state in sorted(state.british_units.items())
        if unit_state.morale is not BritishMorale.REMOVED
        and are_adjacent(attacker.position, unit_state.position)
        and unit_state.position in fire_zone_hexes
    )


def calculate_german_fire_threshold(
    state: GameState,
    *,
    attacker_unit_id: str,
    target_unit_id: str,
) -> int:
    """Return the final 2d6 threshold for one German fire attack."""

    attacker = state.german_units[attacker_unit_id]
    target = state.british_units[target_unit_id]
    german_class = state.mission.german.unit_classes_by_name[attacker.unit_class]
    threshold = german_class.attack_to_hit
    target_hex = state.mission.map.hex_at(target.position)

    if target_hex is not None and target_hex.terrain is TerrainType.WOODS:
        threshold += state.mission.combat_modifiers.defender_in_woods

    threshold += target.cover
    return threshold


def resolve_selected_german_unit_fire(
    state: GameState,
    *,
    unit_id: str,
) -> GameState:
    """Resolve one selected German activation against every eligible British target."""

    rng = DeterministicRNG.from_state(state.rng_state)
    british_units = dict(state.british_units)

    for target_unit_id in german_fire_target_ids(state, attacker_unit_id=unit_id):
        target = british_units[target_unit_id]
        if target.morale is BritishMorale.REMOVED:
            continue

        threshold = calculate_german_fire_threshold(
            state,
            attacker_unit_id=unit_id,
            target_unit_id=target_unit_id,
        )
        roll = rng.roll_nd6(2)
        if sum(roll) >= threshold:
            british_units[target_unit_id] = replace(
                target,
                morale=degrade_british_morale(target.morale),
            )

    next_state = replace(
        state,
        british_units=british_units,
        activated_german_unit_ids=frozenset((*state.activated_german_unit_ids, unit_id)),
        pending_decision=ChooseGermanUnitContext(),
        current_activation=None,
        rng_state=rng.snapshot(),
    )
    validate_game_state(next_state)
    return next_state


__all__ = [
    "calculate_german_fire_threshold",
    "german_fire_target_ids",
    "resolve_selected_german_unit_fire",
    "selectable_german_unit_ids",
]

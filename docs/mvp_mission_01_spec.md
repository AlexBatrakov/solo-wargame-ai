# MVP Mission 1 Spec

## Purpose

This document is the formal Phase 0 specification for the first playable slice
of the simulator.

It answers the practical question:

**what exactly must the first implemented engine support before any code is
written?**

This is not a replacement for the full rulebook.
It is the scoped contract for the first implementation milestone.

Related documents:
- `docs/reference/rules_digest.md`
- `docs/mission_config.md`
- `docs/game_spec.md`
- `docs/state_model.md`
- `docs/action_model.md`
- `docs/testing_strategy.md`
- `configs/missions/mission_01_secure_the_woods_1.toml`

## Scope boundary

The first playable target is:

- **Mission 1 - Secure the Woods (1)**

The goal of this slice is not to prove broad rule coverage.
The goal is to prove that the engine can faithfully execute the real written
turn structure on the smallest meaningful mission.

## Supported British unit classes

This slice supports:

- `rifle_squad`

Mission 1 British roster:

- `rifle_squad_a`
- `rifle_squad_b`

Supported British attack modes in this slice:

- `fire` using rifles
- `grenade_attack`

Supported British morale states in this slice:

- `normal`
- `low`
- `removed`

## Supported German unit classes

This slice supports:

- `heavy_machine_gun`
- `light_machine_gun`

German units in this slice:

- are static once revealed
- have facing
- have Fire Zones
- are removed after one successful British hit

## Supported terrain and board features

This slice supports:

- `clear`
- `woods`
- British start hexes
- unresolved hidden enemy markers (`?`)
- turn tracker / turn limit

This slice does not yet need:

- buildings
- hills
- rivers
- bridges
- minefields
- pre-revealed German units

## Supported player orders

Mission 1 requires these British orders:

- `advance`
- `fire`
- `grenade_attack`
- `take_cover`
- `rally`
- `scout`

Mission 1 Orders Chart is part of scenario data, not engine logic.

## Explicitly out of scope for the first playable slice

The following rule families are intentionally out of scope for the first
implemented engine slice:

- British MG teams
- Mortars
- PIAT teams
- Half-Tracks
- Minefields
- Artillery
- Buildings
- Hills
- Rivers / bridges
- multiple British start hexes
- later mission objective variants such as entering/occupying a target hex

These are not rejected forever.
They are deferred to later milestones in the mission ladder.

## Mission 1 objective in code terms

Mission 1 objective text:

- "Reveal and clear the German unit before time runs out."

Mission 1 terminal victory condition should be modeled as:

- all Mission 1 hidden markers are resolved; and
- no German units remain on the map.

This works because Mission 1 contains exactly one hidden marker and no
pre-revealed German units.

Mission 1 terminal defeat condition should be modeled exactly as written:

- the final turn has been completed; and
- the victory condition is still false.

Important planning decision:
- no extra early-loss rule is introduced at Phase 0 beyond the written turn
  limit rule.

## Hidden-information semantics for Mission 1

Mission 1 has one unresolved hidden marker.

The engine should model that marker as:

- an unresolved enemy position,
- not a pre-instantiated German unit.

Reveal behavior:

1. A marker is revealed either:
   - when a British unit Advances into an adjacent hex, or
   - when a British unit uses Scout from exactly 2 hexes away.
2. On reveal, the engine rolls on the mission's Enemy Unit Chart.
3. The sampled German unit is placed in the marker hex.
4. The marker is marked resolved and no longer exists as hidden state.

Facing on reveal:

- movement reveal: German unit faces the revealing British unit
- scout reveal: player chooses one legal downward-facing direction

## Stochastic elements in Mission 1

Mission 1 includes these stochastic events:

- British 2d6 activation roll
- reveal-table roll for the hidden marker
- British attack rolls
- German attack rolls

All stochastic events must flow through the project RNG interface.

The following are **not** stochastic engine events:

- British activation order
- whether a double is kept or rerolled
- die-result choice
- whether a unit performs the first order, second order, both, or no action
- target / destination choices
- German activation order

Those are decisions and should appear as legal choices in the domain flow.

## Mission 1 decision contexts

The domain engine for Mission 1 should be able to represent at least these
decision contexts:

1. choose next British unit to activate
2. decide whether to keep or reroll a double
3. choose one die result or discard both dice
4. choose how to execute the order pair allowed by the selected die
5. choose any required order parameters:
   - advance destination
   - fire target
   - grenade target
   - scout marker
6. choose next German unit to resolve during the German phase

German target selection itself is not a player decision in Mission 1:

- a German unit fires automatically at every adjacent British unit inside its
  Fire Zone

## Legal state requirements for Mission 1

A valid Mission 1 state must satisfy at least these invariants:

- every unit occupies a playable map hex
- no British unit occupies the same hex as a German unit
- British units may stack with other British units
- no unresolved hidden marker shares a hex with a revealed German unit
- every revealed German unit has a valid facing
- every British unit has a valid morale state
- every British unit has non-negative Cover
- current turn / phase / pending decision context are mutually consistent
- any active-unit reference points to a currently existing non-removed unit
- already-activated unit bookkeeping is consistent within the turn

## Legal action requirements for Mission 1

A legal Mission 1 action must be legal relative to the **current decision
context**, not only to the broad board position.

Examples:

- a British unit may be chosen for activation only if it has not already
  activated this turn and is not removed
- a double may be rerolled only immediately after that double is rolled
- a die result may be chosen only from the currently accepted 2d6 result
- `advance` destinations must be one of the three British forward neighbors
  that exist on the map, are playable, and do not contain a German unit
- `fire` and `grenade_attack` require an adjacent revealed German target
- `scout` requires an unresolved marker exactly 2 hexes away
- `rally` is useful only on a Low-morale unit, though the engine may still
  permit it if it chooses to model wasted orders explicitly
- German activation choice is limited to revealed German units that have not yet
  activated this German phase

## Mission 1 combat and modifier support

This slice must support:

- base rifle fire threshold `8+`
- base grenade threshold `6+` with no modifiers
- German HMG attack threshold `5+`
- German LMG attack threshold `6+`
- Woods defense modifier `+1`
- British flanking modifier `-1`
- British support modifier `-1` per other adjacent British unit
- British Cover bonus against German fire

This slice does not yet need:

- Building modifier
- Hill modifier
- Mortar modifier
- PIAT-specific exceptions

## Replay / trace requirements for Mission 1

Mission 1 replay support should be planned around these minimum trace elements:

- mission id
- seed or serializable RNG state
- every stochastic draw and its purpose
- every player-selected action
- reveal events
- hit/miss results
- morale changes
- unit removals
- turn advancement
- terminal outcome

## What counts as "Phase 0 complete enough" for Mission 1

Mission 1 planning should be considered complete enough to start Phase 1 once:

- scenario data is transcribed
- coordinate convention is fixed
- domain decision flow is fixed
- Mission 1 scope boundaries are explicit
- terminal conditions are explicit
- hidden-information semantics are explicit
- testing/replay expectations are explicit

This document is intended to satisfy that closeout requirement for the first
playable slice.

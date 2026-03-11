# Rules Digest

## Purpose

This file is a software-oriented digest of `docs/reference/rules.pdf`.

It is not a replacement for the PDF.
It exists so future implementation work can recover the core mechanics quickly without
re-reading the whole booklet every time.

Primary source:
- `docs/reference/rules.pdf`

Important rulebook sections:
- pages 5-13: core rules
- page 14: player aid
- pages 16-27: Missions 1-6 (the basic rules ladder)
- pages 28-37: Missions 7-11 (advanced mechanics start appearing)

## Core game loop

The player controls British units and tries to satisfy a mission-specific win
condition before the turn tracker runs out.

At a high level, each turn is:

1. Advance the turn tracker.
2. Activate every British unit once, in an order chosen by the player.
3. Activate every revealed German unit once, in an order chosen by the player.
4. Check whether the mission has been won or lost.

The player wins immediately when the mission win condition is satisfied.
If the final turn is completed and the objective has not been achieved, the
mission is lost.

## British activation flow

Each British unit activates once per turn.

Activation sequence:

1. Choose a British unit that has not yet activated this turn.
2. Roll 2d6.
3. If the roll is a double, the player may either:
   - keep the double and use that die value, or
   - reroll both dice.
4. If another double is rolled, the reroll option can be repeated again.
5. Once the final roll is accepted, the player chooses one die result only.
   The other die is discarded.
6. The chosen die points to an Orders Chart entry for that unit type in the
   current mission.
7. A unit with Normal morale may perform:
   - only the first order,
   - only the second order,
   - or both orders in the printed sequence.
8. A unit with Low morale may perform only the first listed order, or do
   nothing.

Examples from the rulebook:
- `ADV/FIRE` allows `ADV`, or `FIRE`, or `ADV -> FIRE`.
- It does not allow `FIRE -> ADV`.
- The player may discard both dice and do nothing.

## Orders

### Advance

- Move exactly 1 hex.
- Movement must be forward, meaning toward the top of the printed map.
- British units may stack with other British units.
- British units may not enter a hex containing a German unit.
- Moving out of a hex removes all accumulated Cover from that British unit.
- If the destination hex is adjacent to one or more unresolved `?` markers, all
  adjacent markers are immediately revealed.

### Fire

- Target exactly 1 revealed German unit in an adjacent hex.
- Roll 2d6.
- Hit succeeds if the roll is greater than or equal to the attacker's current
  `to_hit` threshold after modifiers.
- One successful hit removes the German target from play.

### Grenade Attack

- Target exactly 1 adjacent German unit.
- Always hits on `6+`.
- No modifiers apply.
- Flanking, support, terrain, hill, and mortar bonuses do not apply.

### Take Cover

- Add one Cover level to the British unit.
- Each Cover level adds `+1` to enemy `to_hit` values against that unit.
- Cover stacks without a printed cap.
- All Cover is lost as soon as the unit Advances out of the hex.

### Rally

- British unit morale goes from Low to Normal.
- If the unit started the activation at Low morale, it still only performs this
  one order on that activation.

### Scout

- Reveal exactly 1 unresolved `?` that is exactly 2 hexes away.
- If a German unit is revealed by Scout, the player chooses the unit's facing.
- The chosen facing must be one of the downward-facing directions and may not
  point directly off-map.
- Scout avoids the immediate Minefield hit test that happens when a Minefield is
  found by movement.

## Morale

British units use a 3-state ladder:

- Normal
- Low
- Removed

Effects:
- a hit on a Normal British unit -> Low morale
- a hit on a Low morale British unit -> Removed
- Low morale units are less effective because they may only perform the first
  order from the chosen Orders Chart row
- Rally restores Low -> Normal

German units do not use the same morale ladder in the rulebook.
They are generally removed by a single successful British hit.

## German units and facing

German units are static defenders.
Once revealed, they stay where they are.

German facing matters because each non-artillery German unit has a Fire Zone:
- the hex it faces
- plus the two adjacent hexes on either side of that facing

German activation:
- each revealed German unit activates once in the German phase
- on activation it fires at every adjacent British unit that is inside its Fire
  Zone

British units do not have facing and do not use Fire Zones.
They may fire into any adjacent hex.

## Reveal rules and hidden information

Enemy positions start as unresolved `?` markers.

They are revealed in two ways:
- a British unit Advances into a hex adjacent to the marker
- a British unit uses Scout on a marker exactly 2 hexes away

On reveal:

1. Roll on the mission-specific Enemy Unit Chart.
2. Place the resulting German unit, or Minefield if applicable.
3. Determine facing:
   - if revealed by movement, face the revealing British unit
   - if revealed by Scout, the player chooses one legal downward-facing option

Important modeling implication:
- unresolved `?` markers do not need to hide pre-sampled units
- the enemy type is sampled at reveal time from the mission chart

## Combat modifiers

The rulebook defines threshold modifiers rather than additive attack bonuses.
Lower target numbers are better for the attacker.

Core modifiers:
- target in Woods: `+1`
- target in Building: `+2`
- attacker firing from Hill: `-1`
- British attacker firing from outside the German target's Fire Zone: `-1`
- for each other British unit adjacent to the German target: `-1`

Notes:
- these modifiers apply to Fire, not to Grenade Attack
- Cover bonuses on British units add to enemy `to_hit` thresholds against that
  British unit
- German units do not receive flanking/support-style bonuses when they attack

## Unit families seen in the rulebook

### British

Rifle Squad:
- rifles: `8+`
- grenades: `6+` with no modifiers

LMG Team:
- machine gun: `6+`

Mortar Team:
- cannot Fire directly
- provides `-2` support if exactly 2 hexes from the German target of a British
  attack
- still gives the normal adjacent support bonus if adjacent to the target
- can also benefit from Hill when providing mortar support

PIAT Team:
- `7+`
- may Fire only at Half-Tracks and units in Buildings
- ignores the Building `+2` defense bonus
- still benefits from normal Hill, Woods, Support, Mortar, and Flanking bonuses

### German

Heavy machine gun:
- `5+`

Light machine gun:
- `6+`

German rifle squad:
- `8+`

Half-Track:
- revealed on the map at mission start
- facing is pre-printed on the map
- can only be Hit by a PIAT Team

Artillery:
- revealed on the map at mission start
- has no facing and cannot be flanked
- attacks every British unit not in defensive cover
- Artillery attack threshold is `10+`

Minefield:
- appears from the Enemy Unit Chart in later missions
- cannot be removed
- if found by movement, immediately tests for a hit on `7+` with no modifiers
- if revealed by Scout, no immediate hit test
- any British unit inside a Minefield hex during German activation tests for a
  Minefield hit on `7+`

## Terrain and board semantics

Terrain effects that matter in code:

- Clear: no terrain modifier
- Woods: defender gets `+1`
- Building: defender gets `+2`
- Hill: attacker gets `-1`
- River: blocks movement across river edges except at bridges

Other board features:
- start hexes are marked by black forward-pointing triangles
- unresolved enemy positions are `?`
- some missions include pre-revealed German units on the map
- turn limit is mission-specific

Important modeling implication:
- the map model must represent blocked edges, not just per-hex terrain
- Rivers are edge constraints

## Mission progression in the booklet

The missions form a natural implementation ladder.

### Missions 1-2

Introduces:
- Rifle Squads only
- Woods
- single or multiple hidden enemy markers
- reveal mechanics
- morale
- German Fire Zones
- flanking and support

Recommended use:
- first faithful playable simulator slice

### Missions 3-4

Adds:
- Buildings
- Hills
- German Rifle Squad

Recommended use:
- first terrain-extension milestone after Mission 1

### Missions 5-6

Adds:
- British MG Team
- unit-type-specific Orders Charts
- multiple start hexes in Mission 6

Recommended use:
- first British roster extension

### Missions 7-9

Adds:
- Mortar Team
- PIAT Team
- Half-Track
- Rivers / bridges
- Minefields

Recommended use:
- first advanced-rules milestone

### Missions 10-11

Adds:
- Artillery

Recommended use:
- final "core rulebook" milestone before broad mission coverage

## Scenario data that must exist in code

Every mission config will eventually need at least:

- mission id and name
- objective type and win condition
- turn limit
- hex map layout
- terrain per hex
- blocked river edges / bridges
- start hexes
- unresolved `?` marker positions
- pre-revealed German units and their facing
- British roster
- mission-specific Orders Chart per British unit type
- mission-specific Enemy Unit Chart
- mission-specific modifier table

## Architecture implications for the simulator

The rulebook pushes the implementation toward a staged decision engine rather
than a single flat action per turn.

Important implications:

- British unit activation order is a player decision.
- Double-reroll choice is a player decision.
- Choosing which die to keep is a player decision.
- Choosing whether to execute the first order, second order, or both is a player
  decision.
- Parameters of each order are also decisions.
- German activation order is a player decision.

This means the engine needs an explicit decision context / subphase model.

Suggested interpretation for implementation planning:
- the domain engine should model the rule-faithful staged decision flow
- later environment wrappers may choose to compress some of that flow if doing so
  does not distort the learning problem too much

## Recommended first implementation target

Mission 1 is the best first playable slice because it covers the essential loop
without the later advanced units and terrain complications.

Mission 1 requires:
- forward movement
- reveal of one hidden marker
- German facing and Fire Zones
- Rifle fire
- Grenade attacks
- Cover
- Rally
- Scout
- morale
- turn limit
- mission objective checking

That is enough to prove the architecture before extending to richer missions.

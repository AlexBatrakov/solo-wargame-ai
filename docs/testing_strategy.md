# Testing Strategy

## Goals

Testing exists to guarantee:
- correctness of implemented rules,
- reproducibility of stochastic simulations,
- confidence during refactoring,
- trustworthy comparisons between agents.

## Testing philosophy

Because the project is a simulation engine, correctness matters more than superficial coverage numbers.

Tests should focus on:
- state invariants,
- legality,
- deterministic reproducibility,
- rule resolution,
- scenario setup integrity.

## Test layers

### 1. Unit tests
Small tests for isolated rule subsystems:
- hex-grid neighbors,
- terrain lookup,
- unit serialization,
- action validation,
- RNG determinism.

### 2. Rule tests
Subsystem-level tests for:
- movement resolution,
- combat resolution,
- morale / status changes,
- reveal mechanics,
- victory conditions.

### 3. Integration tests
End-to-end tests for:
- loading a mission,
- running several actions,
- completing a short deterministic trace.

### 4. Replay / regression tests
Saved seeds or action traces should reproduce identical outcomes across refactors unless behavior is intentionally changed.

## Determinism requirements

All stochastic tests should use controlled seeds.

The simulator should support:
- fixed-seed runs,
- replayable traces,
- stable regression tests.

## Test priorities for MVP

Highest-priority tests:
1. grid correctness,
2. legal action generation,
3. movement transitions,
4. mission loading,
5. terminal condition checks,
6. deterministic seed behavior.

## Mission 1 test matrix

Before Mission 1 implementation is considered trustworthy, the test plan should
cover at least:

1. Mission 1 config loading
2. axial neighbor and British-forward-neighbor logic
3. activation roll handling, including doubles and reroll decisions
4. die-result selection legality
5. Orders Chart lookup for `rifle_squad`
6. `advance` legality and Cover loss on movement
7. reveal by movement, including German facing toward the revealer
8. reveal by Scout, including legal downward-facing choices
9. rifle fire modifier calculation
10. grenade attacks ignoring modifiers
11. German Fire Zone targeting
12. morale transitions (`normal -> low -> removed`)
13. victory and defeat conditions for Mission 1
14. fixed-seed deterministic replay of a short complete trace

## Invariants to enforce with tests

The engine should eventually have tests for invariants such as:

- units only occupy playable hexes
- British/German co-occupation is impossible
- unresolved hidden markers do not coexist with revealed German units
- revealed German units always have valid facing
- removed units are not re-activatable
- already-activated bookkeeping resets correctly across turns
- legal actions depend only on current state and controlled RNG behavior

## Replay and reproducibility policy

Replayability should be treated as a first-class engineering feature, not as an
optional debugging extra.

Minimum planning target:

- fixed mission config
- fixed seed or RNG state
- fixed chosen action sequence
- identical resulting trajectory

Useful replay contents:

- random draws and their purposes
- selected actions
- derived events such as reveal, hit, morale loss, removal, and mission end

## Config validation policy

Mission configs should be validated by tests for cases such as:

- unknown terrain type
- duplicate unit ids
- hidden markers on non-playable hexes
- start hexes on non-playable hexes
- reveal-table gaps or overlaps
- invalid Orders Chart rows
- invalid forward-direction names

## Non-goals

Tests should not depend on GUI or visual output.
The first versions should stay lightweight and domain-focused.

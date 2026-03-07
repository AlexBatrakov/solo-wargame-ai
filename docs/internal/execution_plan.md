# Execution Plan

## Purpose

This file turns the current repository from "good conceptual notes" into an
operational build plan.

It is the main handoff document for future Codex threads.
If a thread needs to decide what to do next, this file should be the first place
it checks after reading the rules digest.

## Project intent

The project has two long-term goals:

1. build a faithful, testable simulator for the game in `rules.pdf`
2. use that simulator to train and evaluate learning agents

The build order must remain:

1. rule digestion and formalization
2. simulator foundation
3. playable mission slices
4. baseline agents
5. RL wrapper
6. RL experiments

## Phase boundary

For this repository, the practical boundary is:

- **Phase 0** = documents, assumptions, config conventions, mission
  transcription, and other planning artifacts
- **Phase 1** = the first code written under `src/` to execute that plan

That means items such as:
- package skeleton,
- mission loader,
- hex-grid helpers,
- `GameState`,
- resolver code,

are already Phase 1 work, even if they are small and foundational.

## Resolved planning decision after reading the rulebook

The original project drafts leaned toward macro-actions for MVP.
After reading the rules, that preference was replaced.

Reason:
- the game has multiple nested player decisions inside a single British unit
  activation
- the player also chooses German activation order
- doubles create a reroll/keep decision point
- choosing which die to keep is a distinct decision point

Operational conclusion:
- the domain engine should first model rule-faithful staged decision contexts
- any later macro-action compression should happen at the environment layer, not
  by hard-coding away the rule flow too early

This decision is now considered part of Phase 0 project truth.

## MVP ladder

Do not try to support the whole book at once.
Use the mission ladder embedded in the rulebook itself.

### Milestone A - Mission 1 only

Rules covered:
- Rifle Squads
- Woods
- reveal of `?`
- German facing / Fire Zones
- Advance / Fire / Grenade / Cover / Rally / Scout
- British morale
- turn limit
- mission objective checking

Why this milestone:
- smallest faithful playable slice
- enough to validate turn flow, hidden reveal, combat, and legality

Exit criteria:
- mission loads from config
- mission can be played end-to-end
- all legal decisions are generated from state
- replay under fixed seed is reproducible

### Milestone B - Missions 3-4 capability

Rules added:
- Buildings
- Hills
- German Rifle Squad

Why this milestone:
- completes the basic terrain/combat modifier set
- still avoids advanced British specialist units

Exit criteria:
- Mission 1 still passes unchanged
- Building/Hill modifiers are covered by tests
- Mission 3 or 4 can be played end-to-end

### Milestone C - Missions 5-6 capability

Rules added:
- British MG Team
- unit-type-specific Orders Charts
- multiple start hexes

Why this milestone:
- first roster-extension test
- proves unit-specific order availability and mission setup flexibility

Exit criteria:
- different British unit classes can coexist cleanly
- Orders Chart lookup is mission + unit-type aware
- Mission 5 or 6 runs deterministically

### Milestone D - Missions 7-9 capability

Rules added:
- Mortar Team
- PIAT Team
- Half-Track
- Rivers / bridges
- Minefields

Why this milestone:
- introduces the first serious exceptions to "adjacent direct fire"
- forces map-edge/blocking representation and special targeting rules

Exit criteria:
- Mortar support works
- PIAT targeting restrictions work
- Half-Track pre-placement works
- river edge blocking works
- Minefield reveal / hit tests work

### Milestone E - Missions 10-11 capability

Rules added:
- Artillery

Why this milestone:
- completes the core rulebook mechanics that materially change combat targeting

Exit criteria:
- Artillery target selection logic works
- Artillery cannot be flanked
- cover filtering for Artillery attacks is correct

### Milestone F - Baselines

Add:
- random policy
- simple heuristic policy
- batch simulation harness

Exit criteria:
- both agents can run many episodes
- basic mission success metrics are collected

### Milestone G - RL wrapper

Add:
- observation schema
- action encoding / masking
- reward function
- Gymnasium-compatible API

Exit criteria:
- the wrapper delegates all rules to the domain engine
- episodes are reproducible under fixed seeds
- invalid actions are masked or rejected cleanly

## Immediate design decisions to resolve

These should be treated as explicit planning tasks, not left to ad hoc coding.

Status after the current planning turn:
- D1 coordinate system / forward convention: resolved
- D2 domain decision granularity: resolved
- D3 Mission 1 config schema: resolved
- D4 replay / trace concept: resolved at planning level, implementation pending
- D5 hidden marker representation: resolved at planning level

### D1. Coordinate system and "forward"

Need:
- a hex coordinate system
- a stable interpretation of "forward" relative to the printed map
- a way to express river-blocked edges and bridges

Recommendation:
- use axial coordinates internally
- store mission metadata that identifies the three "forward" neighbors for the
  British side on that map orientation

### D2. Domain decision granularity

Need:
- a domain step model that can represent nested rule decisions faithfully

Recommendation:
- model explicit decision states such as:
  - choose British unit to activate
  - decide whether to keep / reroll a double
  - choose die result
  - choose order execution and parameters
  - choose next German unit to resolve

### D3. Mission config schema

Need:
- a schema that can encode both Mission 1 simplicity and later mission
  complexity without immediate redesign

Minimum fields:
- mission id
- roster
- map cells
- terrain
- blocked edges
- start hexes
- hidden markers
- pre-revealed enemies
- turn limit
- objective
- Orders Chart
- Enemy Unit Chart
- modifier table

### D4. Replay / trace format

Need:
- enough detail to replay deterministic trajectories and debug failures

Recommendation:
- store seed
- store every random draw with purpose
- store every chosen action / decision
- store major derived events (reveal, hit, morale change, kill, mission end)

### D5. Hidden state representation

Need:
- a clean model for unresolved `?` positions

Recommendation:
- model unresolved enemy markers as markers, not pre-sampled units
- sample the actual enemy result at reveal time from the mission chart

## Recommended source layout

The current repo docs already describe the mature structure.
The first useful code subset should be much smaller.

Start with:

```text
src/solo_wargame_ai/
  domain/
  io/
  agents/
```

First likely modules:

```text
domain/
  enums.py
  hexgrid.py
  terrain.py
  units.py
  state.py
  actions.py
  decision_context.py
  rng.py
  reveal.py
  combat.py
  german_fire.py
  resolver.py

io/
  mission_loader.py
  mission_schema.py
  replay.py

agents/
  random_agent.py
```

## Thread-sized backlog

These are the recommended first Codex tasks.
Each should be one thread or one tightly-scoped pair of threads.

### Phase 1 kickoff queue

1. Create the Python package skeleton under the existing project metadata and
   test tooling.
2. Implement hex coordinates, adjacency, and forward-neighbor helpers.
3. Implement the Mission 1 config loader.
4. Implement the first `GameState` and decision-context models.
5. Start the Mission 1 engine slice.

The detailed backlog below expands this kickoff queue.
`pyproject.toml` and `Makefile` already belong to the completed Phase 0/1
handoff, so the first remaining implementation step starts at `src/`.

### Package foundation

6. Create `src/solo_wargame_ai/` and the first package skeleton under the
   existing project metadata and test tooling.
7. Implement hex coordinates, adjacency, and forward-neighbor helpers.
8. Implement terrain / terrain modifier primitives.
9. Implement core enums for units, terrain, actions, morale, and decision
   phases.
10. Implement RNG wrapper with deterministic seeding and serializable state.

### Mission/state foundation

11. Implement mission models and loader for Mission 1 config.
12. Implement `GameState` and state validation.
13. Implement unresolved enemy marker representation.
14. Implement British unit activation bookkeeping.
15. Implement German unit facing and Fire Zone helpers.

### Mission 1 rule slice

16. Implement reveal resolution from adjacent movement.
17. Implement reveal resolution from Scout.
18. Implement British order-roll logic, including doubles and rerolls.
19. Implement die-result selection and legality checking.
20. Implement Advance order and cover reset behavior.
21. Implement Fire resolution.
22. Implement Grenade Attack resolution.
23. Implement Take Cover and Rally.
24. Implement Scout legality and execution.
25. Implement German activation ordering and attacks.
26. Implement morale transitions.
27. Implement Mission 1 terminal checks.
28. Implement text trace / replay for Mission 1.

### Mission 1 verification

29. Add unit tests for hex logic.
30. Add tests for doubles / reroll activation logic.
31. Add tests for Orders Chart lookup.
32. Add tests for reveal facing when found by movement.
33. Add tests for reveal facing when revealed by Scout.
34. Add tests for flanking modifier.
35. Add tests for support modifier.
36. Add tests for cover stacking and cover loss on movement.
37. Add tests for morale degradation and Rally.
38. Add an end-to-end deterministic Mission 1 replay test.

### Mission 3/4 extension

39. Transcribe Mission 3 or 4 config.
40. Add Building and Hill modifier support.
41. Add German Rifle Squad support.
42. Add regression tests proving Mission 1 behavior did not change.

### Mission 5/6 extension

43. Transcribe Mission 5 config.
44. Add MG Team unit type and chart handling.
45. Add support for multiple start hexes.
46. Add tests for mixed British roster behavior.

### Mission 7/9 extension

47. Transcribe Mission 7 config.
48. Add Mortar support logic.
49. Add PIAT targeting restrictions and building-ignore rule.
50. Add Half-Track pre-revealed placement and combat rules.
51. Add river-blocked edge representation and bridge exceptions.
52. Add Minefield reveal and repeated hit logic.
53. Add deterministic tests for each of the above.

### Mission 10/11 extension

54. Transcribe Mission 10 or 11 config.
55. Add Artillery unit behavior.
56. Add cover filtering for Artillery targeting.
57. Add tests for Artillery non-flankability and global attack pattern.

### Baselines and RL

58. Add random agent over legal actions.
59. Add first heuristic agent.
60. Add batch evaluation harness.
61. Define observation schema.
62. Define action encoding and legal-action mask.
63. Add Gym wrapper.
64. Add first reward design.
65. Run first baseline and RL experiments.

## Testing plan by stage

### Before Mission 1 is considered stable

Must have:
- hex-grid tests
- mission-loading tests
- activation-roll logic tests
- reveal tests
- legality tests
- combat tests
- morale tests
- deterministic replay test

### Before advanced units are considered stable

Must have:
- one focused test per advanced rule family
- at least one integration test using the first mission that introduces that
  family
- regression confirmation that earlier missions still behave correctly

## Documentation update policy

When a thread makes a stable decision, it should update the right layer:

- `ASSUMPTIONS.md` for explicit simplifications and interpretations
- public `docs/*.md` for durable behavior and architecture
- this file for task ordering / progress / next work

## Progress tracking policy

When a thread completes a backlog item from this file, it should:

1. mark the item as done in the thread response
2. note any follow-up tasks that changed
3. update public docs if the change settled an architecture question

If the completed work changes the build order, update this file before moving on.

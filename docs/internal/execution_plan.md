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
```

Defer `agents/`, `env/`, `eval/`, and `cli/` until the Mission 1 engine slice is
real enough that those packages have an immediate use.

First likely modules:

```text
domain/
  enums.py
  hexgrid.py
  terrain.py
  mission.py
  units.py
  state.py
  actions.py
  decision_context.py
  legal_actions.py
  rng.py
  reveal.py
  combat.py
  german_fire.py
  resolver.py
  validation.py

io/
  mission_loader.py
  mission_schema.py
  replay.py  # later in Phase 1, not in the bootstrap thread
```

## Detailed Phase 1 build stages

`pyproject.toml` and `Makefile` already belong to the completed Phase 0/1
handoff, so the first remaining implementation step starts at `src/`.

## Phase 1 master-plan usage

For Phase 1, this file is not only a backlog.
It is the **master execution plan** that a planning / dispatch / review thread
should keep current while implementation happens in separate threads.

Operational rules:
- implementation threads must move stage-by-stage in the order defined here
- do not start a dependent later stage while an earlier stage is still pending,
  in progress, or under review
- do not run dependent stages in parallel
- Stage 3 is architecture-sensitive and must run as:
  - Stage 3A = analysis-before-edit
  - Stage 3B = implementation
- after each completed stage, the master-thread should:
  - update the status block below
  - confirm whether exit criteria for that stage were actually met
  - identify the next commit-sized slice before the next implementation thread
    starts

Allowed status values:
- `pending`
- `in_progress`
- `completed`
- `blocked`

## Phase 1 status block

Update this block only from a planning / review / master-thread after checking
the repository state against the stage exit criteria.

- Stage 1: completed
- Stage 2: completed
- Stage 3A: completed
- Stage 3B: completed
- Stage 4: completed
- Stage 5: completed
- Stage 6A: completed
- Stage 6B: pending
- Stage 7: pending

The key constraint for Phase 1 is:
- model the written Mission 1 turn flow explicitly;
- keep static mission data separate from dynamic state;
- add tests in the same slice as the behavior they protect;
- avoid empty scaffolding outside the files that immediately support Mission 1.

### Stage 1 - Minimal package bootstrap and board primitives

Goal:
- create the smallest executable package surface needed for Mission 1
- lock the coordinate and RNG conventions before higher-level state exists

Deliverables:
- `src/solo_wargame_ai/__init__.py`
- `src/solo_wargame_ai/domain/__init__.py`
- `src/solo_wargame_ai/io/__init__.py`
- `src/solo_wargame_ai/domain/enums.py`
- `src/solo_wargame_ai/domain/hexgrid.py`
- `src/solo_wargame_ai/domain/terrain.py`
- `src/solo_wargame_ai/domain/rng.py`

Tests that should appear:
- `tests/test_hexgrid.py`
- `tests/test_rng.py`
- `tests/test_terrain.py` if terrain lookup is not trivial

Risks / traps:
- drifting away from the documented flat-top axial convention
- encoding British forward movement as a special-case hardcoded list instead of
  a reusable direction helper
- creating `agents/` or other future-facing packages before they are needed

Completion criteria:
- the package imports cleanly under the documented `src` layout
- axial adjacency and British-forward-neighbor helpers are tested
- RNG seeding and repeatability are tested

### Stage 2 - Mission 1 schema, loader, and static mission model

Goal:
- turn the Mission 1 TOML file into a validated in-memory mission definition
- keep runtime state concerns out of the loader

Deliverables:
- `src/solo_wargame_ai/domain/mission.py`
- `src/solo_wargame_ai/domain/validation.py`
- `src/solo_wargame_ai/io/mission_schema.py`
- `src/solo_wargame_ai/io/mission_loader.py`

Tests that should appear:
- `tests/test_mission_loader.py`
- `tests/test_mission_validation.py`

Validation coverage should include:
- duplicate ids
- invalid terrain or direction names
- missing Orders Chart rows for Mission 1 unit classes
- reveal-table gaps or overlaps
- hidden markers or start hexes on non-playable hexes

Risks / traps:
- hardcoding Mission 1 behavior directly into the loader instead of the domain
- merging setup-space data with dynamic `GameState`
- letting the loader depend on resolver or legality code

Completion criteria:
- Mission 1 loads deterministically from
  `configs/missions/mission_01_secure_the_woods_1.toml`
- the loaded mission object is validated and inspectable
- no dynamic turn/activation state is required to load a mission

### Stage 3 - Dynamic state, action schema, and decision-context contract

Dispatch rule:
- do not treat this as a single implementation thread
- execute it as:
  - Stage 3A: analysis-before-edit on the state/action/decision-context
    contract
  - Stage 3B: implementation of the agreed contract plus tests

Goal:
- define the runtime contract that all later legality and resolver code will
  use
- make staged Mission 1 decisions explicit before rule resolution is added

Deliverables:
- `src/solo_wargame_ai/domain/units.py`
- `src/solo_wargame_ai/domain/state.py`
- `src/solo_wargame_ai/domain/actions.py`
- `src/solo_wargame_ai/domain/decision_context.py`
- initial state construction from the loaded mission
- state validation helpers for Mission 1 invariants

Tests that should appear:
- `tests/test_initial_state.py`
- `tests/test_state_validation.py`
- `tests/test_decision_context.py`

Risks / traps:
- hiding pending decisions in resolver-local variables instead of state
- conflating order templates from the Orders Chart with concrete actions chosen
  by the player
- over-generalizing for later missions before Mission 1 state is proven
- treating hidden markers as pre-sampled units instead of unresolved markers

Completion criteria:
- the engine can create a valid initial Mission 1 state from the mission object
- the initial pending decision context is explicit
- activation bookkeeping, morale, cover, hidden markers, and revealed units are
  all representable without ad hoc side channels

### Stage 4 - British activation flow and legality engine

Goal:
- implement the staged British decision flow up to the point where a concrete
  order execution is chosen
- prove that legality is state-driven, not caller-driven

Deliverables:
- `src/solo_wargame_ai/domain/legal_actions.py`
- resolver support for:
  - choosing the next British unit
  - rolling 2d6 through the RNG wrapper
  - deciding keep vs reroll on doubles
  - selecting one die result or discarding both dice
  - choosing first order, second order, both, or no action under morale rules

Tests that should appear:
- `tests/test_activation_flow.py`
- `tests/test_order_chart_lookup.py`
- `tests/test_low_morale_constraints.py`

Risks / traps:
- silently auto-rerolling or auto-keeping doubles
- collapsing die choice and order choice into one macro decision
- letting legality depend on agent-side filtering instead of engine state
- forgetting that "discard both dice and do nothing" is legal

Completion criteria:
- from a valid state, the engine can enumerate only legal British activation
  flow actions
- low-morale restrictions are enforced by legality
- the state can advance from initial setup to a pending concrete order
  parameter decision without manual intervention

### Stage 5 - Positioning orders, support orders, and reveal mechanics

Goal:
- implement the non-attack Mission 1 orders and the reveal system they trigger
- make reveal behavior explicit rather than a side effect hidden in movement code

Deliverables:
- `src/solo_wargame_ai/domain/reveal.py`
- resolver support for:
  - `advance`
  - `take_cover`
  - `rally`
  - `scout`
  - reveal by movement
  - reveal by Scout
  - German facing assignment on reveal

Tests that should appear:
- `tests/test_advance_rules.py`
- `tests/test_cover_and_rally.py`
- `tests/test_reveal_rules.py`
- `tests/test_scout_rules.py`

Risks / traps:
- forgetting that only moving out of a hex removes accumulated Cover
- allowing Scout to bypass the exact-distance and facing-choice constraints
- resolving reveal as preloaded hidden content instead of sampling from the
  reveal table at reveal time
- mixing map mutation, reveal sampling, and state transition bookkeeping in one
  opaque function

Completion criteria:
- all non-attack Mission 1 orders execute through the resolver
- reveal-by-movement and reveal-by-Scout behave as documented
- reveal-facing rules are covered by tests

### Stage 6 - Combat, German phase, turn progression, and terminal checks

Goal:
- complete the first faithful playable Mission 1 engine slice
- close the loop from British phase through German phase to mission end

Deliverables:
- `src/solo_wargame_ai/domain/combat.py`
- `src/solo_wargame_ai/domain/german_fire.py`
- `src/solo_wargame_ai/domain/resolver.py`
- resolver support for:
  - British `fire`
  - British `grenade_attack`
  - combat modifier calculation
  - morale transitions
  - German activation ordering
  - German Fire Zone attacks
  - turn rollover and activation reset
  - Mission 1 terminal evaluation

Tests that should appear:
- `tests/test_combat_rules.py`
- `tests/test_german_phase.py`
- `tests/test_terminal_conditions.py`
- `tests/test_mission1_integration.py`

Risks / traps:
- applying Fire modifiers to grenade attacks
- evaluating German attacks without explicit player-chosen German activation
  order
- forgetting turn-boundary reset of activation bookkeeping
- checking terminal conditions at the wrong point in the flow

Completion criteria:
- Mission 1 can be played end-to-end using only legal actions
- British and German phases both progress through explicit decision contexts
- fixed seed plus fixed chosen actions produces a stable Mission 1 trajectory

### Stage 7 - Replay, text trace, and regression closure

Goal:
- make Mission 1 inspectable and regression-safe once the playable slice exists

Deliverables:
- `src/solo_wargame_ai/io/replay.py`
- optional thin manual-run entrypoint only if it directly exercises the engine
- event / trace objects sufficient to record:
  - random draws and their purposes
  - chosen actions
  - reveals
  - hits, morale changes, removals
  - mission end

Tests that should appear:
- `tests/test_replay_determinism.py`
- one end-to-end fixed-seed trace regression test if not already covered in
  `tests/test_mission1_integration.py`

Risks / traps:
- designing replay too early and forcing the resolver around it
- storing too little information to debug divergence
- coupling human-readable logging to core transition logic

Completion criteria:
- a short Mission 1 trace can be replayed deterministically
- the engine can emit a readable text log without direct state mutation
- replay/logging stays an adapter over the domain engine, not a second source of
  truth

## Recommended Codex thread slicing for Phase 1

The recommended thread order is:

1. Stage 1 only: package bootstrap plus `hexgrid` / `terrain` / `rng` and their
   tests.
2. Stage 2 only: mission schema, mission loader, validation, and loader tests.
3. Stage 3A only: analysis-before-edit for the state / actions /
   decision-context contract.
4. Stage 3B only: state, actions, decision context, initialization, and
   invariant tests.
5. Stage 4 only: British activation flow legality and tests.
6. Stage 5 only: `advance` / `take_cover` / `rally` / `scout` / reveal and
   tests.
7. Stage 6A: British combat and morale tests.
8. Stage 6B: German phase, terminal checks, and Mission 1 integration test.
9. Stage 7 only: replay / trace / manual run path after the engine behavior is
   already stable.

Do not mix these in one thread unless there is a very small cleanup:
- mission-schema changes with state/action redesign
- replay-format work with unresolved legality/resolver redesign
- German phase work with early package/bootstrap setup
- Mission 1 completion work with Mission 3+ extensions
- domain-engine work with agent or RL scaffolding

Master-thread checklist after each completed stage:
1. verify the completed thread against that stage's exit criteria
2. update the Phase 1 status block in this file
3. decide whether the result is one commit-sized slice or needs follow-up before
   commit
4. name the next stage-specific implementation thread explicitly

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

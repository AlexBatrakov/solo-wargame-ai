# Game Specification

## Purpose

This document translates the source rule material into an engineering-oriented specification for implementation.

It is not intended to restate the entire rulebook verbatim.
Instead, it defines the subset of rules and concepts that the codebase must represent and the conceptual boundaries of the first simulator versions.

This file should answer a simple question:
**what kind of game must the engine actually model?**

It is a public specification document, not a scratchpad.
Stable design decisions should be captured here at the level of concepts, while
lower-level private working notes can remain outside the public docs set.

---

## Scope of this specification

This document focuses on:
- the game as a software problem,
- the conceptual structure of play,
- the minimum elements that must exist in the simulator,
- the intended MVP subset,
- what is intentionally deferred.

This document does **not** attempt to fully define:
- the exact `GameState` schema,
- the exact action dataclasses,
- the RL observation format,
- the reward function,
- every advanced or optional rule from the source material.

Those details belong in more specific documents such as:
- `docs/state_model.md`
- `docs/action_model.md`
- `docs/mvp_mission_01_spec.md`
- `ASSUMPTIONS.md`
- later environment/evaluation docs

---

## Initial scope

The initial implementation scope is intentionally limited to an MVP scenario with a minimal subset of the rules.

The first playable target is **Mission 1 - Secure the Woods (1)** from the
rulebook.

The MVP should answer the following questions in executable form:
- What is the current game state?
- What actions are legal right now?
- How does the state change after a legal action?
- When does the mission end?
- What stochastic elements influence outcomes?

The project does **not** aim to begin with complete rulebook coverage.
It aims to begin with a small, trustworthy slice.

Important scope rule:
- when a rule is in scope, it should be modeled as written rather than silently
  simplified away;
- scope control should come from the mission ladder, not from flattening the
  written turn flow.

---

## Core game properties

The game is modeled as:
- turn-based,
- stochastic,
- tactical,
- mission-based,
- played on a hex grid,
- driven by constrained actions and rule-based outcomes.

Additional conceptual properties important for implementation:
- legality is state-dependent;
- the number of valid actions may vary from state to state;
- mission structure matters, rather than only local tactical choices;
- some parts of the simulator truth may not always be fully visible to the player or a future agent;
- random events are part of the rules and must be modeled explicitly rather than treated as external noise.

---

## Fundamental components

### Map
The map consists of hex cells with terrain properties.

At the conceptual level, the simulator must support:
- hex-based spatial relationships,
- terrain-dependent behavior,
- location-based legality and consequences,
- mission-specific layout.

The exact coordinate system is an implementation detail, but the engine must represent adjacency and movement consistently.

### Units
Units are entities that participate in the mission.

At the conceptual level, units have:
- side / ownership,
- type,
- position,
- alive / removed / otherwise active status,
- rule-relevant status information,
- action-relevant attributes.

Depending on the mission and implemented rules subset, status information may include things like morale, suppression, pinned state, or similar tactical constraints.

### Mission
A mission defines the scenario-specific structure of play.

A mission conceptually includes:
- map layout,
- initial friendly setup,
- hidden, scripted, or pre-placed opposing elements,
- mission objectives,
- turn limits or failure conditions,
- any scenario-specific rule modifiers required for that mission.

Mission-specific data should be separable from the general engine where practical.

### Turn structure
The game progresses in discrete turns.
Within a turn, there may be phases, sub-phases, or activation steps depending on the scenario and the implemented rule subset.

Exact sequencing should be represented explicitly in code rather than implied procedurally.

The engine should not rely on “magic control flow” that hides where the player is within a turn.
Turn progression is part of the game state.

For this specific rulebook, the turn structure includes player-visible staged
decisions such as:
- British unit activation order;
- doubles keep / reroll decisions;
- die-result selection;
- order execution sequencing;
- German activation order.

Those substeps are part of the modeled game, not merely UI details.

---

## Simulator viewpoint

The engine is expected to model the game from the perspective of full simulator truth.

This means the engine may internally know more than a player or future learning agent is allowed to observe.
That distinction is important for:
- hidden information,
- reveal mechanics,
- reproducibility,
- replay/debugging,
- future observation design.

Therefore, the simulator should conceptually distinguish between:
- **internal game truth**, and
- **externally exposed observation**.

The exact observation model is deferred, but the conceptual distinction belongs in the game specification.

---

## State transitions

At any moment, the simulator must be able to answer:

1. what actions are legal now;
2. what state results from each legal action;
3. whether the resulting state is terminal.

This implies several design requirements:
- legality must be derived from the current state;
- state transitions must be explicit;
- rule application should not depend on hidden ad hoc logic outside the engine;
- turn/phase progression must be reflected in the transition system;
- illegal actions should be rejectable in a clear and testable way.

The engine is the source of truth for legal actions.
Agents should not be expected to infer validity by trial and error.

The engine should therefore be able to expose legal choices not only at a broad
"turn" level, but at the specific current decision step inside the written turn
flow.

---

## Stochastic elements

The game includes randomness as part of its rules.
Typical random elements may include:
- dice resolution,
- hidden enemy reveal,
- combat outcomes,
- event generation where relevant.

All such randomness must be mediated by the project RNG interface.

This requirement exists to support:
- deterministic seeds,
- replayability,
- debugging,
- regression testing,
- fair comparison between agents.

Randomness is not an implementation nuisance.
It is part of the game dynamics and therefore part of the specification.

---

## Hidden information and delayed revelation

The game may contain information that is not immediately visible at all times.
Examples may include hidden enemies, latent mission elements, or reveal-triggered threats.

For specification purposes, this means:
- the engine may need to track hidden state internally;
- reveal behavior must be modeled as part of the rules;
- player-visible state and simulator state should not be assumed identical;
- the MVP may support only a simplified subset of these mechanics if needed.

The precise internal representation of hidden information is deferred to later design documents and implementation decisions.

---

## Victory and defeat

A mission ends when:
- a victory condition is achieved,
- a defeat condition is reached,
- a hard mission-ending constraint is violated.

Exact mission conditions belong in scenario configuration files or mission definitions rather than hardcoded general logic where avoidable.

At the conceptual level, the engine must support:
- mission-specific terminal conditions,
- state-dependent mission success/failure evaluation,
- deterministic checking of terminal conditions after transitions.

Victory and defeat are properties of mission state, not merely external labels attached after the fact.

---

## MVP subset

The MVP should include:
- Mission 1 only,
- one minimal map,
- one minimal set of unit types,
- the written Mission 1 decision flow,
- deterministic seeded playthrough support,
- legal-action generation,
- terminal condition checks,
- text/log output.

The MVP is expected to prove the following end-to-end path:
1. load a mission,
2. build an initial state,
3. generate legal actions,
4. apply actions through the engine,
5. advance the mission state,
6. detect terminal conditions,
7. produce a reproducible text-based run.

This is the first real success criterion for the simulator.

---

## Non-goals for MVP

The MVP does **not** require:
- complete rulebook coverage,
- a graphical interface,
- sophisticated visualization,
- broad mission coverage,
- advanced optimization for speed,
- RL training support,
- polished experiment infrastructure.

The project should resist expanding scope before the minimal playable engine is real and tested.

---

## Deferred content

The following may be added after MVP:
- more missions,
- advanced unit types,
- more nuanced hidden-information mechanics,
- richer combat resolution,
- broader mission scripting support,
- replay tooling,
- baseline search/planning agents,
- RL-oriented abstractions beyond the first environment wrapper.

Deferred does not mean unimportant.
It means these elements are not required to validate the first simulator slice.

---

## Relationship to other specifications

This file should remain conceptually aligned with:
- `docs/architecture.md`
- `docs/state_model.md`
- `docs/action_model.md`
- `docs/testing_strategy.md`
- `ASSUMPTIONS.md`

Rough division of responsibility:
- `game_spec.md` = what kind of game the engine must model
- `state_model.md` = what information belongs in state
- `action_model.md` = how decisions are represented
- `architecture.md` = how code should be organized
- `ASSUMPTIONS.md` = simplifications, ambiguities, and deferred decisions

If implementation choices begin to change the conceptual game being modeled, this file should be updated.

# State Model

## Purpose

This document defines what information belongs in the game state and how state should be conceptually organized.

A good state model is critical for:
- simulation correctness,
- legal action generation,
- reproducibility,
- debugging,
- replay support,
- observation design for RL.

This file should answer the question:
**what must the simulator know at any given moment in order to evolve the game correctly?**

It is a conceptual specification, not a final implementation schema.
The goal is to make the structure of simulator state explicit before code hardens around accidental modeling choices.

---

## Scope of this document

This document focuses on:
- the conceptual contents of `GameState`,
- the distinction between internal simulator truth and externally exposed information,
- top-level state categories,
- invariants the state should satisfy,
- the MVP preferences for state design.

This document does **not** fully define:
- exact Python dataclasses,
- storage optimization strategies,
- full serialization formats,
- final RL observation encoding,
- every mission-specific extension.

Those belong in implementation code and more specialized documents as the project evolves.

---

## Core design principle

`GameState` should contain the full simulator truth needed to evolve the game.

Observation given to an agent may later be a filtered, transformed, or partial view of this full state.

This distinction is foundational.
The engine should not be built around the assumption that "state" and "what the player sees" are always the same thing.

---

## High-level design goals for state

The state model should support the following properties:

1. **Correctness**
   The engine must be able to compute legal actions and apply rules without relying on information that lives outside the state.

2. **Explicitness**
   Important parts of the game situation should be represented explicitly rather than hidden inside control flow or temporary local variables.

3. **Deterministic reproducibility**
   Given the same initial state, same seed/RNG state, and same action sequence, the resulting trajectory should be reproducible.

4. **Debuggability**
   A state snapshot should be rich enough to understand why a transition occurred.

5. **Extensibility**
   The MVP state model should be easy to extend later with more rule detail, rather than requiring a full redesign.

6. **Separation from observation**
   Internal simulator truth should remain conceptually distinct from player-visible or agent-visible information.

---

## Proposed top-level state categories

The following categories describe the major conceptual components of `GameState`.

### 1. Mission metadata
Information that identifies the scenario and its constraints, such as:
- mission id,
- turn limit,
- objective definitions,
- scenario options,
- mission-specific rule toggles or variants if relevant.

Mission metadata answers the question:
**what scenario is this state currently part of?**

This information may be partly static, but some of it may need to be available during state evaluation, terminal checking, or logging.

### 2. Turn / phase state
Information required to know where in the game flow we are:
- current turn number,
- active side,
- current phase / subphase,
- currently active unit if relevant,
- remaining activations or action budget if relevant,
- currently pending decision context,
- any pending roll / roll-history information needed for the current activation,
- any partial order-resolution context that has not yet completed.

This category answers:
**where are we inside the mission flow right now?**

Turn progression should be represented as state, not hidden in driver logic.
For this game, explicit decision-context state is not optional bookkeeping.
It is part of faithfully representing the written rules.

### 3. Map state
Information about the board:
- hex cells,
- terrain properties,
- occupancy,
- revealed / unrevealed map elements where relevant,
- mission-specific map features if relevant.

At the conceptual level, map state answers:
**what exists on the board, and what is true about each relevant location?**

Some map properties may be static across the mission, while others may change over time.
The state model should support both, even if the first implementation keeps static map structure separate from more dynamic occupancy information.

### 4. Unit state
For each unit represented in the simulator, the state may include:
- unique id,
- side,
- unit type,
- position,
- alive / removed / otherwise active status,
- morale / suppression / pinned state if modeled,
- action-relevant flags,
- mission-specific flags if needed.

This document does not require that friendly and enemy units be stored in separate containers, but it does require that the simulator can distinguish:
- simulator-truth unit state,
- possibly player-visible unit state.

This category answers:
**what units exist, where are they, and what is their current tactical status?**

### 5. Enemy / opposition representation
Enemy state may include both:
- simulator-truth enemy representation,
- player-visible representation.

This distinction becomes important if the game includes hidden information, delayed reveal, or uncertain enemy identity.

In some implementations, enemy state may live inside the general unit collection plus auxiliary hidden-information structures.
In others, it may be partitioned more explicitly.

The exact storage design is open, but the conceptual distinction should remain clear.

### 6. Hidden information state
For missions with hidden content, the simulator may need:
- hidden markers,
- reveal status,
- latent enemy assignments,
- unrevealed map hazards,
- delayed or conditional mission events.

This category answers:
**what does the simulator know that is not necessarily visible externally yet?**

The presence of hidden-information state is one of the strongest reasons to keep simulator state separate from observation.

### 7. RNG state
To support exact replay and deterministic debugging, the simulator may store or serialize RNG state.

This category answers:
**what random-process state must be preserved so that future transitions remain reproducible?**

Depending on implementation, the project may store:
- a seed,
- a full RNG state,
- or a controlled RNG object whose state is serializable.

The exact mechanism is an implementation choice.
The requirement for reproducibility is the conceptual requirement.

### 8. Event / log / trace state
Optional but useful:
- accumulated event log,
- recent transition metadata,
- replay trace information,
- debug annotations.

This category answers:
**what auxiliary information helps explain or reproduce how the current state was reached?**

This is not always strictly necessary for minimal simulation correctness, but it is often extremely valuable for debugging and testing.

---

## Static vs dynamic state

Some information relevant to play may be static for the duration of a mission, while other information changes every step.

Conceptually useful distinction:

### Static or mostly static information
Examples:
- base map layout,
- terrain definitions,
- mission objective definitions,
- scenario parameters.

### Dynamic information
Examples:
- current turn,
- active unit,
- current positions,
- reveal status,
- morale/status effects,
- RNG progression,
- recent event history.

The implementation may choose to store some static information inside or outside `GameState` for engineering convenience.
However, the engine must still have access to all information needed to evaluate legality and transitions correctly.

---

## State invariants

The following should always hold for a valid state:

- no unit occupies an invalid hex;
- no two incompatible occupants share the same hex unless explicitly allowed;
- the active phase / subphase is consistent with the rest of the state;
- terminal states are internally consistent;
- legal actions depend only on the current valid state plus controlled RNG behavior;
- hidden-information bookkeeping is internally coherent;
- repeated runs with identical initial state, RNG state, and action sequence are reproducible.

As implementation evolves, more specific invariants should be added and tested.

---

## Internal truth vs agent observation

Important distinction:

- **Simulator state** = full internal truth.
- **Observation** = what an agent is allowed to see.

These should not be conflated.

Why this matters:
- hidden enemies may exist before they are revealed;
- mission triggers may be latent;
- replay/debug support may need full truth;
- future RL wrappers may expose only a filtered view of the state.

A common failure mode in game-engine design is to overfit the engine to the immediate observation layer.
This project should avoid that.

---

## MVP recommendation

For MVP, keep the state model:
- explicit,
- inspectable,
- verbose if needed,
- easy to validate,
- easy to serialize or log,
- easier to reason about than to optimize.

Clarity is more important than compactness.

The first state model should optimize for:
- trustworthy transitions,
- legal-action generation,
- deterministic debugging,
- ease of writing tests.

That includes enough turn/decision-context state to represent the Mission 1
activation flow without hiding rule-relevant substeps in outer driver code.

Compact encodings, memory optimization, and RL-specific state compression should be deferred until the domain model is stable.

---

## Questions intentionally left open

The following issues are intentionally not finalized in this document:

- whether friendly and enemy units should live in the same container;
- how hidden information should be encoded internally;
- whether `GameState` should own the full map object or reference a mission/static map structure;
- exactly how RNG state should be stored or serialized;
- exactly how much event history should be embedded in state versus kept in external replay/log structures.

These are important engineering decisions, but they should be resolved with implementation context rather than guessed too early.

---

## Relationship to other documents

This file should remain aligned with:
- `docs/game_spec.md`
- `docs/action_model.md`
- `docs/architecture.md`
- `docs/testing_strategy.md`
- `ASSUMPTIONS.md`

Rough division of responsibility:
- `game_spec.md` = what kind of game must be modeled
- `state_model.md` = what the simulator must know
- `action_model.md` = how decisions are represented
- `architecture.md` = where code responsibilities live
- `ASSUMPTIONS.md` = simplifications and unresolved decisions

If implementation starts depending on state information not conceptually justified here or in related docs, the design should be revisited.

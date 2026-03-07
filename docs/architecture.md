# Architecture

## Overview

The project is organized as a layered simulation and agent framework.

The architecture should support:
- rule-faithful game logic,
- deterministic testing,
- multiple agent types,
- later RL integration without contaminating core game logic.

## Design principles

1. **Domain logic first**
   The game engine must exist independently of any RL framework.

2. **Pure state transitions where possible**
   Rules should be implemented as explicit transitions from one state to another.

3. **Reproducible stochasticity**
   All randomness should flow through a controlled RNG interface.

4. **Legal action generation is first-class**
   The engine should explicitly generate legal actions rather than rely on agents to guess valid moves.

5. **Explicit decision-state modeling**
   If the written rules expose staged decisions, the domain layer should model those stages explicitly rather than collapsing them into hidden control flow.

6. **Layer separation**
   RL wrappers and agent policies must not be mixed into core game rule code.

## Proposed layers

### 1. Domain layer
Responsible for:
- game state representation,
- map / terrain / units,
- turn structure,
- decision contexts / activation substeps,
- rules and transitions,
- legality checks,
- mission setup,
- terminal conditions.

The domain layer should not depend on Gymnasium, PyTorch, or training code.

### 2. Environment layer
Responsible for:
- translating domain state into observations,
- translating agent actions into domain actions,
- optionally compressing staged domain decisions into a higher-level RL-facing
  interface if that proves useful later,
- legal action masks,
- reward calculation,
- `reset()` and `step()` interface.

### 3. Agents layer
Responsible for:
- random agent,
- heuristic agent,
- later search-based and learned agents.

Agents consume environment outputs or domain-readable interfaces, but should not mutate state directly.

### 4. Evaluation layer
Responsible for:
- batch simulation,
- metrics,
- benchmarking,
- experiment reports.

## Dependency rules

Preferred dependency direction:

`domain -> none`  
`env -> domain`  
`agents -> env and/or domain interfaces`  
`eval -> env + agents`

Forbidden or discouraged:
- domain importing RL or training libraries;
- agents directly changing internal state without action/resolver APIs;
- duplicated rule logic in agents or evaluation code.

## RNG policy

All stochastic events should use a project-controlled RNG wrapper.
This enables:
- deterministic seeds,
- replayability,
- testability,
- easier debugging.

## Initial implementation style

Preferred initial implementation:
- Python dataclasses or similarly lightweight models;
- explicit enums for action types, terrain types, unit types, statuses;
- explicit decision-context types for staged rule flow;
- explicit resolver functions for state transitions;
- tests written alongside each rule subsystem.

## Evolution plan

The architecture should remain stable as the project expands from:
- one mission,
- to several missions,
- to baseline agents,
- to RL training and evaluation.

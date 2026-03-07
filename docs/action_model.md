# Action Model

## Purpose

This document defines how game decisions are represented in code and how legal actions are generated.

This is one of the most important design choices in the project because action design directly affects:
- simulator correctness,
- legal-action generation,
- testability,
- baseline-agent design,
- RL environment complexity,
- and the eventual size and shape of the learning problem.

This file should answer the question:
**how should the simulator expose decision-making in a way that is faithful enough to the game, but still structured enough to implement and learn from?**

It is a conceptual design document, not a final Python API reference.

---

## Scope of this document

This document focuses on:
- the conceptual representation of actions,
- rule-faithful staged decisions in the domain layer,
- later RL-facing action compression tradeoffs,
- the lifecycle of a decision inside the engine,
- legal-action generation,
- invalid-action handling,
- action masking readiness for ML/RL.

This document does **not** fully define:
- exact Python dataclasses,
- exact enum names,
- the final RL policy interface,
- reward design,
- every mission-specific action extension.

Those belong in implementation code and more specialized environment or evaluation documents later.

---

## Why action design matters

The action model is not just a code-detail choice.
It determines:
- how difficult the simulator is to implement,
- how easy it is to verify legality,
- how much of the game flow is explicit versus hidden in the engine,
- how natural baseline agents will be,
- how large and irregular the future RL action space will become.

A poor action model can make even a simple game feel complicated in code.
A good action model can preserve clarity while keeping future extensions possible.

---

## Core design question

For this rulebook, the main design question is not simply "macro vs micro" in
the abstract.

The real question is:

**how closely should the domain engine mirror the written staged decision flow,
and where, if anywhere, should later action compression happen?**

---

## Initial decision

The current preferred direction is:

**Model the written decision flow explicitly in the domain engine.**

### Rationale

The written rules make several substeps strategically meaningful:
- choosing British unit activation order,
- deciding whether to keep or reroll doubles,
- choosing which die result to use,
- choosing whether to perform the first order, second order, or both in sequence,
- choosing German activation order.

Those are not accidental UI details.
They are part of the actual game logic.

Therefore:
- the domain engine should expose these staged decision points explicitly;
- legality should be generated for the current decision context;
- any later macro-action wrapper should be treated as an adapter on top of the
  domain engine rather than as the source of truth.

---

## Conceptual design goals for actions

The action model should support the following goals:

1. **Legality should be explicit**
   The engine should be able to enumerate or otherwise expose legal choices from the current state.

2. **Actions should be resolvable**
   An action should contain enough information for the engine to apply the corresponding transition cleanly.

3. **Actions should be testable**
   It should be possible to write focused tests for action generation and action resolution.

4. **Actions should be loggable and replayable**
   Action records should be suitable for debugging, replay traces, and deterministic regression tests.

5. **Actions should support future RL integration**
   The representation should not make legal-action masking or constrained action selection unnecessarily difficult.

6. **The action model should not overfit MVP so hard that later extension becomes awkward**
   The first model can be simple, but it should still leave room for additional action types and richer decision contexts.

---

## Domain staging vs later compression

### Rule-faithful staged domain decisions

In the domain layer, a decision should usually correspond to the current written
rule step.

Examples in this game:
- choose the next British unit to activate;
- choose whether to keep or reroll a double;
- choose which die result to use;
- choose the concrete execution of the available order sequence;
- choose the next German unit to resolve.

#### Advantages
- faithful to the written rules;
- clearer legality boundaries;
- easier replay/debugging;
- less hidden engine-side policy;
- safer foundation for later wrappers.

#### Risks
- more decision states;
- more bookkeeping in the domain layer;
- a less convenient first RL interface if exposed directly.

### Later environment-level macro compression

Once the domain engine is faithful and stable, the environment layer may later
choose to compress some staged domain decisions into larger RL-facing actions if
that can be justified clearly.

Examples of possible later compression:
- wrapping a whole British activation into one RL-facing action;
- replacing explicit keep/reroll handling with a higher-level policy adapter;
- using action templates or parameterized action heads instead of raw domain
  decisions.

#### Advantages
- smaller RL action spaces;
- easier integration with standard RL tooling;
- potentially faster experimentation later.

#### Risks
- hidden policy choices may leak into the wrapper;
- debugging becomes harder if the wrapper silently rewrites game flow;
- incorrect compression could distort the problem being learned.

---

## Current design preference

For the first playable simulator, the design preference is:

- use explicit staged domain decisions,
- keep the engine responsible for enumerating legal actions at the current
  decision context,
- keep action objects explicit and structured,
- avoid hiding rule-relevant substeps inside procedural driver logic.

This is a working preference, not an irreversible commitment.
If later evidence suggests that some of these staged decisions can be safely
compressed for RL, that compression should be added at the environment layer.

---

## Action requirements

Any action representation should:
- be serializable,
- be easy to validate,
- be easy to log and replay,
- encode enough information to resolve the transition,
- support legal-action masking or equivalent constrained selection,
- be stable enough to support tests,
- be readable enough for debugging.

An action object should be something the engine can reason about clearly, not just an opaque token unless later optimization makes that useful.

---

## Proposed conceptual action structure

An action should conceptually contain:
- action type,
- acting unit id where relevant,
- target hex and/or target unit where relevant,
- optional rule-specific parameters,
- decision-context information where needed to disambiguate staged rule flow.

Not every action needs every field.
The exact implementation may use:
- a tagged union style,
- dataclass variants,
- or a single structured action record with optional fields.

The important requirement is conceptual clarity.

---

## Action lifecycle inside the engine

At each decision point, the engine should:

1. inspect the current state;
2. determine what decision context currently applies;
3. generate all legal actions for that context;
4. expose those actions to the caller;
5. accept one selected action;
6. validate it against the current legal set or equivalent legality rules;
7. resolve the state transition;
8. update turn / phase / activation context;
9. check terminal conditions;
10. produce any event/log information needed for replay or debugging.

This lifecycle is important because it makes action handling an explicit engine process rather than scattered control logic.

---

## Decision context

Legal actions may depend not only on the whole state in a broad sense, but also on the current decision context.

Examples of contextual factors:
- active side,
- current phase,
- currently active unit,
- mission-specific pending choice,
- whether a reveal or resolution substep is in progress,
- whether the turn structure currently allows a support or end-step action.

The action model should therefore be understood as:
- **state-dependent**, and
- often **phase/context-dependent**.

This is one reason legal-action generation belongs in the engine.

---

## Legal action generation

Preferred policy:
- legal actions should normally be generated by the engine,
- legal-action generation should be treated as a first-class responsibility,
- legality should not be delegated to ad hoc agent-side guessing,
- legality rules should be testable independently of policy logic.

Why this matters:
- it improves correctness,
- it makes debugging easier,
- it reduces duplication,
- it supports action masking cleanly,
- it prevents agents from learning around engine bugs in unpredictable ways.

---

## Illegal actions

Preferred policy:
- illegal actions should not normally be proposed by the engine;
- if passed manually, they should raise a clear validation error or be rejected explicitly;
- illegal action handling should be deterministic and easy to test.

The project should avoid silent coercion of invalid actions into something else.
That kind of behavior makes debugging and RL evaluation much harder.

---

## Action masking and RL readiness

For ML/RL support, the environment should be able to expose a legal-action mask or an equivalent constrained action interface.

This is expected to be important because:
- the set of valid actions will vary by state,
- mission context may sharply constrain options,
- some actions may be structurally impossible in most states,
- naive flat action spaces may be extremely inefficient.

The domain engine should remain the source of truth for legality.
The environment layer may transform that legality information into whatever form an RL library requires.

---

## Replay and debugging considerations

Because actions are central to reproducibility, they should be suitable for:
- storing in replay traces,
- deterministic regression testing,
- human-readable debugging logs,
- baseline-agent analysis.

This strongly suggests that early action representations should favor clarity over compression.

---

## MVP recommendation

For MVP, the action model should be:
- explicit,
- relatively small,
- based on staged rule-faithful decisions,
- easy to enumerate,
- easy to validate,
- easy to serialize,
- easy to inspect in tests and logs.

The first action model should optimize for:
- end-to-end playability,
- written-rule fidelity,
- legal-action correctness,
- clean engine integration,
- later RL wrapping without forcing a domain redesign.

---

## Later wrapper examples

If a later RL wrapper uses higher-level actions, they may represent things like:
- complete a whole British activation with a selected unit and order plan;
- take a tactical support action;
- choose a higher-level movement/fire intent that expands into staged domain
  actions.

These examples are intentionally deferred.
They should not be treated as the domain-engine source of truth.

They are included only to acknowledge a possible future adapter layer.

---

## Questions intentionally left open

The following remain open:
- exact action schema;
- whether the RL wrapper should expose the staged domain decisions directly or
  introduce higher-level adapters;
- how to encode stochastic sub-decisions if player choice interacts with randomness;
- whether all future agents should use the same action abstraction;
- how much of phase management should be visible in the external action model;
- whether some rare decisions should be represented as special-case actions or handled as internal engine consequences.

These questions should be resolved with implementation evidence rather than guessed too early.

---

## Relationship to other documents

This file should remain aligned with:
- `docs/game_spec.md`
- `docs/state_model.md`
- `docs/architecture.md`
- `docs/testing_strategy.md`
- `ASSUMPTIONS.md`

Rough division of responsibility:
- `game_spec.md` = what kind of game is being modeled
- `state_model.md` = what the simulator must know
- `action_model.md` = how the simulator exposes decisions
- `architecture.md` = where the implementation responsibilities live
- `ASSUMPTIONS.md` = simplifications, ambiguities, and deferred decisions

If implementation begins forcing action choices that no longer fit the written
rule flow, this document should be revised rather than quietly bypassed.

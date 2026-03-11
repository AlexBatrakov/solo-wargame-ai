# Assumptions

This file records engineering assumptions, simplifications, deferred decisions, and rule interpretations made during development.

Its purpose is to prevent ambiguity from silently leaking into the implementation and to make scope decisions explicit before they become buried in code.

This file is not only for uncertain rules from the source material.
It is also for recording deliberate engineering choices made for the MVP, for reproducibility, for architecture, and for later ML / RL integration.

---

## Guiding principle

If the original rules are ambiguous, incomplete, inconvenient for simulation, or too broad for the current scope, the implementation may adopt a simplified rule interpretation.

Every such decision should be recorded here.

The project prefers:
- explicit simplification over hidden guesswork,
- documented scope limits over accidental partial implementation,
- stable public documentation over informal internal memory,
- narrow, testable assumptions over speculative generality.

---

## What belongs in this file

This file should capture assumptions of several kinds:

1. **Rule interpretation assumptions**
   When the source material can reasonably be interpreted in more than one way.

2. **MVP simplification assumptions**
   When a broader rule system is intentionally reduced to a smaller initial subset.

3. **Architecture-related assumptions**
   When the software representation of the game requires a deliberate modeling choice.

4. **Testing and reproducibility assumptions**
   When a feature must be constrained in a certain way to stay testable.

5. **RL-facing assumptions**
   When future agent/environment design may require abstraction choices that are not yet finalized.

---

## How this file should be used

- Add an entry whenever an implementation-relevant ambiguity is resolved.
- Add an entry whenever scope is intentionally narrowed.
- Add an entry whenever a design choice is made that could otherwise be mistaken for a faithful reading of the full rules.
- Update or retire entries when assumptions stop being provisional.
- If an assumption becomes part of stable project behavior, reflect it in the public docs under `docs/` as well.

This file is a registry of explicit decisions, not a scratchpad.

---

## MVP simplification policy

The MVP prioritizes:
1. correctness of the implemented subset,
2. reproducibility,
3. clean architecture,
4. testability,
5. clear extensibility.

The MVP does **not** attempt to implement every rule from the source material.

The MVP should prefer:
- one small mission over many shallowly implemented missions,
- one tested rules subset over broad but fragile coverage,
- a clean domain engine over early environment or RL code,
- explicit legal action generation over implicit assumptions in agent code.

---

## Current assumptions

### A1. First playable mission target
The first playable simulator target is **Mission 1 - Secure the Woods (1)**.

Rationale:
Mission 1 is the smallest scenario that still exercises the actual written game
loop: forward movement, reveal of hidden positions, German facing / Fire Zones,
combat, morale, Cover, Rally, Scout, turn limits, and mission-end checking.
Broader mission coverage is deferred until the core engine is trustworthy.

### A2. No GUI in MVP
The first versions are text-based only.

Rationale:
A GUI would add implementation surface area without helping the core questions of simulator correctness, action modeling, and agent interaction.

### A3. Engine before RL
RL support is intentionally postponed until the domain engine is stable and tested.

Rationale:
The main early risk is incorrect or poorly structured simulation logic, not lack of learning code.
A weak engine would make later RL results untrustworthy.

### A4. Public specs override internal notes
Any stable implementation decision should eventually be reflected in public documentation files under `docs/`.

Rationale:
Stable project truth should not exist only in internal planning files or private prompting context.

### A5. Engine-first responsibility for legality
Legal-action generation is assumed to be an engine responsibility, not an agent responsibility.

Rationale:
Agents should choose among valid actions, not infer the rules by trial and error.
This is important for correctness, testing, and later action masking.

### A6. Controlled randomness
All simulator randomness is assumed to flow through a project-controlled RNG interface.

Rationale:
This is required for deterministic seeds, debugging, reproducibility, and regression testing.

### A7. Simulator truth is richer than observation
The internal simulator state is assumed to be conceptually richer than what a future agent may observe.

Rationale:
This is important for hidden information, delayed reveal mechanics, replay/debugging support, and future RL environment design.

### A8. Domain-first architecture
Game rules are assumed to belong in the domain layer, not in scripts, notebooks, agents, or RL wrappers.

Rationale:
This preserves a single source of behavioral truth and reduces duplication.

### A9. Rulebook-first decision flow
If an in-scope rule presents a player-visible substep as a distinct decision, the
domain engine should model that substep explicitly rather than silently
compressing it away.

Rationale:
Scope control should come from limiting mission coverage, not from flattening
the written turn structure.
This is especially important in this game because activation order, doubles,
die-result selection, order sequencing, and German activation order all matter.

### A10. Map transcription convention
Printed maps are transcribed using flat-top axial coordinates with British
"forward" defined as the three map-up neighbor directions.

Rationale:
The simulator needs one stable coordinate convention before code and configs can
interoperate safely.
This is an engineering representation choice, not a claim that the printed
rulebook itself uses axial notation.

Current implementation fact:
- a playable hex may carry one or more terrain features in mission data
- the only accepted multi-terrain combination today is the bounded `woods +
  hill` case needed for Mission 3 wooded-hill hexes

Rationale:
This keeps Mission 3 rule semantics faithful without widening immediately into a
generic terrain-platform redesign.

### A11. Hidden markers are unresolved until reveal
Hidden enemy markers are represented as unresolved runtime markers and are
sampled from the mission reveal table only when a reveal event actually occurs.

Rationale:
This matches the accepted Mission 1 implementation and keeps hidden information
separate from revealed unit state.
It also preserves the distinction between simulator truth, player-visible
information, and replay/debugging behavior.

### A12. First env observation is structured and player-visible
The first accepted RL-facing observation is a structured Mission 1 view derived
from runtime state rather than a raw `GameState` export.

Rationale:
The accepted wrapper exposes the current decision context, public mission/map
data, British units, revealed German units, and unresolved marker positions,
while keeping RNG state and other simulator-only debugging fields out of the
observation boundary.

### A13. First env action surface uses fixed Mission 1 action ids
The first accepted RL-facing action interface is a fixed Mission 1 action
catalog that encodes the staged domain `GameAction` family directly.

Rationale:
This preserves the written staged decision flow, keeps legality owned by the
resolver, and avoids hiding doubles, activation-die choice, order sequencing,
or German activation order inside undocumented macro-actions.

### A14. First env reward and termination contract stays terminal-only
The first accepted env reward contract is terminal-only: victory `+1`, defeat
`-1`, and nonterminal states `0`.

Rationale:
Reward remains an env-layer concern, not a domain-layer concern. Mission
victory and mission defeat, including turn-limit defeat, map to
`terminated=True` and `truncated=False`; truncation is reserved for external
wrapper limits such as optional step caps.

---

## Open assumptions to resolve later

These are known decision areas that remain intentionally unresolved.
They should be revisited when implementation reaches the relevant subsystem.

### O1. Post-MVP mission ladder
The first mission target is fixed, but the exact extension order after Mission 1
may still need small adjustments if implementation evidence suggests a better
build path.

Current planning preference:
Mission 1 -> Missions 3-4 -> Missions 5-6 -> Missions 7-9 -> Missions 10-11.

Questions:
- Should Missions 3-4 definitely come before the MG-team missions?
- Are there any rule interactions that would justify pulling a later mechanic
  slightly earlier?

### O2. Future observation variants beyond the accepted wrapper
The first Mission 1 observation boundary is now resolved, but later alternative
observation families remain open.

Current implementation fact:
- hidden enemy markers are stored as unresolved markers, not as pre-sampled
  concealed units
- the accepted env observation exposes unresolved marker positions and revealed
  German units without exporting raw `GameState`

Questions:
- Should later learning code consume the current structured observation
  directly, or should it derive a flattened/tensorized representation from it?
- Should the project ever support an intentionally simulator-truth-rich
  debugging observation alongside the player-visible default?
- Which hidden-information details belong in replay/debugging traces but not in
  future agent observation?

### O3. Alternative action abstractions
The first RL-facing action abstraction is now resolved, but later alternatives
remain open.

Current implementation fact:
- the accepted Mission 1 wrapper uses a fixed action-id catalog over staged
  domain actions
- legality is still derived from `resolver.get_legal_actions(...)`

Questions:
- How much of the written turn structure can later be compressed for RL without
  distorting the game too much?
- If later experiments add macro-actions, how should they stay auditable
  against the accepted staged-action reference?

### O4. Reward shaping beyond the default contract
The default reward contract is now resolved, but later shaping choices remain
open.

Current implementation fact:
- the accepted default env reward is terminal-only
- Phase 3 evaluation metrics remain analysis/comparison signals, not reward
  terms

Questions:
- What minimal shaping is necessary to make early learning stable?
- How can shaping avoid teaching behavior that optimizes proxy rewards instead
  of mission success?
- Which evaluation metrics should remain separate from reward?

### O5. Advanced rules
Any complex optional, scenario-specific, or advanced rule is deferred unless needed for MVP mission fidelity.

Questions:
- Which rules are genuinely necessary for the first mission?
- Which rules can be stubbed conceptually without misleading future design?
- Which advanced rules most strongly affect the future state/action model and therefore should be considered earlier?

### O6. Learning-oriented observation representation
The first observation schema now exists, but the representation used directly
by future learning code is still unresolved.

Questions:
- Should the current structured observation remain the training interface, or
  should it be transformed into flattened/tensorized features?
- Which mission metadata should stay explicit versus being encoded into derived
  features?
- How should hidden information be masked consistently if multiple observation
  representations are introduced?

### O7. Replay granularity
The exact level of detail for replay traces is unresolved.

Questions:
- Should replay store only seed + actions?
- Should replay store intermediate derived events as well?
- What is the minimum useful trace for debugging vs regression testing?

---

## Deferred-by-policy assumptions

These are not unknown because they were overlooked.
They are intentionally postponed.

### D1. Performance optimization
No assumption is currently made that the early engine must be optimized for large-scale throughput.

Policy:
Correctness, inspectability, and determinism matter more than speed in the first implementation stages.

### D2. Broad config abstraction
No assumption is currently made that every part of the simulator must be config-driven from day one.

Policy:
Config files should be introduced where they provide immediate clarity, especially for missions.
Heavy generic config systems are deferred.

### D3. Search/planning integration
No assumption is currently made that search-based agents must be supported before a baseline simulation harness exists.

Policy:
Random and simple heuristic agents come first.
Search-based methods can be added later if the environment proves suitable.

### D4. Visualization
No assumption is currently made that map rendering or visualization is required before the simulator is playable and tested.

Policy:
Visualization is deferred until it clearly improves debugging, demonstration, or analysis enough to justify the extra complexity.

---

## Assumption lifecycle

Assumptions should move through the following lifecycle when possible:

1. **Open**
   A known unresolved decision area exists.

2. **Current assumption**
   A working decision has been made and is guiding implementation.

3. **Documented stable behavior**
   The decision is reflected in public docs and tested code.

4. **Revised or retired**
   The earlier assumption is replaced, narrowed, or no longer relevant.

When changing an important assumption, prefer updating the old entry instead of silently drifting away from it in code.

---

## Update rule

Whenever a new rule interpretation affects implementation, testing, environment design, or agent design, add it here.

Whenever a simplification is chosen for MVP scope control, add it here.

Whenever a provisional assumption becomes stable project behavior, also reflect it in the relevant public documentation under `docs/`.

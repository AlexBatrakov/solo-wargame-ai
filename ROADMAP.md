# Roadmap

This roadmap is intentionally detailed.
Its purpose is not only to track implementation, but also to preserve scope discipline, architectural intent, and the correct build order of the project.

Phases 0 through 6 are now complete by repository evidence.
They remain here as the historical build record.
Future work after Phase 6 is intentionally described later in this document as
a packet-based backlog rather than as a precommitted Phase 7 / Phase 8 / Phase
9 sequence.

The repository is expected to evolve in the following order:
1. planning and formalization,
2. domain engine,
3. testing and reproducibility,
4. baseline agents,
5. RL environment,
6. experiments and extensions.

The project should remain **engine-first**.
RL integration is important, but only after the simulator is sufficiently trustworthy and testable.

---

## Phase 0 — Planning and formalization

Goal: establish a strong source of truth before implementation begins, so that
later implementation is guided by explicit architecture, scope boundaries, and
formalized concepts rather than improvised code generation.

### 0.1 Repository and documentation setup

- [x] Create repository structure
- [x] Add rule reference materials
- [x] Create public documentation skeleton under `docs/`
- [x] Create internal documentation skeleton under `docs/internal/`
- [x] Ensure documentation layout matches the intended public/internal split
- [x] Add a basic `.gitignore` policy that supports internal docs, outputs, and local artifacts
- [x] Add initial Python project metadata files (`pyproject.toml`, `Makefile`, package skeleton plan) at the Phase 0/1 handoff
- [x] Decide which empty directories should exist now and which should be created later
- [x] Record the intended mature repository structure in internal docs

### 0.2 Public project-facing documentation

- [x] Write `README.md`
- [x] Write `ROADMAP.md`
- [x] Write `ASSUMPTIONS.md`
- [x] Write `docs/architecture.md`
- [x] Write `docs/game_spec.md`
- [x] Write `docs/state_model.md`
- [x] Write `docs/action_model.md`
- [x] Write `docs/testing_strategy.md`
- [x] Write `docs/development_workflow.md`
- [x] Add `docs/reference/README.md`
- [x] Ensure public docs are mutually consistent and do not contradict each other

### 0.3 Internal working documents for development workflow and execution

- [x] Create `docs/internal/repo_layout.md`
- [x] Create `docs/internal/codex_workflow.md`
- [x] Add `docs/internal/README.md`
- [x] Record the target repository layout and dependency boundaries
- [x] Record internal execution workflow rules
- [x] Record what belongs in public docs vs internal docs
- [x] Record how assumptions discovered during implementation should be promoted into public documentation
- [x] Record what kinds of changes require architecture review before coding

### 0.4 Formalization of the game as a software problem

- [x] Identify the minimum viable playable scope for the first simulator version
- [x] Lock the MVP mission / scenario target to Mission 1 - Secure the Woods (1)
- [x] Decide the initial subset of unit types to support
- [x] Decide the initial subset of terrain types to support
- [x] Decide the initial subset of actions to support
- [x] Decide which advanced rules are explicitly out of scope for MVP
- [x] Translate the game from rulebook language into software-oriented concepts
- [x] Define what counts as a legal game state
- [x] Define what counts as a legal action
- [x] Define what counts as a terminal state
- [x] Define what counts as a mission objective in code terms
- [x] Identify all stochastic elements relevant to MVP
- [x] Identify all hidden-information elements relevant to MVP
- [x] Separate simulator truth from player-visible information conceptually

### 0.5 State, action, and turn-structure design

- [x] Define the top-level `GameState` concept
- [x] Define the mission metadata needed inside state
- [x] Define turn / phase / subphase representation
- [x] Define how map state should be represented conceptually
- [x] Define how unit state should be represented conceptually
- [x] Define how hidden state should be represented conceptually
- [x] Define the distinction between internal state and observation
- [x] Decide that the domain engine models the written staged decision flow and defer any later macro compression to the environment layer
- [x] Define the conceptual action schema for MVP
- [x] Define legal-action generation as a first-class engine responsibility
- [x] Define the lifecycle of a single decision step
- [x] Define how turn progression should be modeled
- [x] Define how RNG interacts with state transitions

### 0.6 Scope-control and simplification policy

- [x] Explicitly state that MVP does not require full rulebook coverage
- [x] Explicitly state that MVP does not require GUI or visualization
- [x] Explicitly state that MVP does not require RL code
- [x] Explicitly state that MVP does not require performance optimization beyond correctness and repeatability
- [x] Record the principle that the engine should be built before environment wrappers
- [x] Record the principle that legal-action generation should come from the engine, not the agent
- [x] Record the principle that ambiguous rules must be documented rather than silently guessed
- [x] Record the principle that rule logic belongs in `domain/`
- [x] Record the principle that scripts and notebooks should remain thin

### 0.7 Reproducibility and testing philosophy before coding

- [x] Decide that simulator randomness must be controlled via a project RNG interface
- [x] Decide that deterministic seeds must be supported from early development
- [x] Decide how replayability should be handled conceptually
- [x] Define what types of tests will be required for MVP
- [x] Define which invariants should be enforced by tests
- [x] Define what types of regression tests may be useful later
- [x] Define what types of config loading need validation tests
- [x] Record that stochastic features must remain testable under fixed seeds

### 0.8 Execution operating rules before implementation begins

- [x] Define the preferred task granularity for implementation work
- [x] Define the rule that work should proceed in narrow, testable slices
- [x] Define when analysis should happen before code changes
- [x] Define when architecture may be changed and when it may not
- [x] Define how ambiguity in the rule source should be handled
- [x] Define the expectation that nontrivial rule changes require tests
- [x] Define the expectation that stable implementation decisions should update docs
- [x] Define the expectation that unrelated refactors should be avoided

### 0.9 Exit criteria for Phase 0

Phase 0 should be considered complete only when:

- [x] public docs exist and are internally coherent
- [x] internal docs exist and describe both layout and workflow
- [x] the MVP scope is explicitly limited
- [x] the initial state model is conceptually defined
- [x] the initial action model is conceptually defined
- [x] the repository structure strategy is documented
- [x] Phase 0/1 handoff metadata exists (`pyproject.toml`, `Makefile`)
- [x] the testing philosophy is documented
- [x] the implementation workflow is documented
- [x] the next implementation slice is obvious and small enough to execute safely

Status note: the planning and formalization work is complete enough to hand off
to Phase 1 implementation threads without requiring more architectural
invention first.

---

## Phase 1 — MVP domain engine

Goal: build a minimal but reliable simulator for a single mission, with explicit state transitions, deterministic randomness, and a domain layer that can later support both baseline agents and RL wrappers.

Status note: Phase 1 implementation is complete in the repository. Mission 1 is
playable through the accepted resolver path, covered by deterministic tests,
and replayable through structured text traces.

Focused tests should already start appearing during Phase 1 whenever a slice
adds nontrivial rule behavior.
Phase 2 expands that into broader coverage, regression support, and
reproducibility discipline; it does not mean "start testing only after the
engine exists."

### 1.1 Package and module skeleton

- [x] Create `src/solo_wargame_ai/`
- [x] Create initial `domain/` package
- [x] Create initial `io/` package
- [x] Confirm that the first playable slice does not yet require `agents/` or `utils/` packages
- [x] Add `__init__.py` files where appropriate
- [x] Ensure package layout matches documented architecture

### 1.2 Core domain primitives

- [x] Implement hex-grid coordinates and neighbors
- [x] Implement terrain representation
- [x] Implement core enums (unit types, terrain types, action types, statuses, phases if needed)
- [x] Implement base unit dataclasses / models
- [x] Implement base mission / scenario models
- [x] Implement action dataclasses / models
- [x] Implement explicit decision-context / pending-choice models for the staged turn flow
- [x] Implement RNG wrapper with deterministic seeding

### 1.3 Game state and flow

- [x] Implement `GameState`
- [x] Implement mission metadata in state
- [x] Implement map state representation
- [x] Implement unit collections and indexing strategy
- [x] Implement turn / phase structure
- [x] Implement state validation helpers if needed
- [x] Implement terminal conditions

### 1.4 Mission loading and initialization

- [x] Implement scenario / mission loading
- [x] Define mission config format for the first playable scenario
- [x] Validate mission loading against config expectations
- [x] Implement initial state creation from mission data
- [x] Ensure first mission can be initialized deterministically

### 1.5 Action generation and resolution

- [x] Implement legal action generation for MVP actions
- [x] Implement action validation
- [x] Implement state transition resolver
- [x] Implement movement resolution
- [x] Implement first-pass combat resolution
- [x] Implement morale / status change resolution if required by MVP
- [x] Implement hidden-information / reveal handling if required by MVP
- [x] Ensure illegal actions are rejected cleanly

### 1.6 Playable text-based slice

- [x] Implement readable text trace / replay output for the playable slice
- [x] Implement minimal event/log output
- [x] Implement one deterministic playable trace
- [x] Ensure a single mission can be progressed through multiple steps without manual state editing

### 1.7 Exit criteria for Phase 1

- [x] one mission can be loaded
- [x] initial state can be built deterministically
- [x] legal actions can be generated
- [x] chosen actions can be applied through the engine
- [x] state progresses correctly across turns/phases for the MVP slice
- [x] terminal conditions can be detected
- [x] the simulator can produce a text-based playable run

---

## Phase 2 — Testing and reproducibility

Goal: make the simulator trustworthy enough to refactor and extend without losing correctness.

Status note: the focused Phase 2 hardening cycle is complete in the repository.
Engine contract hardening, replay/reproducibility hardening, and the minimal CI
gate have all landed.

### 2.1 Unit tests for primitives

- [x] Unit tests for grid logic
- [x] Unit tests for terrain behavior / lookup
- [ ] Unit tests for enum-driven validation if useful
- [x] Unit tests for RNG determinism

### 2.2 State and loading tests

- [x] Unit tests for mission loading
- [x] Unit tests for initial state creation
- [x] Unit tests for state invariants
- [x] Validation tests for malformed mission configs

### 2.3 Rule and transition tests

- [x] Unit tests for legal action generation
- [x] Unit tests for staged decision-context progression and German activation ordering
- [x] Unit tests for movement resolution
- [x] Unit tests for combat resolution
- [x] Unit tests for morale / status changes
- [x] Unit tests for hidden-information / reveal behavior if applicable
- [x] Unit tests for terminal / victory conditions

### 2.4 Reproducibility and regression support

- [x] Replay format for complete game traces
- [x] Seed-based reproducibility tests
- [x] Deterministic short-trace regression tests
- [x] Ensure fixed seed + fixed actions produce stable outcomes

### 2.5 Exit criteria for Phase 2

- [x] core domain primitives are tested
- [x] the first mission load path is tested
- [x] key state transitions are tested
- [x] deterministic seeded execution is verified
- [x] the simulator is safe enough to extend without blind refactoring

Closeout note: Phase 2 is formally complete; the next macro-step is Phase 3
baselines.

---

## Phase 3 — Baseline agents

Goal: add simple non-learning agents to validate the usefulness of the environment and provide comparison baselines before RL.

Status note: Phase 3 is complete in the repository. The accepted slice now
includes a minimal agent contract, random and heuristic Mission 1 baselines, a
fixed-seed evaluation harness and benchmark protocol, and a thin manual CLI for
smoke / benchmark reruns.

### 3.1 Agent interfaces and simple policies

- [x] Define a minimal agent interface if needed
- [x] Implement Random agent
- [x] Implement first Heuristic agent
- [x] Ensure agents consume legal actions rather than mutating state directly

### 3.2 Simulation harness and metrics

- [x] Implement batch simulation script
- [x] Implement evaluation metrics
- [x] Decide which metrics matter most for early comparison
- [x] Define a fixed evaluation seed set / benchmark protocol for agent comparisons
- [x] Implement baseline comparison report

### 3.3 Baseline validation

- [x] Compare random vs heuristic behavior
- [x] Verify that baseline agents can complete full episodes in the MVP slice
- [x] Identify obvious failure modes before RL integration

### 3.4 Exit criteria for Phase 3

- [x] at least one nontrivial baseline agent exists
- [x] agents can run many episodes automatically
- [x] basic metrics can be computed and compared
- [x] there is a baseline performance reference before RL work starts

Closeout note: the accepted 200-seed Mission 1 benchmark now records a clear
baseline gap before RL work begins, with `random` at 11/200 wins and
`heuristic` at 157/200 wins. The next macro-step is Phase 4 RL-environment
planning rather than more Phase 3 delivery slices.

---

## Phase 4 — RL environment

Goal: expose the accepted Mission 1 engine through a minimal RL-friendly
wrapper without contaminating the domain layer or discarding the accepted
Phase 3 baseline / benchmark surface.

Status note: the first Mission 1 RL-friendly wrapper is now implemented in the
repository. Phase 4 closeout should focus on preserving the accepted operator
surface and Phase 3 comparison path rather than reopening wrapper-boundary
questions.

### 4.1 Wrapper contract and boundary decisions

- [x] Decide the first observation boundary and document whether it is
      player-visible, full-state, or another explicitly justified view
- [x] Ensure the observation shape is conditioned on the current staged
      decision context
- [x] Decide the first RL-facing action exposure around the staged domain
      decisions
- [x] Decide how legal actions are surfaced to RL code
- [x] Freeze the first reward contract, keeping terminal mission outcome as the
      anchor and any shaping explicit
- [x] Decide `terminated` vs `truncated` semantics for mission completion and
      turn-limit defeat
- [x] Preserve compatibility with the accepted Phase 3 benchmark/reference path

### 4.2 Wrapper implementation

- [x] Implement observation encoding
- [x] Implement action encoding
- [x] Implement legal-action masking or equivalent constrained-action support
- [x] Implement a dependency-free Gym-style wrapper
- [x] Implement any required action adapter on top of the staged domain engine
      without redefining rules
- [x] Ensure the wrapper delegates actual rules to the domain engine
- [x] Verify deterministic seeded resets / episodes where appropriate

### 4.3 RL usability checks

- [x] Verify that the environment can run complete Mission 1 episodes through
      `reset` / `step`
- [x] Verify that invalid actions are masked or rejected correctly
- [x] Verify that reward signals are documented and testable
- [x] Verify that seeded rollouts are reproducible enough for debugging and
      comparison
- [x] Verify that the wrapper does not silently leak simulator-only truth unless
      that choice is explicitly documented

### 4.4 Exit criteria for Phase 4

- [x] the simulator is exposed through a clean Mission-1 RL-friendly interface
- [x] observation, action, legality, and reward contracts are documented
      explicitly
- [x] the wrapper can run deterministic seeded episodes without redefining game
      rules
- [x] the accepted Phase 3 baseline surface remains usable as the comparison
      reference for later RL work

Closeout note: the accepted manual Phase 4 env smoke command is
`.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`, and the
preserved Phase 3 comparison reference remains
`.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke` /
`.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode benchmark`.

---

## Phase 5 — Learning experiments

Goal: run the first end-to-end learning experiments on the accepted Mission 1
wrapper and learn whether the current environment/action design is actually
usable.

Status note: Phase 5 is complete in the repository. The accepted slice now
includes a bounded masked actor-critic training/evaluation path, preserved
Phase 3 anchor comparison, explicit seed separation, and an external-audit-
confirmed decision not to open Package C.

### 5.1 First training loop

- [x] Select and document one narrow first RL baseline / training setup
- [x] Define experiment configuration, seed policy, and local run protocol for
      early RL runs
- [x] Record how evaluation is compared against the accepted Phase 3 baselines
- [x] Decide what counts as a minimally successful first learning result

### 5.2 Evaluation and comparison

- [x] Run at least one end-to-end training / evaluation cycle
- [x] Evaluate against random and heuristic agents
- [x] Analyze failure modes and sample-efficiency problems
- [x] Evaluate whether the chosen RL-facing action abstraction is helping or hurting learning
- [x] Refine reward design only if experiments justify it explicitly
- [x] Record which limitations come from engine scope vs RL method choice

### 5.3 Decision gate after the first RL pass

- [x] Decide whether the next major investment should be environment iteration,
      stronger baselines, or Mission 3/4 content extension
- [x] Decide whether Mission 1 is a sufficient learning target or now too small
      / degenerate
- [x] Record the recommended next macro-step in the docs

### 5.4 Exit criteria for Phase 5

- [x] at least one RL experiment has been run end-to-end
- [x] RL performance has been compared against the accepted baselines
- [x] the project has a documented recommendation for what to do after the
      first RL pass

Closeout note: Phase 5 demonstrated terminal-only learnability on the accepted
Mission 1 wrapper without opening Package C. The accepted aggregate result is
`101 -> 144/200`, `202 -> 133/200`, `303 -> 121/200`, with `133/200` median
wins against the preserved anchors `random` `11/200` and `heuristic`
`157/200`. The next macro-step is stronger baselines/search planning rather
than more Phase 5 delivery work, environment iteration, or Mission 3/4 content
extension.

---

## Phase 6 — Post-first-RL strengthening

Goal: use the accepted Mission 1 engine, wrapper, baselines, and first learner
result to answer the next high-value questions before widening content:
1. how much headroom still exists on Mission 1 for stronger non-learning
   baselines / search;
2. which repository-structure and naming issues should be cleaned up now so the
   next research/content cycle is easier to work on.

Status note: Phase 6 is complete in the repository. Accepted Delivery A cleaned
up the most immediate durable naming/layout friction, and accepted Delivery B
added a bounded stronger rollout baseline that reached `195/200` wins on the
preserved benchmark. Package C was not opened. A later strategic review
concluded that Mission 1 is now close enough to saturated for default planning
purposes, so the next recommended packet is no longer another Mission 1
strengthening cycle but a bounded Mission 3 content-extension slice with only
the structural prep it directly needs.

### 6.1 Repository hygiene and naming cleanup

- [x] Rename durable `src/` modules by responsibility rather than phase history
      where practical
- [x] Keep phase-based naming only where it is genuinely useful, such as thin
      operator commands, milestone docs, or archived artifacts
- [x] Reorganize `tests/` into clearer subsystem-oriented groups if that
      improves navigation and future maintenance
- [x] Reduce mixed or confusing naming in `agents/`, `eval/`, and `cli/`
      without changing accepted behavior
- [x] Update repository-layout docs if structural cleanup changes the intended
      long-lived package organization

### 6.2 Stronger baselines and search track

- [x] Add at least one stronger non-learning baseline, search baseline, or
      planning-style baseline on Mission 1
- [x] Compare stronger baselines against the preserved `random`, `heuristic`,
      and accepted Phase 5 learned-policy references
- [x] Determine how much Mission 1 headroom remains above the current best
      learned result
- [x] Record whether stronger baselines/search change the recommendation about
      Mission 3/4 timing

### 6.3 Comparative evaluation and decision gate

- [x] Improve comparison reporting only as needed to answer the stronger-
      baseline question cleanly
- [x] Record whether Mission 1 now looks strategically saturated or still
      informative
- [x] Decide whether the next major investment after Phase 6 should be:
      stronger baselines/search iteration,
      Mission 3/4 content extension,
      or targeted environment/action iteration

### 6.4 Deferred maintainability and scaling work

- [ ] Revisit `legal_actions.py` structure before major rule / content growth
- [ ] Revisit replay draw-prediction coupling before adding more RNG-heavy
      mechanics
- [ ] Introduce synthetic fixtures if new content/testing work needs them
- [ ] Consider tooling upgrades such as `mypy`, Python 3.12 CI, broader Ruff,
      or coverage if they clearly pay for themselves

### 6.5 Exit criteria for Phase 6

- [x] at least one stronger post-Phase-5 baseline/search result exists
- [x] the repository structure is cleaner and easier to extend than it was at
      the start of the phase
- [x] the project has a documented recommendation for the next macro-step after
      the Mission 1 strengthening pass

Closeout note: Phase 6 confirmed that Mission 1 still has substantial headroom.
The accepted stronger rollout baseline reached `195/200` benchmark wins versus
the preserved heuristic anchor `157/200` and accepted learned best `144/200`,
while the bounded repository-hygiene slice removed the most immediate durable
naming friction. A subsequent post-Phase-6 strategic review concluded that this
new result actually lowers the value of another Mission 1 strengthening cycle:
the better next investment was a bounded Mission 3 vertical slice plus minimal
structural prep, so the architecture was tested against richer content rather
than optimized further on the near-solved Mission 1 slice.

That next packet has now landed as well:
- Mission 3 is now a deterministic resolver-playable and replayable slice;
- bounded support for Building, Hill, wooded-hill semantics, and German Rifle
  Squad behavior is in place;
- the subsequent Mission 3 baselines/search packet has also landed and produced
  a first accepted Mission 3 comparison surface.

### Completed packets since the original phase roadmap

- [x] **Mission 3 vertical slice + minimal structural prep**
  Closed as a bounded packet after Phase 6.
  Outcome:
  - Mission 3 config transcription landed;
  - the domain engine now supports Building, Hill, bounded wooded-hill
    semantics, and German Rifle Squad behavior;
  - Mission 3 can be loaded, initialized, played, and replayed deterministically
    through the accepted resolver path;
  - the packet stayed out of env/RL/baseline/search follow-on work.
- [x] **Mission 3 baselines/search re-establishment**
  Closed as a bounded follow-on packet after the Mission 3 vertical slice.
  Outcome:
  - a Mission-3-only comparison surface landed for `random`, `heuristic`, and
    `rollout-search`;
  - accepted Mission 3 references were established at
    `random 0/200`, `heuristic 72/200`, `rollout-search 105/200`;
  - preserved Mission 1 anchors remained explicit and unchanged;
  - the packet stayed out of env/wrapper, learning, Mission 4 content, and
    generic cross-mission platform work.
- [x] **Mission 3 search strengthening**
  Closed as a bounded follow-on packet after Mission 3
  baselines/search re-establishment.
  Outcome:
  - the preserved historical Mission 3 comparison surface remained explicit;
  - one bounded strengthened Mission-3-local search result landed at
    `rollout-search-strengthened 171/200`;
  - the packet stayed out of env/wrapper, learning, Mission 4 content, and
    generic search/reporting platform work;
  - the default next step moved to Mission 3 env/wrapper extension rather than
    another search packet.

### Current planning pause

After the Mission 3 search-strengthening closeout, additional audit and
brainstorm work changed the preferred sequencing slightly:

- no big top-level repository reorg is needed;
- the macro split `domain / io / env / agents / eval / cli` still looks right;
- the highest-value immediate work is now a **small preparatory packet** before
  Mission 3 env work, not a broad redesign and not another default Mission 3
  tuning loop;
- the main reasons are:
  - recent mission-config/schema hardening findings are real;
  - the env layer should grow through a narrow shared adapter seam rather than
    by turning `Mission1Env` into the permanent center or creating a second
    isolated `MissionXEnv` island.

---

## Post-Phase-6 Planning Model

The original six-phase roadmap is now complete.

From this point onward, the project should prefer a **rolling packet-based
roadmap** rather than precommitting to Phase 7 / Phase 8 / Phase 9.
Each new packet should define:

- a bounded goal;
- explicit scope and non-goals;
- concrete deliverables;
- completion criteria;
- the decision gate it is expected to clarify.

The current default should be to let richer content drive the next design
questions instead of spending more cycles on Mission 1 alone.

### Recommended next packet

**Mission 3 env-prep hardening and adapter seam**

Goal:
- make one bounded preparatory pass before Mission 3 env/wrapper work.

Scope:
- strengthen mission-config/schema semantics where recent audits found real
  gaps;
- carve a narrow shared resolver-backed env-adapter seam so Mission 3 env work
  does not become another isolated wrapper stack;
- preserve both the historical Mission 3 references and the accepted
  strengthened local search result as comparison truth;
- allow only the smallest env/eval export cleanup that directly supports that
  seam.

Non-goals:
- no broad repo reorganization;
- no Mission 3 wrapper implementation yet;
- no Mission 3 learning experiments yet;
- no Mission 4 content landing yet;
- no generic multi-mission env/reporting/search platform buildout;
- no reopening of Mission 3 search strengthening by default.

Completion criteria:
- the mission loader/validation boundary is stricter and less misleading than
  it is today;
- the project has one narrow shared env-extension seam ready for Mission 3
  wrapper work without committing to a broad env-platform shape;
- preserved Mission 1 anchors plus preserved historical and strengthened
  Mission 3 references remain explicit and separate.

### Likely follow-on packets after that

1. **Mission 3 env/wrapper extension**
   Extend the accepted env boundary only as far as the new slice requires.
2. **Mission 3 learning experiments**
   Re-test learnability on content that is materially richer than Mission 1.
3. **Cross-mission comparison and reporting**
   Add only the evaluation/reporting support needed once more than one mission
   is active.
4. **Mission 4 or another bounded richer content slice**
   Continue content growth only after the Mission 3 stack is healthier.

### Ranked future backlog

#### Highest-value backlog

1. Mission 3 env-prep hardening and adapter seam
2. Mission 3 env/wrapper extension
3. Mission 3 learning experiments

#### Medium-value backlog

1. Mission 4 or another bounded richer content slice once the Mission 3 env
   and learning path are healthier
2. A narrow search-transfer/localization follow-up only if a later thread opens
   that as a new explicit question rather than more tuning
3. Observation/action redesign only if richer content shows the accepted
   wrapper is too Mission-1-shaped
4. Synthetic fixtures and bounded maintainability refactors ahead of broader
   multi-mission growth
5. Better evaluation, reporting, and replay-assisted debugging once more than
   one mission is active

#### Lower-priority / opportunistic backlog

1. Additional Mission 1 strengthening only if a very specific research question
   remains after the Mission 3 pivot
2. Another default Mission 3 search packet without a clearly different question
3. Wider tooling upgrades such as `mypy`, Python 3.12 CI, broader Ruff, or
   coverage-driven cleanup
4. Generic config / artifact / experiment-platform buildout if repeated manual
   work starts to dominate progress
5. Additional framework compatibility layers, richer operator UX, or optional
   visualization/debug views

---

## Guiding constraints across all phases

These constraints apply throughout the roadmap:

- [ ] keep the project engine-first
- [ ] avoid premature RL scaffolding
- [ ] avoid overengineering before the first playable slice exists
- [ ] keep rule logic inside the domain layer
- [ ] keep assumptions documented
- [ ] keep tests growing with rule complexity
- [ ] prefer deterministic and reproducible workflows
- [ ] prefer small, bounded tasks over broad autogenerated rewrites

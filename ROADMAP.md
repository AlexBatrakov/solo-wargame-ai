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
- [x] Create a local working-notes skeleton
- [x] Ensure documentation layout matches the intended public/private split
- [x] Add a basic `.gitignore` policy that supports local notes, outputs, and local artifacts
- [x] Add initial Python project metadata files (`pyproject.toml`, `Makefile`, package skeleton plan) at the Phase 0/1 handoff
- [x] Decide which empty directories should exist now and which should be created later
- [x] Record the intended mature repository structure in local working notes

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

### 0.3 Local working notes for development workflow and execution

- [x] Create a local repo-layout note
- [x] Create a local workflow note set
- [x] Add a local working-docs index
- [x] Record the target repository layout and dependency boundaries
- [x] Record internal execution workflow rules
- [x] Record what belongs in public docs vs local working notes
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
- [x] local working notes exist and describe both layout and workflow
- [x] the MVP scope is explicitly limited
- [x] the initial state model is conceptually defined
- [x] the initial action model is conceptually defined
- [x] the repository structure strategy is documented
- [x] Phase 0/1 handoff metadata exists (`pyproject.toml`, `Makefile`)
- [x] the testing philosophy is documented
- [x] the implementation workflow is documented
- [x] the next implementation slice is obvious and small enough to execute safely

Status note: the planning and formalization work is complete enough to hand off
to Phase 1 implementation work without requiring more architectural invention
first.

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

Those Mission 3 follow-on packets have now landed as well:
- Mission 3 is now a deterministic resolver-playable and replayable slice;
- bounded support for Building, Hill, wooded-hill semantics, and German Rifle
  Squad behavior is in place;
- the subsequent Mission 3 baselines/search packet has also landed and produced
  a first accepted Mission 3 comparison surface;
- the accepted Mission 3 wrapper and first bounded Mission 3 learning path have
  also landed in repo history.

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
- [x] **Mission 3 env-prep hardening and adapter seam**
  Closed as a bounded preparatory packet after Mission 3 search strengthening.
  Outcome:
  - mission-schema parsing now rejects unknown keys and reports missing
    required fields structurally;
  - numeric mission validation is stricter for the currently supported slice;
  - unsupported multi-start missions are rejected before runtime;
  - a narrow shared resolver-backed env session seam landed under
    `Mission1Env`;
  - the default next step is now Mission 3 env/wrapper extension.
- [x] **Mission 3 env/wrapper extension**
  Closed as a bounded wrapper-boundary packet after Mission 3 env-prep.
  Outcome:
  - `Mission3Env` landed on top of the shared resolver-backed session seam;
  - the accepted Mission 3 wrapper contract is player-visible by default and
    keeps raw `GameState` / `rng_state` out of the public surface;
  - Mission 3 public action exposure now uses a fixed 49-id local catalog with
    resolver-owned legality and opaque contact handles;
  - `mission3_env_smoke` landed as a thin wrapper/operator surface kept
    separate from historical `mission3_comparison`;
  - the packet stayed out of learning, Mission 4 content, and generic
    multi-mission env-platform work.
- [x] **Mission 3 learning experiments**
  Closed as a bounded first-pass learner-transfer packet after Mission 3
  env/wrapper extension.
  Outcome:
  - the accepted Phase-5-style learner family now runs end-to-end on
    `Mission3Env`;
  - Mission 3 now has local train / eval / summary operator surfaces under
    `outputs/mission3_learning/`;
  - the first accepted Mission 3 learned smoke surface was weak (`0/16`), which
    counted as valid transfer evidence rather than an implementation failure;
  - preserved historical Mission 3 heuristic/search references remained
    explicit and separate from the new observation-based learned surface;
  - the default next step moved to Mission 1 honest/fair-agent lab kickoff.
- [x] **Mission 1 honest/fair-agent lab kickoff**
  Closed as a bounded packet after Mission 3 learning.
  Outcome:
  - Mission 1 now has an explicit fair-vs-oracle contract in tracked repo
    surfaces;
  - the exact Mission 1 fair-ceiling workflow landed in tracked code plus a
    thin Mission-1-local operator/report surface;
  - an operator-owned exact rerun produced the exact fair reference
    `0.949848647767`, or about `189.97` expected wins per `200`;
  - preserved Mission 1 historical anchors remained explicit and separate:
    `random 11/200`, learned best `144/200`, `heuristic 157/200`, and
    oracle/planner-like `rollout 195/200`;
  - the packet stayed out of Mission 1 honest-search baselines, Mission 2
    transfer, Mission 3 honest-agent approximation, reward shaping, and
    generic planner/reporting platform work.
- [x] **Mission 1/2 artifact-backed heuristic assimilation**
  Closed as a bounded packet after Mission 1 honest/fair-agent lab kickoff.
  Outcome:
  - generic exact-artifact, policy-audit, and mission-summary workflows landed
    in tracked repo code with thin CLI/operator surfaces;
  - Mission 2 deterministic config coverage now exists inside those generic
    workflows;
  - the exact-backed evaluation contract is now explicit in tracked reporting
    surfaces, including both full-space and fixed-seed normalization views for
    exact-solved missions;
  - a promoted `ExactGuidedHeuristicAgent` landed beside the preserved
    historical `HeuristicAgent` baseline rather than silently replacing it;
  - Mission 2 now has a benchmark-light transfer/comparison path plus a known
    fixed-seed ceiling anchor `131/200` on the preserved `0..199` surface,
    carried as a strong working anchor from artifact-backed deterministic
    replay;
  - the packet stayed out of honest search, value-function study, deeper
    Mission 2 assimilation, broad distillation work, and generic experiment
    platform buildout.
- [x] **Versioned orchestration-facing episode-batch runner interface**
  Closed as a bounded packet after Mission 1/2 artifact-backed heuristic
  assimilation.
  Outcome:
  - the repo now has a tracked versioned `episode_batch` runner surface under
    `eval/episode_batch_runner.py` and `cli/episode_batch_runner.py`;
  - the first external runner contract is machine-readable,
    subprocess-friendly, and intentionally narrow in scope;
  - aggregate metrics, resolved execution metadata, structured artifact
    manifests, warnings, and explicit failure payloads are part of the tracked
    result contract;
  - builtin policy loading stays narrow in v1 through stable names rather than
    a broad dynamic loader contract;
  - the packet stayed out of exact-artifact build, policy-audit build,
    generic mission-summary as a primary external contract, and broader
    multi-operation runner-platform work.

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

The current default should be to let the highest-value unanswered research
question drive sequencing, rather than mechanically staying on Mission 3 or
returning to Mission 1 tuning without a clearer fair-agent goal.

### Current planning state

#### Recently closed packet

**Versioned orchestration-facing episode-batch runner interface**

Most important closeout result:
- the repo now has a tracked `episode_batch` runner surface over the accepted
  fixed-seed episode-runner seam;
- the first external runner contract is versioned, machine-readable, and
  subprocess-friendly;
- aggregate metrics, resolved execution metadata, structured artifact
  manifests, warnings, and explicit failure payloads are part of the tracked
  result contract;
- the packet added a bounded orchestration-facing execution surface without
  widening into heavy artifact workflows or a broad multi-operation platform.

#### Current recommended next packet

**Mission 1 honest search baselines**

Goal:
- build the first bounded family of non-oracle Mission 1 search baselines on
  top of the stronger exact-backed heuristic base rather than the older
  historical heuristic alone;
- compare simple honest-search ideas such as expected one-step scoring,
  depth-limited expectimax, sampled expectimax, and bounded rollouts without
  opening the whole ladder at once;
- keep the new honest-search results clearly separated from both the preserved
  oracle/planner-like Mission 1 rollout anchor and the promoted exact-guided
  heuristic successor.

Why this is now preferred:
- the temporary integration step for external orchestration is now closed, so
  the fair-agent ladder can return to its next open research question;
- Mission 1 now has a strong exact-backed heuristic baseline and a stable
  exact fair reference, which makes it the cleanest place to compare honest
  search families before opening heavier Mission 2-specific follow-up work;
- later value-function study, Mission 2 heuristic assimilation follow-up, and
  Mission 3 honest-agent approximation all benefit from having at least one
  bounded honest-search packet on top of the new tracked heuristic base.

Lessons already absorbed into the plan:

- promote builders and evaluation contracts, not round scripts;
- keep two exact-backed normalization views for exact-solved missions:
  - full-space ceiling vs policy root value
  - fixed-seed ceiling vs policy fixed-seed result
- preserve one promoted heuristic surface, not one tracked agent per promoted
  round;
- keep Mission 2 benchmark-light by default until a later packet explicitly
  opens deeper Mission 2 assimilation again;
- keep the orchestration-facing runner narrow and stable rather than widening
  it into a broad platform before new evidence demands it.

#### Planned fair-agent ladder after artifact-backed assimilation

This research line should stay visible in planning, but only one of its packets
should be active by default at a time.

The temporary orchestration-facing runner packet is now closed, so the next
research packet inside this ladder is again **Mission 1 honest search
baselines**.

1. **Mission 1 exact ceiling artifact**
   Closed.
   The exact fair reference is now recorded through the tracked workflow at
   `0.949848647767`.
2. **Mission 1/2 artifact-backed heuristic assimilation**
   Closed.
   The generic exact / policy / summary machinery and the promoted
   `ExactGuidedHeuristicAgent` are now tracked.
3. **Mission 1 honest search baselines**
   Try non-oracle Mission 1 baselines such as expected one-step scoring,
   depth-limited expectimax, sampled expectimax, and bounded rollouts.
4. **Mission 1 value-function study**
   Measure how well the current heuristic evaluation aligns with exact values,
   then try learned evaluators.
5. **Mission 2 heuristic assimilation follow-up**
   After the generic builders and the first promoted Mission 1-led heuristic
   are tracked, selectively assimilate the heavier Mission 2-specific
   improvements rather than rebuilding deep Mission 2 artifacts for every
   earlier candidate.
6. **Mission 1/2 artifact-driven policy-improvement and distillation**
   Turn the exact/policy-artifact workflow into a more explicit methodology:
   weighted audits, conservative `Q_pi` improvement, compact tables, and later
   other bounded distillation ideas.
7. **Mission 1 search-efficiency ideas**
   Explore pruning, beam search, top-K rollout filtering, and later bounded
   MCTS-style ideas only after the simpler honest ladder exists.
8. **Mission 3 honest-agent approximation**
   Move from exact-oracle-backed research to richer-slice approximation:
   sampled expectimax, honest rollouts, pruning, and later bounded stochastic
   tree-search ideas where exact solution is no longer available.

Why Mission 2 deserves to stay visible:

- it shares the same core rules as Mission 1, so it is the cleanest
  generalization step after a Mission 1 exact lab;
- recent experiments already suggest practical exact/artifact workflows there,
  which makes it a second high-value calibration point rather than only a
  speculative transfer target;
- it is a better bridge to Mission 3 than jumping directly from one tiny exact
  mission to a much richer slice with no oracle.

Operational note:

- some exact or large fixed-seed experiments may take many minutes rather than
  seconds;
- when that happens, the preferred shape is a thin operator-controlled command
  that the user can run locally rather than a long interactive session;
- if the workload is naturally seed-parallel or episode-parallel, future
  research packets may add bounded multi-core local execution support so the
  user can exploit available hardware without changing benchmark semantics.

### Preserved farther-out ideas

These ideas are intentionally farther out than the current mainline, but they
are worth pinning in the roadmap so they do not disappear between packets.

- keep fair and oracle agent families explicitly separated in future benchmark
  framing and docs;
- preserve the March 14 negative-result lessons:
  - naive terminal Monte Carlo is often too noisy;
  - shallow fair search only helps when the leaf evaluator is strong;
  - direct exact fair turn-search scaled badly from Mission 1 to Mission 3;
- keep later RL-agent design ideas visible, including:
  - masked legal-action policies;
  - hierarchical policies;
  - action-scoring networks over legal actions;
  - aggregated, fixed-slot, or entity-based state encodings;
  - actor-critic / PPO-style baselines;
  - imitation learning or search-distilled policies before or alongside later
    RL fine-tuning.
- keep cross-mission comparison, reporting, and replay/debug support visible,
  but only after more than one honest-agent line is active.

### Ranked future backlog

#### Highest-value backlog

1. Mission 1 honest search baselines
2. Mission 1 value-function study after the honest-search baseline packet is
   stable
3. Mission 2 heuristic assimilation follow-up
4. Mission 1/2 artifact-driven policy-improvement / distillation work
5. Mission 3 honest-agent approximation once the Mission 1 / Mission 2
   fair-agent ladder is stronger

#### Medium-value backlog

1. Cross-mission comparison and reporting once more than one honest-agent line
   is active
2. Mission 4 or another bounded richer content slice once the Mission 3 env
   and learning path are healthier
3. A narrow search-transfer/localization follow-up only if a later planning
   pass opens that as a new explicit question rather than more tuning
4. Observation/action redesign only if richer content shows the accepted
   wrapper is too Mission-1-shaped
5. Synthetic fixtures and bounded maintainability refactors ahead of broader
   multi-mission growth
6. Operator-controlled multi-core local runners for heavy exact or seeded
   experiments once the honest-agent lab starts needing repeated long runs
7. Later RL-agent design work around state/action encoding and policy/value
   architecture once the fair-agent ladder has stronger foundations

#### Lower-priority / opportunistic backlog

1. Additional Mission 1 oracle-style strengthening only if a very specific
   research question remains after the fair-agent line is clearer
2. Another default Mission 3 search packet without a clearly different question
3. Wider tooling upgrades such as `mypy`, Python 3.12 CI, broader Ruff, or
   coverage-driven cleanup
4. Generic config / artifact / experiment-platform buildout if repeated manual
   work starts to dominate progress
5. Broad agent-architecture churn before the Mission 1 / Mission 2 fair-agent
   line has produced clearer evidence
6. Additional framework compatibility layers, richer operator UX, or optional
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

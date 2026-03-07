# Roadmap

This roadmap is intentionally detailed.
Its purpose is not only to track implementation, but also to preserve scope discipline, architectural intent, and the correct build order of the project.

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

Goal: establish a strong source of truth before implementation begins, so that Codex-assisted coding is guided by explicit architecture, scope boundaries, and formalized concepts rather than improvised code generation.

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

### 0.3 Internal working documents for AI-assisted development

- [x] Create `docs/internal/repo_layout.md`
- [x] Create `docs/internal/codex_workflow.md`
- [x] Add `docs/internal/README.md`
- [x] Record the target repository layout and dependency boundaries
- [x] Record Codex prompting strategy and workflow rules
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

### 0.8 Codex operating rules before implementation begins

- [x] Define the preferred prompt granularity for Codex tasks
- [x] Define the rule that Codex should work in narrow, testable slices
- [x] Define when to ask Codex for analysis before code changes
- [x] Define when Codex is allowed to change architecture and when it is not
- [x] Define how Codex should handle ambiguity in the rule source
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
- [x] the Codex workflow is documented
- [x] the next implementation slice is obvious and small enough to execute safely

Status note: the planning and formalization work is complete enough to hand off
to Phase 1 implementation threads without requiring more architectural
invention first.

---

## Phase 1 — MVP domain engine

Goal: build a minimal but reliable simulator for a single mission, with explicit state transitions, deterministic randomness, and a domain layer that can later support both baseline agents and RL wrappers.

Focused tests should already start appearing during Phase 1 whenever a slice
adds nontrivial rule behavior.
Phase 2 expands that into broader coverage, regression support, and
reproducibility discipline; it does not mean "start testing only after the
engine exists."

### 1.1 Package and module skeleton

- [ ] Create `src/solo_wargame_ai/`
- [ ] Create initial `domain/` package
- [ ] Create initial `io/` package
- [ ] Create initial `agents/` package only if the first playable slice actually needs it
- [ ] Create initial `utils/` package if needed
- [ ] Add `__init__.py` files where appropriate
- [ ] Ensure package layout matches documented architecture

### 1.2 Core domain primitives

- [ ] Implement hex-grid coordinates and neighbors
- [ ] Implement terrain representation
- [ ] Implement core enums (unit types, terrain types, action types, statuses, phases if needed)
- [ ] Implement base unit dataclasses / models
- [ ] Implement base mission / scenario models
- [ ] Implement action dataclasses / models
- [ ] Implement explicit decision-context / pending-choice models for the staged turn flow
- [ ] Implement RNG wrapper with deterministic seeding

### 1.3 Game state and flow

- [ ] Implement `GameState`
- [ ] Implement mission metadata in state
- [ ] Implement map state representation
- [ ] Implement unit collections and indexing strategy
- [ ] Implement turn / phase structure
- [ ] Implement state validation helpers if needed
- [ ] Implement terminal conditions

### 1.4 Mission loading and initialization

- [ ] Implement scenario / mission loading
- [x] Define mission config format for the first playable scenario
- [ ] Validate mission loading against config expectations
- [ ] Implement initial state creation from mission data
- [ ] Ensure first mission can be initialized deterministically

### 1.5 Action generation and resolution

- [ ] Implement legal action generation for MVP actions
- [ ] Implement action validation
- [ ] Implement state transition resolver
- [ ] Implement movement resolution
- [ ] Implement first-pass combat resolution
- [ ] Implement morale / status change resolution if required by MVP
- [ ] Implement hidden-information / reveal handling if required by MVP
- [ ] Ensure illegal actions are rejected cleanly

### 1.6 Playable text-based slice

- [ ] Implement textual game runner
- [ ] Implement minimal event/log output
- [ ] Implement one deterministic playable trace
- [ ] Ensure a single mission can be progressed through multiple steps without manual state editing

### 1.7 Exit criteria for Phase 1

- [ ] one mission can be loaded
- [ ] initial state can be built deterministically
- [ ] legal actions can be generated
- [ ] chosen actions can be applied through the engine
- [ ] state progresses correctly across turns/phases for the MVP slice
- [ ] terminal conditions can be detected
- [ ] the simulator can produce a text-based playable run

---

## Phase 2 — Testing and reproducibility

Goal: make the simulator trustworthy enough to refactor and extend without losing correctness.

### 2.1 Unit tests for primitives

- [ ] Unit tests for grid logic
- [ ] Unit tests for terrain behavior / lookup
- [ ] Unit tests for enum-driven validation if useful
- [ ] Unit tests for RNG determinism

### 2.2 State and loading tests

- [ ] Unit tests for mission loading
- [ ] Unit tests for initial state creation
- [ ] Unit tests for state invariants
- [ ] Validation tests for malformed mission configs

### 2.3 Rule and transition tests

- [ ] Unit tests for legal action generation
- [ ] Unit tests for staged decision-context progression and German activation ordering
- [ ] Unit tests for movement resolution
- [ ] Unit tests for combat resolution
- [ ] Unit tests for morale / status changes
- [ ] Unit tests for hidden-information / reveal behavior if applicable
- [ ] Unit tests for terminal / victory conditions

### 2.4 Reproducibility and regression support

- [ ] Replay format for complete game traces
- [ ] Seed-based reproducibility tests
- [ ] Deterministic short-trace regression tests
- [ ] Ensure fixed seed + fixed actions produce stable outcomes

### 2.5 Exit criteria for Phase 2

- [ ] core domain primitives are tested
- [ ] the first mission load path is tested
- [ ] key state transitions are tested
- [ ] deterministic seeded execution is verified
- [ ] the simulator is safe enough to extend without blind refactoring

---

## Phase 3 — Baseline agents

Goal: add simple non-learning agents to validate the usefulness of the environment and provide comparison baselines before RL.

### 3.1 Agent interfaces and simple policies

- [ ] Define a minimal agent interface if needed
- [ ] Implement Random agent
- [ ] Implement first Heuristic agent
- [ ] Ensure agents consume legal actions rather than mutating state directly

### 3.2 Simulation harness and metrics

- [ ] Implement batch simulation script
- [ ] Implement evaluation metrics
- [ ] Decide which metrics matter most for early comparison
- [ ] Define a fixed evaluation seed set / benchmark protocol for agent comparisons
- [ ] Implement baseline comparison report

### 3.3 Baseline validation

- [ ] Compare random vs heuristic behavior
- [ ] Verify that baseline agents can complete full episodes in the MVP slice
- [ ] Identify obvious failure modes before RL integration

### 3.4 Exit criteria for Phase 3

- [ ] at least one nontrivial baseline agent exists
- [ ] agents can run many episodes automatically
- [ ] basic metrics can be computed and compared
- [ ] there is a baseline performance reference before RL work starts

---

## Phase 4 — RL environment

Goal: wrap the simulator in an RL-friendly interface without contaminating the domain layer.

### 4.1 Observation and action interfaces

- [ ] Observation encoding
- [ ] Action encoding
- [ ] Decide whether RL observations are full-state, player-visible, or another documented partial view
- [ ] Ensure observation and action encoding are conditioned on the current staged decision context
- [ ] Decide whether the RL wrapper exposes staged domain decisions directly or uses a higher-level action adapter
- [ ] Decide how legal actions are exposed to RL code
- [ ] Implement Legal action masking

### 4.2 Environment wrapper

- [ ] Reward function
- [ ] Gymnasium-compatible wrapper
- [ ] Decide `terminated` vs `truncated` semantics for mission end and turn-limit defeat
- [ ] Implement any required action adapter on top of the staged domain engine without redefining rules
- [ ] Ensure wrapper delegates actual rules to the domain engine
- [ ] Verify deterministic seeded resets / episodes where appropriate

### 4.3 RL usability checks

- [ ] Verify that the environment can run complete episodes
- [ ] Verify that invalid actions are masked or rejected correctly
- [ ] Verify that reward signals are at least minimally coherent

### 4.4 Exit criteria for Phase 4

- [ ] the simulator is exposed through a clean RL-friendly interface
- [ ] legal actions are handled explicitly
- [ ] reward behavior is documented well enough for experiments
- [ ] the environment can be used in training loops without redefining game rules

---

## Phase 5 — Learning experiments

Goal: run the first learning-based agent experiments and compare them against non-learning baselines.

### 5.1 First training loop

- [ ] First RL baseline
- [ ] Select and document the first training setup
- [ ] Define experiment configuration for early RL runs
- [ ] Record seeds, config versions, and evaluation protocol for each experiment run

### 5.2 Evaluation and comparison

- [ ] Evaluate against random and heuristic agents
- [ ] Analyze failure modes
- [ ] Evaluate whether the chosen RL-facing action abstraction is helping or hurting learning
- [ ] Refine reward design and action abstraction
- [ ] Record which limitations come from engine scope vs RL method choice

### 5.3 Exit criteria for Phase 5

- [ ] at least one RL experiment has been run end-to-end
- [ ] RL performance has been compared to baselines
- [ ] main bottlenecks are understood well enough to guide the next iteration

---

## Phase 6 — Extensions

Goal: extend the project beyond the first MVP slice once the core simulator and first learning loop are established.

### 6.1 Content extensions

- [ ] More missions
- [ ] Advanced rule support
- [ ] Additional unit / terrain / event mechanics as needed

### 6.2 Agent extensions

- [ ] Search-based agent
- [ ] Curriculum learning
- [ ] Better experiment reporting
- [ ] Stronger heuristic or planning baselines

### 6.3 Possible future directions

- [ ] richer observation design
- [ ] improved replay / debugging tools
- [ ] scenario generalization analysis
- [ ] broader benchmarking across missions
- [ ] optional visualization layer after the engine is mature

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
- [ ] prefer small Codex tasks over broad autogenerated rewrites

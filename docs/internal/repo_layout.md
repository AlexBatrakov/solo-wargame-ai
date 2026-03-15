# Repository Layout Plan

## Purpose

This document records the intended repository structure during early development.

It is a working architecture note for local development and AI-assisted coding.
It may be more detailed or more operational than the public documentation.

This file is meant to preserve the original architectural intent of the project before the implementation grows organically.
It should help maintain consistency across manual development and Codex-assisted changes.

## Status of this document

This is a **working internal plan**, not a strict frozen contract.

The repository may evolve differently in small details, but the core structural ideas should remain stable unless there is a deliberate architectural decision to change them.

## Guiding idea

The repository should evolve in layers:

1. game/domain logic first,
2. baseline agents second,
3. RL/environment integration later,
4. evaluation and experiments on top.

The project should avoid premature complexity.
Not every planned directory must exist immediately.

The repository should be understandable both as:
- a simulation-engine project,
- and a later ML / RL experimentation project.

The engine is the foundation.
The ML layer is built on top of it, not mixed into it.

---

## Target high-level structure

```text
repo/
├── README.md
├── ROADMAP.md
├── ASSUMPTIONS.md
├── pyproject.toml
├── Makefile
├── docs/
│   ├── reference/
│   ├── architecture.md
│   ├── game_spec.md
│   ├── state_model.md
│   ├── action_model.md
│   ├── testing_strategy.md
│   ├── development_workflow.md
│   └── internal/
│       ├── thread_reports/
│       ├── experiments/
│       └── project_profiles/
├── configs/
│   ├── missions/
│   ├── agents/
│   └── experiments/
├── src/
│   └── solo_wargame_ai/
│       ├── domain/
│       ├── io/
│       ├── agents/
│       ├── env/
│       ├── eval/
│       ├── cli/
│       └── utils/
├── tests/
├── scripts/
├── outputs/
└── notebooks/
```

This tree describes the intended mature structure.
The early repository does not need to instantiate every node immediately.

---

## Meaning of top-level directories and files

### `README.md`
Public entry point for the project.
Should explain what the repository is, why it exists, and what stage it is in.

### `ROADMAP.md`
Planning document for milestones and development phases.
Should help keep the work focused and avoid scope creep.

### `ASSUMPTIONS.md`
Registry of engineering decisions, simplifications, and rule interpretations.
Critical for avoiding hidden ambiguity.

### `pyproject.toml`
Primary Python project configuration.
Should eventually define dependencies, tooling, packaging, and development settings.

### `Makefile`
Convenience wrapper for common development commands such as tests, linting, formatting, or local runs.

### `docs/`
Public and semi-public documentation.
Contains the formalized specification of the project and reference materials.

The tracked internal workflow notes also live under `docs/internal/`.
Short per-thread local reports may live under `docs/internal/thread_reports/`,
with the reports themselves gitignored.
Scratch experiment code may live under `docs/internal/experiments/`, also
gitignored except for a short local README.

### `configs/`
Configuration files for missions, agents, and experiments.
Used to keep scenario data and experiment settings out of hardcoded Python logic where practical.

### `src/`
All Python implementation code.
Should follow a `src` layout.

### `tests/`
Unit and integration tests.
This project relies heavily on tests because it implements rule-based stateful simulation.

During Phase 0, this directory may contain only a short README.
Do not add placeholder tests here before real executable code exists under
`src/`.

### `scripts/`
Thin entrypoint scripts for local execution.
Useful for manual runs, debugging, evaluation, and training orchestration.

### `outputs/`
Generated artifacts such as logs, replays, reports, and checkpoints.
Usually not tracked in git unless explicitly curated.

### `notebooks/`
Optional exploratory notebooks.
Should not become the primary source of implementation logic.

---

## Meaning of source-code subpackages

### `src/solo_wargame_ai/domain/`
This is the core of the project.

It should contain:
- enums,
- grid representation,
- terrain,
- units,
- state models,
- actions,
- rules,
- transition resolution,
- RNG interface,
- mission-independent victory logic.

This package should represent the actual game engine.
It must remain usable without RL libraries.

### `src/solo_wargame_ai/io/`
Input/output utilities related to the simulation.

Typical responsibilities:
- mission loading,
- serializers,
- replay saving/loading,
- config parsing,
- possibly export helpers.

This layer may depend on `domain`, but should not contain rule logic itself.

### `src/solo_wargame_ai/agents/`
Agent implementations.

Expected contents over time:
- random agent,
- heuristic agent,
- rollout/search-based agent,
- learned-policy wrappers.

Agents should consume legal actions and observations/interfaces.
They should not implement or duplicate the underlying game rules.
Durable library modules under this package should be named by responsibility;
phase-history tags are acceptable only for thin operator entrypoints and
archived artifacts.

### `src/solo_wargame_ai/env/`
Environment-facing code for ML / RL integration.

Likely responsibilities:
- observation construction,
- action encoding,
- legal action masks,
- reward calculation,
- Gymnasium-compatible environment wrapper.

This package is important later, but should not drive the initial architecture.
When multi-mission growth resumes, prefer one narrow shared resolver-backed env
core plus mission-local wrappers/observation/action adapters rather than
hardening `Mission1Env` into the permanent center or building a broad generic
env platform early.
Until multiple missions really require wider abstraction, Mission-1-specific
helpers such as fixed action catalogs, observation builders, and reward helpers
should be treated as local wrapper details rather than as the future package-
wide default API.

### `src/solo_wargame_ai/eval/`
Benchmarking and analysis utilities.

Typical responsibilities:
- running many episodes,
- collecting metrics,
- summarizing results,
- producing evaluation reports,
- comparing agents.

Mission-local comparison helpers may remain local until more than one mission
actually needs a shared evaluation/reporting layer.

### `src/solo_wargame_ai/cli/`
Small command-line interfaces for local development.

Examples:
- run one deterministic scenario,
- simulate a batch of games,
- inspect mission configs,
- print legal actions for a state.

### `src/solo_wargame_ai/utils/`
Small shared utilities that do not belong in a more specific package.

This package should stay small.
It should not become a dumping ground for unresolved architecture.

---

## Dependency rules

Preferred dependency direction:

- `domain` depends on nothing project-specific outside itself
- `io` may depend on `domain`
- `env` depends on `domain`
- `agents` depend on `domain` and/or `env` interfaces
- `eval` depends on `agents`, `env`, and `io`
- `cli` may depend on `domain`, `agents`, `io`, and `eval`
- `utils` should remain lightweight and dependency-safe

### Important constraints

#### 1. Domain must remain clean
`domain` must not import:
- Gymnasium,
- PyTorch,
- Stable-Baselines,
- training code,
- notebook-specific logic.

#### 2. Rule logic belongs in domain
Game rules must not be reimplemented in:
- agents,
- eval,
- scripts,
- notebooks.

Those layers should call the engine, not recreate it.

#### 3. Agents must not mutate state directly
Agents should choose actions.
They should not directly edit `GameState` internals.
All state evolution should happen via explicit action application / resolver APIs.

#### 4. Environment is an adapter, not the source of truth
The RL environment should wrap the domain engine.
It should not become the place where the actual rules are defined.

#### 5. Scripts stay thin
Files in `scripts/` should mainly orchestrate reusable code from `src/`.
They should not contain large independent logic trees.

---

## Documentation structure policy

### Public documentation
Files under public `docs/` should contain stable, project-level information:
- architecture,
- game specification,
- state model,
- action model,
- testing strategy,
- development workflow.

### Internal documentation
Files under `docs/internal/` may contain:
- local planning notes,
- Codex workflow notes,
- prompt templates,
- architecture scratchpads,
- early structural plans.

Important rule:
If a design decision becomes stable and affects implementation, it should eventually be reflected in the public documentation as well.

Internal docs are for active work.
Public docs are for durable project truth.

---

## MVP subset

The MVP does **not** need the full target structure immediately.

A realistic first useful subset is:

```text
src/solo_wargame_ai/
├── domain/
├── io/
├── agents/
└── utils/
```

### Likely first implementation files

Inside `domain/`:
- `enums.py`
- `hexgrid.py`
- `terrain.py`
- `units.py`
- `state.py`
- `actions.py`
- `rng.py`
- `resolver.py`

Inside `io/`:
- `mission_loader.py`
- `serializers.py` later
- `replay.py` later

Inside `agents/`:
- `base.py` later or immediately if useful
- `random_agent.py`
- `heuristic_agent.py` later

Inside `utils/`:
- `seeding.py` if needed
- possibly minimal logging helpers

### Probably unnecessary in the first coding pass

Can be created later:
- `env/gym_env.py`
- `env/reward.py`
- `env/action_mask.py`
- `agents/rl_agent.py`
- `eval/metrics.py`
- `eval/reports.py`
- most experiment configs
- notebooks beyond minimal exploration

The main idea is to avoid scaffolding out future complexity before the engine exists.

---

## Current reality vs target structure

### Current reality
At the current planning stage, the repository may contain mostly:
- public documentation,
- internal planning notes,
- the reference rules PDF,
- basic repository metadata.

This is acceptable and intentional.
The documentation is establishing a strong source of truth before implementation expands.

### Target trajectory
The expected build order is:
1. docs and planning,
2. domain package,
3. mission loading,
4. tests,
5. simple CLI / scripts,
6. baseline agents,
7. RL environment,
8. evaluation framework.

This order should be preferred unless there is a good reason to deviate.

---

## Config strategy

### `configs/missions/`
Mission or scenario definitions.
Should gradually hold structured descriptions of maps, setup, objectives, and mission-specific parameters.

### `configs/agents/`
Optional parameterization for baseline agents or learned agents.
Not required on day one.

### `configs/experiments/`
Experiment definitions, evaluation settings, and training/evaluation presets.
Useful later for reproducibility.

The repository should not force heavy config abstraction too early.
But when scenario data becomes nontrivial, configs should prevent logic from becoming hardcoded everywhere.

---

## Testing layout expectations

The project should eventually include tests such as:
- `test_hexgrid.py`
- `test_actions.py`
- `test_mission_loader.py`
- `test_movement_rules.py`
- `test_fire_rules.py`
- `test_reveal_rules.py`
- `test_victory_conditions.py`
- `test_seed_reproducibility.py`

Tests should grow alongside features.
The repository should resist adding large new rule modules without corresponding tests.

After the first RL pass, a flat `tests/` root is no longer the preferred durable
shape.
When Phase 6 cleanup is opened, prefer a bounded regrouping such as:

- `tests/domain/`
- `tests/env/`
- `tests/agents/`
- `tests/eval/`
- `tests/cli/`
- `tests/integration/`

The goal is navigation clarity, not clever taxonomy.
Keep the regrouping mechanical and avoid coupling it to unrelated fixture or
behavior changes.

---

## Scripts and notebooks policy

### Scripts
Scripts are expected to be lightweight wrappers around library code.
Examples:
- run one mission,
- simulate N episodes,
- benchmark agents,
- train an RL agent later.

### Notebooks
Notebooks may be useful for:
- result exploration,
- quick visualization,
- debugging,
- experiment analysis.

However, they should not become the primary implementation location.
Core logic belongs in `src/`.

---

## Outputs policy

`outputs/` may contain:
- logs,
- replays,
- checkpoints,
- evaluation reports,
- generated summaries.

These files are usually ephemeral and should generally be ignored by git unless a specific artifact is intentionally preserved.

It may later be useful to keep curated small example outputs for demonstration, but the default assumption is that `outputs/` is local and disposable.

---

## Naming and package design principles

1. Prefer explicit names over overly clever names.
2. Prefer small modules with clear responsibilities.
3. Avoid premature abstraction.
4. Avoid broad “manager” classes unless they are clearly justified.
5. Prefer deterministic interfaces around stochastic processes.
6. Keep the engine inspectable and debuggable.
7. Prefer responsibility-based names for durable library modules.
8. Phase-based names are acceptable for thin operator CLIs, milestone docs,
   thread reports, tags, and archived artifact directories, but they should not
   dominate long-lived library surfaces once those surfaces outlive the phase
   that introduced them.

The project should optimize for clarity and correctness first, then convenience, then sophistication.

---

## Codex-oriented implementation notes

When Codex adds or edits code, it should prefer:
- small vertical slices,
- explicit tests,
- minimal but meaningful module creation,
- local consistency with the documented layout,
- no broad placeholder architecture without immediate value.

### Good examples of scope
- implement `hexgrid.py` and tests only,
- add `Unit` dataclasses and tests,
- implement mission loading for one scenario,
- implement legal movement generation only,
- implement one deterministic CLI run path.

### Bad examples of scope
- scaffolding the full RL stack before the engine exists,
- creating many empty files “for future use”,
- introducing deep inheritance hierarchies without need,
- putting rule logic in notebooks or scripts.

---

## Review checklist for future structure changes

When introducing a new directory, file group, or subsystem, ask:

1. Does it have an immediate use?
2. Does it belong in an existing package instead?
3. Does it preserve the domain-first architecture?
4. Does it reduce confusion or increase it?
5. Does it require documentation updates?
6. Does it require tests?

If the answer suggests premature complexity, defer it.

---

## Final architectural preference

The desired long-term identity of the repository is:
- a clean tactical simulation engine,
- with reproducible experiments,
- with baseline and learned agents built on top,
- with enough structure to scale,
- but without overengineering the early stages.

In short:
**engine first, agents second, RL third, polish later.**

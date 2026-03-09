# Execution Plan

## Purpose

This file is the current master control surface for repository-level planning,
dispatch, and closeout.

As of March 8, 2026, Phases 1 and 2 are complete and archived.
As of March 9, 2026, Phases 1, 2, and 3 are complete and archived.
The active planning problem is no longer "how to finish Mission 1", "how to
harden the accepted engine", or "how to open Phase 3 baselines", but "how to
open Phase 4 RL-environment planning without contaminating the domain layer or
forgetting the accepted Phase 3 benchmark surface."

If a future thread needs to know what to do next, it should read this file
after the public specs and the rules digest.

After Phase 2, future phases should use the orchestration model in
`docs/internal/orchestration_policy.md`.
In particular, prefer a small number of delivery packages per phase rather than
opening a new implementation chat for every micro-stage.

This file should now let a future master-thread do four things without
recovering chat history:

- preserve the accepted Phase 3 packet and closeout record,
- avoid reopening completed Delivery A / B / C work accidentally,
- recover the accepted baseline contract and benchmark reference quickly,
- point the next planning thread toward Phase 4.

## Current checkpoint

- Accepted milestones:
  - Phase 1 complete
  - Phase 2 complete
  - Phase 3 complete
- Local tags:
  - `phase1-complete`
  - `phase2-complete`
- Repository state checked on March 9, 2026 before closeout:
  - `git status --short` was empty
  - `git log --oneline --decorate -10` showed `HEAD` on
    `291a121 phase3: add manual baselines cli`
  - `.venv/bin/pytest -q` passed with `153 passed in 1.69s`
  - `.venv/bin/ruff check src tests` passed with `All checks passed!`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
    succeeded
  - `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode benchmark`
    succeeded

Accepted runtime surface after Phase 3 closeout:

- `Mission` remains static scenario data loaded from config.
- `GameState` remains runtime truth with explicit staged decision contexts.
- `domain/resolver.py` remains the accepted playable engine entry path.
- `io/replay.py` remains a replay adapter over the resolver path, not a second
  engine.
- `agents/base.py` records the accepted Phase 3 agent-facing contract.
- `RandomAgent` and `HeuristicAgent` provide the first accepted non-learning
  baselines on top of Mission 1.
- `eval/episode_runner.py`, `eval/metrics.py`, and `eval/benchmark.py` provide
  the accepted repeated-episode harness, metrics surface, and fixed-seed
  benchmark protocol.
- `cli/phase3_baselines.py` provides the accepted thin manual rerun surface for
  smoke and benchmark comparisons.
- Mission 1 remains playable, deterministic, regression-covered, and now
  benchmarkable through fixed-seed baseline comparisons.

Phases 1 and 2 should be treated as archived implementation history, not as the
active dispatch target.

## Phase 3 objective

Phase 3 is now defined as:

> Add the first non-learning baselines on top of the accepted Mission 1 engine,
> pressure-test repeated episode execution, and freeze a minimal agent-facing
> integration surface before any RL wrapper work.

Desired outcome:

- Random and heuristic baselines exist.
- Repeated episodes can be run over fixed seed sets.
- Baseline comparisons use explicit metrics and a stable benchmark protocol.
- The agent-facing engine surface is named clearly enough that Delivery Threads
  do not invent ad hoc integration seams.
- Mission 1 remains the only required content slice for the phase.

## Phase 3 planning audit findings

- Baseline work should use `domain/resolver.py` as the public engine facade, not
  `domain/legal_actions.py` internals.
- External audit follow-up `P3-R1` is active: Phase 3 needs an explicit
  agent-facing API note early so agents and harnesses do not bind themselves to
  helper-level seams accidentally.
- External audit follow-up `P3-R2` is already materially addressed by repo
  fact: `tests/test_replay_contracts.py` includes a deterministic full-game
  defeat replay path, so Phase 3 should retain that path as an acceptance
  contract rather than reopen it as a missing blocker.
- Repeated episode execution is more likely to stress package boundaries and
  harness interfaces than the Mission 1 rule surface itself.
- `legal_actions.py` growth and replay draw-prediction coupling remain real
  future risks, but they are preserved watchpoints for Mission 3/4-era growth,
  not default Phase 3 scope.
- Synthetic fixtures, `mypy`, Python 3.12 CI, broader Ruff, and similar tooling
  improvements remain backlog items unless a delivery package is blocked without
  them.

## Accepted Phase 3 scope

In scope:

- explicit Phase 3 agent-facing API contract
- thin agent and evaluation package surfaces for Mission 1 only
- `RandomAgent`
- first heuristic baseline
- repeated-episode harness over fixed seed sets
- comparison metrics and a reproducible benchmark protocol
- thin benchmark invocation surface if needed to make reruns practical

Out of scope:

- Gymnasium-style env wrappers, `reset` / `step`, reward design, observation
  encoding, action encoding, legal-action masks, or any other RL-facing
  adapter surface
- Mission 3/4 or broader rule/content expansion unless baseline work exposes a
  real blocking engine bug in the current Mission 1 slice
- refactors motivated only by anticipated `legal_actions.py` growth or replay
  draw-prediction discomfort
- synthetic fixture programs, `mypy` / `pyright`, Python 3.12 CI expansion,
  broader Ruff, or coverage campaigns as default Phase 3 work
- vectorized simulation, performance engineering, or experiment-platform
  generalization beyond what fixed-seed baseline runs directly require
- implementation commits or closeout work from this Phase Master Thread

## Phase 3 agent-facing API contract

Stable Phase 3 contract:

- the harness owns mission loading and episode initialization via
  `load_mission(...)` and `create_initial_game_state(...)`
- the player-facing step loop uses
  `solo_wargame_ai.domain.resolver.get_legal_actions(state)` and
  `solo_wargame_ai.domain.resolver.apply_action(state, action)`
- agents choose one `GameAction` from the current legal set; they do not mutate
  `GameState` directly and do not call `domain/legal_actions.py` helpers
- terminal handling is based on `state.terminal_outcome` and the resolver
  facade returning no legal actions for terminal states
- `IllegalActionError` is a contract error, not normal control flow for agent
  play
- replay helpers are optional evaluation/debugging adapters; agents should not
  need `ReplayTrace` or replay-event internals in order to act

Recommended external agent shape:

- input: current `GameState` plus current legal `tuple[GameAction, ...]`
- output: one selected `GameAction`
- optional per-agent RNG or seed, but any randomness must remain explicit and
  reproducible

## Defeat trace decision

Decision:

- full-game defeat coverage stays inside Phase 3 acceptance scope, but it does
  not need its own delivery package
- it belongs in Delivery A because the first agent/harness package is where the
  episode-loop contract is frozen
- repo fact already provides a deterministic defeat replay round trip, so
  Delivery A should preserve that path as a named acceptance check and add more
  direct harness coverage only if the new runner surface bypasses the existing
  replay contract

## Phase 3 metrics and benchmark protocol

Required comparison metrics:

- episode count
- terminal outcome counts plus win rate / defeat rate
- mean terminal turn
- mean resolved-marker count
- mean removed-German count
- mean player-decision count per episode

Why this set:

- it keeps the first comparison grounded in mission success plus simple mission
  progress diagnostics
- it avoids coupling core baseline metrics to replay-event internals or future
  RL reward design

Benchmark protocol:

- Mission 1 only
- same fixed seed list for all agents
- two tiers:
  - smoke: 16 seeds for package-local verification
  - benchmark: 200 fixed seeds for accepted comparison
- agent tie-breaking or randomness must be seeded explicitly and reported
- comparison output should be a small stable table/report, not a general
  experiment platform
- benchmark runs are local/manual Phase 3 verification, not CI gates

Acceptance expectation:

- both baselines complete the fixed benchmark without illegal actions or
  crashes
- heuristic behavior is measurably distinct from random on the recorded metrics
- preferred outcome is heuristic better than random on win rate; if not, the
  result must be explained explicitly before Phase 3 closeout

## Boundary: baseline harness vs premature RL/env work

Baseline harness work may include:

- episode runner around existing resolver APIs
- batch evaluation over fixed seeds
- metrics/result dataclasses
- thin CLI or script entrypoints
- agent-local ranking and selection logic over concrete legal `GameAction`
  objects

Phase 3 must not include:

- Gymnasium-style `reset` / `step`
- reward definitions or shaping
- observation encoders or tensor adapters
- action masking or flattened action ids for RL libraries
- vectorized env management
- macro-action compression designed primarily for RL rather than the current
  baseline agents

## Operational rules for Phase 3

- this master-thread owns the Phase 3 packet, status block, acceptance notes,
  and closeout docs
- Delivery Threads own implementation for one package only and normally make
  implementation commits after acceptance
- keep Phase 3 to two required Delivery Threads plus one optional package only
  if needed
- do not reopen stage-per-thread micro-slicing inside a delivery package
- if repeated episodes expose a real Mission 1 engine bug, fix it narrowly in
  the owning Delivery Thread and add protecting coverage; do not widen to
  Mission 3/4
- public docs can wait until Phase 3 deliverables are stable enough to describe
  without churn

Allowed status values:

- `pending`
- `in_progress`
- `completed`
- `blocked`

## Phase 3 status block

Update this block only from a planning / audit / master-thread after checking
repo state against the package criteria.

- Package A - Agent-facing API and episode harness foundation: completed
- Package B - Heuristic baseline and comparison loop: completed
- Package C - Benchmark packaging and operator surface: completed (optional)
- Phase 3 overall: completed
- Planning audit date: March 8, 2026
- Closeout verification date: March 9, 2026
- Blocking findings before Delivery A: none

## Phase 3 closeout record

- Accepted implementation commits:
  - `7b8937e phase3: add random agent and mission1 episode runner`
  - `b34d247 phase3: add heuristic baseline and fixed-seed comparison`
  - `291a121 phase3: add manual baselines cli`
- Final verification:
  - `.venv/bin/pytest -q` -> `153 passed in 1.69s`
  - `.venv/bin/ruff check src tests` -> `All checks passed!`
  - smoke CLI rerun succeeded on the fixed 16-seed set
  - benchmark CLI rerun succeeded on the fixed 200-seed set
- Accepted benchmark snapshot:
  - smoke: `random` 2/16 wins vs `heuristic` 11/16 wins
  - benchmark: `random` 11/200 wins vs `heuristic` 157/200 wins
- Residual Phase 3 boundaries preserved at closeout:
  - no RL/env wrapper surface was added
  - Mission 3/4 remains out of scope
  - broader tooling backlog remains deferred

## Package A - Agent-facing API and episode harness foundation

Status:

- completed
- accepted in `7b8937e phase3: add random agent and mission1 episode runner`

Goal:

- freeze the minimal agent-facing contract and land the first repeated-episode
  baseline path without introducing RL-oriented abstractions

Concrete deliverables:

- one explicit note or code-level contract naming the stable Phase 3
  agent-facing API surface
- `src/solo_wargame_ai/agents/` skeleton with a minimal agent protocol/base and
  `RandomAgent`
- minimal episode runner that owns mission init, decision looping, and
  per-episode result recording
- fixed-seed repeated-episode smoke path for Mission 1 only
- explicit acceptance check that the defeat terminal path remains covered after
  the new runner surface lands

Likely files / subsystems touched:

- `src/solo_wargame_ai/agents/__init__.py`
- `src/solo_wargame_ai/agents/base.py`
- `src/solo_wargame_ai/agents/random_agent.py`
- `src/solo_wargame_ai/eval/__init__.py`
- `src/solo_wargame_ai/eval/episode_runner.py`
- optional thin entrypoint under `src/solo_wargame_ai/cli/` or `scripts/`
- narrow doc note only if the API surface needs one tracked local home beyond
  code

Required tests / verification:

- focused tests that agents return only legal actions and do not bypass the
  resolver facade
- fixed-seed episode-runner tests that reach terminal states through actual
  gameplay flow
- repeated-episode smoke verification on the 16-seed smoke set
- `.venv/bin/pytest -q`
- `.venv/bin/ruff check src tests`

Risks / traps:

- binding agents directly to `domain/legal_actions.py` or other helper-level
  seams
- using replay as the primary control path instead of the resolver facade
- inventing a Gym-like interface before Phase 3 actually needs one
- mixing API-boundary decisions with heuristic-policy design

Completion criteria:

- `RandomAgent` can play full Mission 1 episodes through the resolver facade
- the runner returns deterministic per-episode results for fixed seeds
- the Phase 3 agent-facing contract is explicit enough that Delivery B can build
  on it without re-planning the integration surface
- defeat-path acceptance coverage remains present by repo fact

Commit shape:

- one commit preferred
- split into two only if the API note/contract surface and the runner/agent code
  become awkwardly mixed in review

Analysis-before-edit:

- required

## Package B - Heuristic baseline and comparison loop

Status:

- completed
- accepted in `b34d247 phase3: add heuristic baseline and fixed-seed comparison`

Goal:

- add the first non-random baseline and lock the first comparison-ready metrics
  and benchmark loop

Concrete deliverables:

- `HeuristicAgent` that acts only through legal `GameAction` choices
- metrics aggregation over repeated episodes using the fixed seed sets
- fixed benchmark seed/config surface for Phase 3 comparisons
- thin comparison command or callable that evaluates random vs heuristic on the
  same seeds and emits the required report table

Likely files / subsystems touched:

- `src/solo_wargame_ai/agents/heuristic_agent.py`
- `src/solo_wargame_ai/eval/metrics.py`
- `src/solo_wargame_ai/eval/benchmark.py` or adjacent comparison module
- optional thin entrypoint under `src/solo_wargame_ai/cli/` or `scripts/`
- `configs/experiments/` or another small committed seed/config surface if that
  is the cleanest way to freeze the benchmark

Required tests / verification:

- focused tests for heuristic legality and targeted preference behavior
- deterministic smoke comparison on the 16-seed smoke set
- local rerun of the 200-seed benchmark comparison
- `.venv/bin/pytest -q`
- `.venv/bin/ruff check src tests`

Risks / traps:

- heuristic logic quietly re-encoding rule legality instead of consuming the
  engine output
- metrics drifting into replay-event coupling or reward-like proxy design
- benchmark seeds or agent randomness staying implicit and making comparisons
  irreproducible
- mixing heuristic iteration with broader operator-surface or public-doc work

Completion criteria:

- random vs heuristic can be compared on one committed fixed seed set
- the required metrics are emitted in one stable report/table shape
- heuristic behavior is measurably distinct from random and preferably better on
  win rate
- no RL/env abstractions were added to make the comparison work

Commit shape:

- one commit is acceptable if the diff stays coherent
- a two-commit series is also acceptable if heuristic policy logic and
  evaluation/report plumbing are cleaner to review separately

Analysis-before-edit:

- straight to implementation after Package A is accepted
- return to analysis first only if Package B needs to change the Package A API
  contract rather than merely use it

## Package C - Benchmark packaging and operator surface

Status:

- completed (optional)
- accepted in `291a121 phase3: add manual baselines cli`

Goal:

- package benchmark invocation so accepted comparisons are easy to rerun without
  turning Phase 3 into an experiment-platform buildout

Concrete deliverables:

- one documented command or thin CLI entrypoint for smoke and benchmark runs
- committed seed/config surface if it did not already land in Package B
- only the narrow packaging/polish needed to make baseline comparisons
  repeatable by operator command rather than ad hoc Python entry

Likely files / subsystems touched:

- `src/solo_wargame_ai/cli/phase3_baselines.py` or
  `scripts/run_phase3_baselines.py`
- `configs/experiments/`
- a small internal doc note only if invocation naming or location needs to be
  frozen

Required tests / verification:

- local invocation of the accepted command on the 16-seed smoke set
- local rerun of the full benchmark if the package changes benchmark entry
  semantics
- `.venv/bin/ruff check src tests`
- targeted `pytest` if new logic lives outside existing coverage

Risks / traps:

- inventing a generic experiment-orchestration framework or RL config layer
- mixing public-doc polish or Phase 3 closeout with operator-surface work
- using Package C as a dumping ground for unresolved Package A/B design

Completion criteria:

- the accepted comparison can be rerun from one stable operator surface
- the package remains a thin wrapper over Package A/B code
- no new env/RL abstractions were introduced

Commit shape:

- one small commit only if the package actually exists

Analysis-before-edit:

- straight to implementation if the package stays a thin wrapper
- analysis-before-edit is required if Package C starts adding generic config or
  CLI architecture beyond a narrow benchmark entry surface

## Recommended Delivery Thread sequence for Phase 3

Default queue:

1. Delivery A only: agent-facing API and episode harness foundation
2. Delivery B only: heuristic baseline and comparison loop
3. Delivery C only if Package B would otherwise mix operator-surface work with
   heuristic/comparison logic, or if rerun ergonomics remain weak after
   Package B

Do not mix in one thread:

- Package A API-boundary work with heuristic tuning or benchmark interpretation
- Package B policy logic with public-doc polish or Phase 3 closeout
- Package C packaging work with RL/env design or Mission 3/4 content extension
- any Phase 3 package with backlog-only tooling expansions

Straight to implementation is appropriate when the package scope is:

- implementing Package B on top of an accepted Package A contract
- implementing a thin Package C wrapper after Package B has settled the
  benchmark shape
- adding narrow benchmark/config plumbing that does not redefine interfaces

Analysis-before-edit is required when a thread proposes to change:

- the Package A contract boundary
- the resolver facade or episode-loop ownership model
- the benchmark/config surface in a way that implies general experiment
  architecture
- the role of replay helpers in core baseline metrics
- scope boundaries toward RL/env or Mission 3/4 work

## Archived Phase 1 / Phase 2 note

The detailed Phase 1 stage plan and Phase 2 hardening plan served their purpose
and are now closed.
Do not dispatch more "Phase 1" or "Phase 2" implementation work unless
repeated baseline execution exposes a narrow Mission 1 corrective bug.

Historical context lives in:

- `docs/internal/thread_reports/2026-03-07_phase1-master-thread.md`
- `docs/internal/thread_reports/2026-03-07_phase1-full-audit.md`
- `docs/internal/thread_reports/2026-03-07_phase2-master-thread.md`
- `docs/internal/thread_reports/2026-03-07_phase2-stage4-closeout-audit.md`

## Archived Phase 2 control record

The Phase 2 plan below is preserved as archived local history because later
threads may still need to understand what was hardened and why.

Detailed Phase 2 stage reports now live primarily in the archived thread
reports listed above.

## Archived Phase 2 dispatch notes

Default queue:

1. Stage 1 only: engine contract tests and any narrow fixes they expose
2. Stage 2 only: replay/reproducibility contract tests and any narrow fixes
3. Stage 3 only: minimal CI / automation gate
4. Stage 4 only: master-thread closeout audit and next-phase handoff

Do not mix in one thread:

- Phase 2 hardening with Mission 3/4 implementation
- Phase 2 hardening with baseline-agent or RL work
- CI/tooling work with replay-format redesign
- public-roadmap rewrite with engine bug fixing

Analysis-before-edit is required when a thread proposes to change:

- `GameState` structure or runtime invariants
- decision-context or resolver semantics
- replay event/schema contracts
- the scope of the CI gate beyond the minimal accepted commands

Implementation can go straight to editing when the scope is:

- adding focused negative-path tests
- adding explicit regression tests for an already accepted contract
- adding the minimal CI workflow
- updating status docs after a completed stage

## Archived decision after Phase 2

Recommended next macro-step:

- Phase 3 baselines

Rationale:

- the repo already has a deterministic playable slice strong enough to support a
  first random/heuristic agent harness
- baselines will pressure-test the accepted legality and replay surfaces under
  repeated episode execution without increasing rule complexity first
- Mission 3/4 extension would widen the engine surface before the project has a
  baseline simulation/evaluation loop to exploit the current slice

Planning decision:

- after accepted Phase 2 closeout, open Phase 3 baselines first
- keep Mission 3/4 content extension as the next content track after the first
  baseline harness is real, or reopen earlier only if Phase 3 proves Mission 1
  too degenerate for useful comparisons

External audit follow-up:

- before opening the Phase 3 master-thread, review
  `docs/internal/independent_audit_followups.md`
- treat that file as preserved guidance for:
  - non-blocking pre-Phase-3 corrections,
  - architecture concerns to revisit before Mission 3/4,
  - optional tooling and workflow polish

## Decision after Phase 3 closeout

Recommended next macro-step:

- Phase 4 RL-environment planning

Rationale:

- the repository now has an accepted Mission 1 engine, deterministic replay
  path, fixed-seed random/heuristic baselines, and a manual rerun surface
- the next design problem is how to expose RL-facing observations, actions, and
  wrapper semantics without contaminating the domain layer or discarding the
  accepted Phase 3 comparison protocol
- Mission 3/4 content extension remains a later content track unless Phase 4
  planning proves the current Mission 1 slice structurally insufficient

## Public docs after Phase 3 closeout

During closeout, `README.md` and `ROADMAP.md` were synced to reflect that:

- Phase 3 is complete
- the next macro-step is Phase 4 RL-environment planning
- the accepted manual Phase 3 rerun commands are now documented in `README.md`

Further public polish can happen later in separate docs-only threads.

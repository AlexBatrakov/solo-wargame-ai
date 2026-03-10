# Execution Plan

## Purpose

This file is the current master control surface for repository-level planning,
dispatch, and closeout.

As of March 10, 2026, Phases 1, 2, and 3 are complete and archived.
The active planning problem is no longer "how to finish Mission 1", "how to
harden the accepted engine", or "how to open Phase 3 baselines", but "how to
open Phase 4 RL-environment planning without contaminating the domain layer,
without discarding the accepted Phase 3 benchmark surface, and without
overcommitting to a later content track too early."

If a future thread needs to know what to do next, it should read this file
after the public specs and the rules digest.

After Phase 2, future phases should use the orchestration model in
`docs/internal/orchestration_policy.md`.
In particular, prefer a small number of delivery packages per phase rather than
opening a new implementation chat for every micro-stage.

This file should now let a future master-thread do four things without
recovering chat history:

- preserve the accepted Phase 3 packet, closeout record, and benchmark
  reference,
- avoid reopening completed Delivery A / B / C work accidentally,
- recover the accepted baseline contract and benchmark reference quickly,
- point the next planning thread toward Phase 4 and later-phase decision gates.

## Current checkpoint

- Accepted milestones:
  - Phase 1 complete
  - Phase 2 complete
  - Phase 3 complete
- Local tags:
  - `phase1-complete`
  - `phase2-complete`
- `phase3-complete`
- Repository state checked on March 10, 2026 before opening this Phase 4
  master-thread:
  - `git status --short` was empty
  - `git log --oneline --decorate -12` showed `HEAD` on
    `5bd9a08 docs: refresh phase4+ roadmap after phase3`
  - `.venv/bin/pytest -q` passed with `153 passed in 1.62s`
  - `.venv/bin/ruff check src tests` passed with `All checks passed!`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
    succeeded with the accepted `random` 2/16 wins vs `heuristic` 11/16 wins
  - `git show --no-patch --decorate phase1-complete`,
    `phase2-complete`, and `phase3-complete` resolved successfully

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
- no `src/solo_wargame_ai/env/` package exists yet, and `pyproject.toml`
  currently declares no runtime RL/environment dependency
- Mission 1 remains playable, deterministic, regression-covered, and now
  benchmarkable through fixed-seed baseline comparisons.

## Strategic update after opening the Phase 4 master-thread

Current planning assumptions for later phases:

- Phase 4 should stay Mission-1-only and focus on wrapper/interface decisions
  first, not content expansion.
- The accepted Phase 3 baseline benchmark remains the pre-RL comparison
  reference and should not be replaced casually during env/training work.
- The first RL wrapper should continue to delegate legality and transitions to
  the accepted domain resolver facade rather than creating a parallel rules
  path.
- The first accepted Phase 4 contract should:
  - use an explicit player-visible observation boundary, not a raw
    `GameState` leak
  - expose the existing staged `GameAction` family through an RL adapter rather
    than silently introducing macro-actions
  - keep reward terminal-outcome-anchored and environment-level
- Phase 5 should answer whether the chosen Mission 1 wrapper/action design is
  learnable enough, not just whether training can run mechanically.
- After the first RL pass, the project should make an explicit decision between:
  - environment/action iteration,
  - stronger baselines/search,
  - or Mission 3/4 content extension.

Phases 1 and 2 should be treated as archived implementation history, not as the
active dispatch target.

## Phase 4 objective

Phase 4 is now defined as:

> Open the first Mission 1 RL-friendly environment wrapper on top of the
> accepted resolver and baseline surfaces, while keeping the domain engine
> responsible for rules and legality, keeping observation/action/reward
> boundaries explicit, and preserving the accepted Phase 3 benchmark as the
> pre-RL comparison reference.

Desired outcome:

- first observation, action, legality, and reward contracts are explicit
- a Mission 1 wrapper can run complete seeded episodes through `reset` / `step`
- the accepted Phase 3 benchmark surface remains intact and discoverable
- Phase 5 can start first learning experiments without reopening core wrapper
  boundary questions

## Phase 4 planning audit findings

- `src/solo_wargame_ai/env/` does not exist yet, so Phase 4 must add a true
  adapter layer rather than quietly repurposing `agents/`, `eval/`, or `cli/`
  as RL surfaces.
- The accepted engine seam is already good enough for a first wrapper:
  `create_initial_game_state(...)`, `resolver.get_legal_actions(state)`,
  `resolver.apply_action(state, action)`, and `state.terminal_outcome`.
- Mission 1 already exposes explicit staged `DecisionContextKind` values and a
  concrete `GameAction` union, so the first RL wrapper does not need to invent
  macro-actions just to become usable.
- Turn-limit defeat is already a domain terminal outcome, so Gymnasium
  `truncated` should be reserved for external wrapper caps rather than mapped
  from mission defeat.
- The external audit items that are truly active now are `P4-R1` through
  `P4-R4`; `C1` through `C5` remain later content-extension watchpoints, and
  `C6` is a caution not to copy `HeuristicAgent` coupling into the RL contract.
- Because `pyproject.toml` currently has no runtime dependencies, any
  `gymnasium` addition belongs inside a bounded wrapper-package decision rather
  than inside generic experiment-platform scaffolding.
- The accepted Phase 3 smoke/benchmark surfaces already provide the pre-RL
  reference and should remain separate from reward design.

## Active external audit follow-ups for Phase 4

- `P4-R1` active: lock the observation boundary explicitly and document any
  simulator-truth leakage if chosen.
- `P4-R2` active: choose the first RL action exposure and legality interface
  without silently flattening staged decisions.
- `P4-R3` active: freeze a first reward contract anchored to mission outcome.
- `P4-R4` active: preserve the accepted Phase 3 smoke and benchmark reference
  for later comparison.
- `C6` active as a caution only: `HeuristicAgent` is an accepted Mission-1
  baseline, not the stable RL/env interface to copy.
- `C1` through `C5` are not active Phase 4 scope unless wrapper work uncovers a
  concrete blocker that cannot be solved inside the env layer.

## Accepted Phase 4 scope

In scope:

- Mission 1 only
- an explicit env-layer adapter on top of the resolver path
- first observation/view construction for RL use
- first RL-facing action catalog/encoding over the accepted staged action flow
- legal-action masking or an equivalent constrained-action interface derived
  from the domain engine
- `reset` / `step` episode semantics, deterministic seeded resets, and
  environment-level reward handling
- focused wrapper tests and verification for full Mission 1 episodes
- internal planning/status docs and any narrow contract notes needed to support
  Delivery Threads

Out of scope:

- Phase 3 closeout work, baseline rewrites, or benchmark metric redesign
- treating Phase 3 metrics as default reward terms
- training loops, policy code, hyperparameter search, experiment dashboards, or
  generic RL platform buildout
- Mission 3/4 or broader content/rule expansion
- broad domain cleanup motivated by anticipated future growth rather than a
  concrete wrapper blocker
- public-doc expansion beyond narrow contract promotion that becomes stable
  after implementation
- implementation commits from this Phase Master Thread

## Phase 4 contract decisions

- First observation boundary:
  - use a structured player-visible observation derived from `GameState`
  - include the current staged decision context plus public mission/map/unit
    data needed to act
  - do not expose raw `GameState`, RNG state, or simulator-only debugging
    fields
  - unresolved marker positions remain visible because they are player-visible
    map facts, not hidden simulator truth
- First RL-facing action exposure:
  - use a fixed Mission 1 action catalog that encodes the accepted staged
    `GameAction` family as RL action ids
  - the wrapper may flatten ids for library compatibility, but it must not
    auto-resolve doubles, activation-die choice, order sequencing, or German
    activation order into hidden macro-policy
- Legality interface policy:
  - `resolver.get_legal_actions(state)` remains the source of truth
  - the wrapper maps current legal `GameAction` objects to legal ids/masks and
    surfaces those to RL code
  - invalid action ids are deterministic contract errors, not a new
    reward/transition mechanic
- `terminated` vs `truncated` semantics:
  - mission victory and mission defeat, including turn-limit defeat, map to
    `terminated=True` and `truncated=False`
  - `truncated=True` is reserved for external step caps or debug guards and
    should be absent from the default Phase 4 wrapper
- First reward contract boundary:
  - default Phase 4 reward is environment-level terminal-only reward:
    `+1` victory, `-1` defeat, `0` otherwise
  - any shaping stays explicitly deferred to named Phase 5 experiments unless a
    later accepted phase packet updates this policy
- Benchmark/reference preservation:
  - keep `agents/base.py`, `eval/episode_runner.py`, `eval/benchmark.py`, and
    `cli/phase3_baselines.py` unchanged as the accepted pre-RL comparison
    surface unless a later thread gets explicit approval to revise them
  - keep the 16-seed smoke set and the accepted 200-seed snapshot (`random`
    11/200 wins, `heuristic` 157/200 wins) as the comparison anchor
  - continue using the existing baseline CLI as a regression/comparison surface
    rather than translating its metrics into reward terms

## Boundary: wrapper work vs Phase 5 vs Mission 3/4

RL wrapper work includes:

- env package/module creation
- observation building
- action-id/catalog adaptation
- legal-action masks or equivalent constrained-action support
- reward computation at the environment boundary
- deterministic `reset` / `step` behavior and wrapper-focused verification

Phase 5 experiment work begins only when:

- a specific training library or algorithm is chosen
- experiment configs and seed policy for learning runs are being defined
- reward shaping is being tuned beyond the default terminal-only contract
- learned-policy evaluation is being compared against the accepted Phase 3
  baselines
- the project is answering whether the current Mission 1 wrapper is learnable

Later Mission 3/4 content extension begins only when:

- new terrain/unit/objective families are being added to the domain engine
- multiple-start-hex handling or objective dispatch needs to be generalized
- `legal_actions.py` structure or replay draw-prediction coupling is being
  revisited for broader content growth

## Operational rules for Phase 4

- this master-thread owns the Phase 4 packet, status block, acceptance notes,
  and closeout docs
- Delivery Threads own implementation for one package only and normally make
  implementation commits after acceptance
- keep Phase 4 to Delivery A plus Delivery B, with optional Delivery C only if
  operator-surface or closeout ergonomics remain awkward
- do not reopen Phase 3 closeout, Mission 3/4 extension, or generic RL-platform
  buildout inside Delivery A/B/C
- if a package needs to revise the accepted observation/action/reward/legality
  decisions below, return to the Phase Master Thread before editing
- routine package verification should continue to include:
  - `.venv/bin/pytest -q`
  - `.venv/bin/ruff check src tests`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
- rerun the 200-seed Phase 3 benchmark at Phase 4 closeout or earlier only if
  wrapper work touches the accepted baseline comparison surface directly

Allowed status values:

- `pending`
- `in_progress`
- `completed`
- `blocked`

## Phase 4 status block

Update this block only from a planning / audit / master-thread after checking
repo state against the package criteria.

- Package A - Observation/action/legality contract foundation: pending
- Package B - Wrapper step/reset semantics and reward contract: pending
- Package C - Operator surface and reference-preservation polish: pending
  (optional)
- Phase 4 overall: pending
- Planning audit date: March 10, 2026
- Blocking findings before Delivery A: none

## Package A - Observation/action/legality contract foundation

Status:

- pending

Goal:

- freeze the first wrapper-facing observation, action, and legality seams on top
  of the accepted resolver path without mixing in reward or operator-surface
  concerns

Concrete deliverables:

- `src/solo_wargame_ai/env/` package entry surface for Phase 4 work
- structured player-visible observation/view builder conditioned on current
  decision context
- fixed Mission 1 action catalog plus encode/decode helpers between RL action
  ids and staged domain `GameAction` objects
- legal-action mask or legal-id adapter sourced directly from the resolver legal
  set
- only the narrow doc note(s) needed to keep the contract explicit if code names
  are not self-explanatory

Likely files / subsystems touched:

- `src/solo_wargame_ai/env/__init__.py`
- `src/solo_wargame_ai/env/observation.py`
- `src/solo_wargame_ai/env/action_catalog.py` or equivalent
- `src/solo_wargame_ai/env/legal_action_mask.py` or equivalent
- focused tests under `tests/` for observation filtering and action/mask
  round-trips

Required tests / verification:

- focused tests that observation excludes RNG state and other simulator-only
  fields
- focused tests that action-id encode/decode stays aligned with the staged
  `GameAction` contract
- focused tests that the legal mask/legal-id surface matches
  `resolver.get_legal_actions(state)` for representative decision contexts
- `.venv/bin/pytest -q`
- `.venv/bin/ruff check src tests`
- `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`

Risks / traps:

- leaking raw `GameState` instead of creating an explicit observation boundary
- silently compressing staged decisions into macro-actions
- inferring legality in the env layer instead of deriving it from the resolver
- copying Mission-1-specific `HeuristicAgent` coupling into the general wrapper
  contract
- overengineering a multi-mission/generic RL platform before the first wrapper
  exists

Completion criteria:

- Mission 1 observation, action-id, and legality contracts are explicit and
  testable
- the env layer can map between RL-facing action ids and current legal staged
  domain actions without redefining rules
- Package B can build `reset` / `step` on top of this contract without reopening
  boundary decisions

Commit shape:

- one commit preferred
- split into two only if observation-boundary work and action/mask work are
  cleaner to review separately

Analysis-before-edit:

- required

## Package B - Wrapper step/reset semantics and reward contract

Status:

- pending

Goal:

- build the thin Mission 1 RL wrapper on top of Package A and freeze the first
  `reset` / `step` / reward / termination semantics

Concrete deliverables:

- Mission 1 environment class or wrapper around mission loading, initial-state
  creation, resolver stepping, and Package A encoders
- deterministic seeded `reset` contract
- `step` contract returning observation, reward, `terminated`, `truncated`, and
  `info`
- environment-level terminal-only reward helper
- invalid-action rejection behavior consistent with the legality policy
- full-episode wrapper coverage for complete Mission 1 runs

Likely files / subsystems touched:

- `src/solo_wargame_ai/env/mission1_env.py` or equivalent wrapper module
- `src/solo_wargame_ai/env/reward.py`
- `src/solo_wargame_ai/env/__init__.py`
- `pyproject.toml` if the package adds a runtime dependency such as
  `gymnasium`
- focused tests under `tests/` for wrapper semantics and determinism

Required tests / verification:

- focused tests for `reset` / `step` full-episode progression
- focused tests for victory and turn-limit defeat mapping to
  `terminated=True`, `truncated=False`
- focused tests for deterministic invalid-action rejection
- deterministic seeded wrapper tests that reproduce complete Mission 1 episodes
- `.venv/bin/pytest -q`
- `.venv/bin/ruff check src tests`
- `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`

Risks / traps:

- turning the wrapper into a second rules path instead of a resolver adapter
- sneaking benchmark metrics into reward
- treating mission defeat as truncation
- adding dependency/runtime scaffolding larger than the wrapper actually needs
- overloading `info` with raw internal truth that bypasses the chosen
  observation boundary

Completion criteria:

- the wrapper can run complete Mission 1 episodes through `reset` / `step`
- default reward and termination semantics are explicit and tested
- Package A contracts remain intact
- the accepted Phase 3 baseline surface still reruns unchanged

Commit shape:

- one coherent commit preferred
- two commits acceptable only if dependency/runtime-wrapper setup and
  reward/verification work are cleaner to review separately

Analysis-before-edit:

- straight to implementation after Package A is accepted
- return to analysis first only if Package B needs to revise Package A
  contracts or make a nontrivial dependency/API choice

## Package C - Operator surface and reference-preservation polish

Status:

- pending (optional)

Goal:

- make the accepted wrapper easy to verify and hand off to Phase 5 without
  turning Phase 4 into an experiment-platform buildout

Concrete deliverables:

- one thin manual operator surface for Phase 4 env smoke reruns if Package B
  leaves wrapper verification awkward
- narrow docs updates freezing accepted Phase 4 verification commands and
  explicitly pointing back to the preserved Phase 3 comparison reference
- only the minimal packaging/polish needed so Phase 5 does not start from ad hoc
  local commands

Likely files / subsystems touched:

- `src/solo_wargame_ai/cli/phase4_env_smoke.py` or a similarly thin operator
  entrypoint
- narrow internal/public docs if the accepted wrapper command and contract need
  promotion after Packages A/B
- targeted tests only if Package C adds nontrivial logic beyond a thin wrapper

Required tests / verification:

- local invocation of the accepted Phase 4 env smoke command if Package C adds
  one
- `.venv/bin/ruff check src tests`
- targeted `pytest` only if Package C introduces new logic
- `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`

Risks / traps:

- inventing a generic experiment/config platform
- mixing Phase 5 training concerns into a Phase 4 operator-surface package
- rerouting or redefining the accepted Phase 3 benchmark surface instead of
  preserving it

Completion criteria:

- wrapper verification can be rerun from one stable operator surface if needed
- the preserved Phase 3 comparison reference remains explicit in docs
- Phase 5 can start from accepted wrapper commands without extra planning churn

Commit shape:

- one small commit only if this optional package is actually needed

Analysis-before-edit:

- straight to implementation if the package stays a thin CLI/doc layer
- analysis-before-edit is required if Package C starts adding config or command
  architecture that looks like a general experiment platform

## Recommended Delivery Thread sequence for Phase 4

Default queue:

1. Delivery A only: observation/action/legality contract foundation
2. Delivery B only: wrapper step/reset semantics and reward contract
3. Delivery C only if Package B leaves operator-surface or closeout ergonomics
   awkward, or if Phase 5 handoff would otherwise depend on ad hoc commands/docs

Do not mix in one thread:

- Package A contract/boundary work with Package B reward or episode-semantics
  work
- any Phase 4 package with Phase 3 closeout or benchmark reinterpretation
- any Phase 4 package with Mission 3/4 content extension or domain cleanup
  aimed at later scale
- Package C polish with training-loop or experiment-config architecture

Straight to implementation is appropriate when the package scope is:

- implementing Package B on top of an accepted Package A contract
- implementing a thin Package C operator layer after Packages A/B settle the
  accepted wrapper surface
- adding narrow verification packaging that does not redefine contracts

Analysis-before-edit is required when a thread proposes to change:

- the first observation boundary
- the staged action exposure / action-catalog semantics
- legality ownership or invalid-action policy
- reward semantics beyond the default terminal-only contract
- dependency strategy for the wrapper surface
- the relationship between Phase 4 verification and the preserved Phase 3
  benchmark reference

## Archived Phase 3 control record

- Accepted implementation commits:
  - `7b8937e phase3: add random agent and mission1 episode runner`
  - `b34d247 phase3: add heuristic baseline and fixed-seed comparison`
  - `291a121 phase3: add manual baselines cli`
- Final accepted verification:
  - `.venv/bin/pytest -q`
  - `.venv/bin/ruff check src tests`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode benchmark`
- Accepted benchmark snapshot:
  - smoke: `random` 2/16 wins vs `heuristic` 11/16 wins
  - benchmark: `random` 11/200 wins vs `heuristic` 157/200 wins
- Detailed Delivery A/B/C history remains in:
  - `docs/internal/thread_reports/2026-03-08_phase3-master-thread.md`
  - `docs/internal/thread_reports/2026-03-08_phase3-delivery-a.md`
  - `docs/internal/thread_reports/2026-03-08_delivery-b_phase3_baselines.md`
  - `docs/internal/thread_reports/2026-03-09_phase3-package-c-analysis.md`
  - `docs/internal/thread_reports/2026-03-09_phase3-super-master-handoff.md`

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

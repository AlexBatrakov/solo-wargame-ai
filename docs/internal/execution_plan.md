# Execution Plan

## Purpose

This file is the current master control surface for repository-level planning,
dispatch, and closeout.

As of March 7, 2026, Phase 1 is complete.
The active planning problem is no longer "how to finish Mission 1", but "how
to harden the accepted Mission 1 engine enough that the next growth step is
safe and well-sequenced."

If a future thread needs to know what to do next, it should read this file
after the public specs and the rules digest.

## Current checkpoint

- Accepted milestone: Phase 1 complete
- Local tag: `phase1-complete`
- Repository state checked on March 7, 2026:
  - `git status --short` was empty
  - `git log --oneline --decorate -12` showed `HEAD` on
    `d6445d9 docs: sync public handoff after phase1 completion`
  - `git show --no-patch --decorate phase1-complete` resolved to the same
    commit
  - `.venv/bin/pytest -q` passed with `106 passed`
  - `.venv/bin/ruff check src tests` passed

Accepted Phase 1 runtime surface:

- `Mission` is static scenario data loaded from config.
- `GameState` is runtime truth with explicit staged decision contexts.
- `domain/resolver.py` is the accepted playable engine entry path.
- `io/replay.py` is a replay adapter over the resolver path, not a second
  engine.
- Mission 1 is playable, deterministic, and regression-covered.

Phase 1 should be treated as archived implementation history, not as the active
dispatch target.

## Archived Phase 1 note

The detailed Phase 1 stage plan served its purpose and is now closed.
Do not dispatch more "Phase 1" implementation work unless a bug found during
Phase 2 hardening requires a narrow corrective fix.

Historical context lives in:

- `docs/internal/thread_reports/2026-03-07_phase1-master-thread.md`
- `docs/internal/thread_reports/2026-03-07_phase1-full-audit.md`

## Why Phase 2 had to be replanned

The original `ROADMAP.md` Phase 2 checklist assumed that most testing and
reproducibility work would happen after the first playable slice existed.
That assumption is no longer true.

What changed in practice:

- The repository already has focused tests across primitives, loading, state
  invariants, legality, reveal, combat, German phase, terminal conditions, and
  replay.
- Deterministic replay and text-trace regression already exist.
- The accepted engine is stronger than the old setup-era wording implied.

Operational conclusion:

- Phase 2 should not be interpreted as "add more tests in general."
- Phase 2 should be treated as a short hardening cycle that locks down the
  contracts future growth will rely on.

## Audit of the old Phase 2 scope

### Already completed by fact

The following old Phase 2 items are already materially closed in the repo:

- primitive tests for grid, terrain, and RNG
- mission loading and mission validation tests
- initial-state and runtime-invariant tests
- staged British activation-flow tests
- reveal, movement, Scout, cover, and Rally tests
- British combat and German phase tests
- terminal-condition tests
- deterministic replay support
- fixed-seed replay regression coverage

### Still open

The following gaps remain meaningful even though the suite is already broad:

- there is no minimal CI / automation gate for the accepted local verification
  commands
- several stable contracts are protected only indirectly or via one accepted
  happy path
- replay is strong enough to use, but its schema/serialization guarantees are
  not yet explicitly frozen by dedicated contract tests
- the old exit criterion "safe enough to extend without blind refactoring" has
  not yet been closed by an explicit hardening audit

### Needs reframing

The following Phase 2 themes remain valid, but need narrower wording:

- "testing" should mean contract hardening for extension safety
- "reproducibility" should mean replay and deterministic regression contracts,
  not generic tooling expansion
- "regression support" should focus on stable engine surfaces that future
  baselines and content extensions will consume

### Not Phase 2 work

Do not smuggle the following into Phase 2:

- Mission 3/4 implementation
- broader rulebook content extension
- baseline agents or batch-evaluation harnesses
- RL wrappers, reward design, or action masking
- performance work beyond what a hardening bug fix directly requires
- test additions whose only purpose is coverage-number inflation
- broad public-doc rewrites unless an accepted Phase 2 decision would otherwise
  remain undocumented

## Phase 2 objective

Phase 2 is now defined as:

> Harden the accepted Mission 1 engine so that future growth can rely on
> explicit, regression-protected contracts for legality, automatic progression,
> replay/reproducibility, and basic repository verification.

The desired outcome is not a larger engine.
The desired outcome is a safer engine.

## Operational rules for Phase 2

- The master-thread owns this file and the Phase 2 status block.
- Implementation threads should execute one stage only.
- Dependent stages should not run in parallel.
- If a hardening stage finds a real engine bug, fix only that bug and add the
  protecting tests; do not expand scope to new content.
- Public docs should stay mostly unchanged during Phase 2 unless stable public
  truth would otherwise become misleading.
- CI/tooling work should lock in the accepted local commands, not invent a new
  verification stack.

Allowed status values:

- `pending`
- `in_progress`
- `completed`
- `blocked`

## Phase 2 status block

Update this block only from a planning / audit / master-thread after checking
repo state against the stage criteria.

- Stage 0 - Phase 2 replanning audit: completed
- Stage 1 - Engine contract regression hardening: completed
- Stage 2 - Replay and reproducibility contract hardening: pending
- Stage 3 - Minimal CI / automation gate: pending
- Stage 4 - Phase 2 closeout audit and next-phase dispatch: pending

## Stage 0 - Phase 2 replanning audit

Status:

- completed

Goal:

- replace the stale setup-era interpretation of Phase 2 with a repo-true
  hardening plan

Concrete deliverables:

- audited repo state against docs and the `phase1-complete` milestone
- updated this file into a Phase 2 control document
- updated `docs/internal/thread_playbook.md` for Phase 2 dispatch
- created a local master-thread report for the planning pass

Likely files / subsystems touched:

- `docs/internal/execution_plan.md`
- `docs/internal/thread_playbook.md`
- local report under `docs/internal/thread_reports/`

Verification artifacts:

- checked git status, recent history, and the `phase1-complete` tag
- reran `pytest` and `ruff`
- reviewed the required public and internal docs in full

Risks / traps:

- silently inheriting the old Phase 2 wording even though the repo has moved on
- overreacting and turning Phase 2 into a new broad architecture phase

Completion criteria:

- the new Phase 2 objective and stage plan are explicit
- the master-thread can dispatch future hardening threads from this file alone

## Stage 1 - Engine contract regression hardening

Goal:

- harden the domain/resolver contracts that future baselines and content work
  will depend on

Concrete deliverables:

- focused tests for illegal-action rejection on the accepted engine path
- focused tests for resolver automatic-progression behavior, including terminal
  normalization and turn/phase rollover contracts
- focused tests for runtime-state invariants that are present in code but still
  only partially protected
- narrow bug fixes only if those tests expose real Phase 1 contract gaps

Likely files / subsystems touched:

- `tests/test_activation_flow.py`
- `tests/test_state_validation.py`
- `tests/test_terminal_conditions.py`
- one new focused resolver-contract test module if needed
- possibly narrow fixes in:
  - `src/solo_wargame_ai/domain/legal_actions.py`
  - `src/solo_wargame_ai/domain/resolver.py`
  - `src/solo_wargame_ai/domain/state.py`

Verification artifacts that should appear:

- targeted regression tests for:
  - `IllegalActionError` paths
  - terminal-state action rejection
  - `resolve_automatic_progression()` idempotence and normalization behavior
  - phase/pending-decision coupling invariants
- passing targeted `pytest` on touched files
- passing `ruff check` on touched files

Risks / traps:

- rewriting accepted resolver semantics instead of testing them
- locking in incidental implementation details that are not intended contracts
- turning a hardening thread into Mission 3+ feature work

Completion criteria:

- accepted engine entry points have explicit negative-path and normalization
  coverage
- any discovered Phase 1 bug is fixed narrowly with protecting tests
- Mission 1 playable behavior remains unchanged

## Stage 2 - Replay and reproducibility contract hardening

Goal:

- lock replay in as a dependable regression surface rather than a lightly
  exercised debug helper

Concrete deliverables:

- focused tests for replay serialization and deterministic ordering
- a small multi-seed replay matrix that covers more than the single accepted
  victory path
- replay round-trip checks for representative trajectories such as:
  - accepted victory path
  - German-fire morale loss path
  - defeat or non-victory end-state path if a compact deterministic trace is
    practical
- narrow replay-adapter fixes only if the hardening tests expose real drift

Likely files / subsystems touched:

- `tests/test_replay_determinism.py`
- one new replay-contract test module if needed
- possibly narrow fixes in:
  - `src/solo_wargame_ai/io/replay.py`

Verification artifacts that should appear:

- tests that directly exercise:
  - `serialize_action()`
  - `ReplayTrace.to_dict()`
  - `summarize_state()`
  - `replay_trace()`
- at least one deterministic artifact beyond the current text snapshot if that
  helps freeze structured replay output without overfitting formatting
- passing targeted `pytest` and `ruff`

Risks / traps:

- redesigning replay format instead of hardening the accepted one
- duplicating engine logic so heavily in tests that the tests become brittle
- freezing cosmetic text details that should remain free to change

Completion criteria:

- replay round-trips remain deterministic across representative trajectories
- structured replay output has explicit regression protection where future tools
  are likely to rely on it
- replay still remains an adapter over the accepted resolver path

## Stage 3 - Minimal CI / automation gate

Goal:

- convert the accepted local verification commands into an automatic repository
  gate

Concrete deliverables:

- one minimal CI workflow that runs the current accepted checks:
  - `pytest -q`
  - `ruff check src tests`
- optional small local command unification such as `make verify` only if it
  reduces drift between local and CI commands
- minimal internal doc note if the invocation surface changes

Likely files / subsystems touched:

- `.github/workflows/ci.yml`
- `Makefile` only if a shared verify target is justified
- possibly one internal doc note if command naming changes

Verification artifacts that should appear:

- workflow file that installs the project and runs the accepted checks on
  Python 3.11
- local dry-run review of the workflow contents
- unchanged local `pytest` and `ruff` behavior

Risks / traps:

- overengineering a matrix, coverage upload, or release pipeline before needed
- adding gates stricter than the accepted local baseline
- mixing CI work with unrelated hardening or content changes

Completion criteria:

- the repo has an automatic minimum-quality gate for the same commands already
  used locally
- the workflow remains intentionally small and easy to maintain

## Stage 4 - Phase 2 closeout audit and next-phase dispatch

Goal:

- explicitly decide whether the hardening cycle is actually finished before
  opening the next macro-step

Concrete deliverables:

- master-thread closeout audit against Stages 1-3
- updated Phase 2 status block in this file
- explicit recommendation for the next macro-step
- note whether a public-roadmap sync is needed after the internal closeout

Likely files / subsystems touched:

- `docs/internal/execution_plan.md`
- possibly `docs/internal/thread_playbook.md` if dispatch rules need adjustment
- local audit report under `docs/internal/thread_reports/`
- public `ROADMAP.md` only in a separate docs-only follow-up if the divergence
  is still material after acceptance

Verification artifacts that should appear:

- rerun of the accepted repo verification commands
- explicit comparison between planned Stage 1-3 deliverables and actual repo
  state
- closeout note on residual risks, if any

Risks / traps:

- declaring Phase 2 complete without checking the actual remaining gaps
- carrying open hardening debt into baseline-agent or mission-extension work
- bundling public-doc cleanup into the same thread as the closeout audit

Completion criteria:

- every Phase 2 stage is either completed or explicitly deferred out of scope
- the next macro-step is named and justified
- the master-thread can hand off to the next phase without ambiguity

## Recommended Codex thread slicing for Phase 2

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

## Decision after Phase 2

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

- after Phase 2, open Phase 3 baselines first
- keep Mission 3/4 content extension as the next content track after the first
  baseline harness is real, or reopen earlier only if Phase 3 proves Mission 1
  too degenerate for useful comparisons

## Public roadmap policy after this replanning

The public `README.md` already says the next milestone should be chosen in a
separate planning pass, so the internal replanning can proceed without
immediately rewriting public docs.

However, the public `ROADMAP.md` Phase 2 wording is now partially stale.
After Stage 4, open a separate docs-only public handoff thread if the internal
Phase 2 plan is accepted unchanged and the public roadmap still risks misleading
future readers.

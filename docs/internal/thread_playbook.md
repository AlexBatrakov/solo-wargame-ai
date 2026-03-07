# Codex Thread Playbook

## Purpose

This file defines how to run Codex threads on the repository without losing
continuity.

As of March 7, 2026, Phase 2 hardening is complete.
This file remains the accepted playbook for that completed cycle.
The next master-thread should replace the active phase context with Phase 3
baseline planning before new implementation threads begin.

## Current phase context

- Phase 1 is complete and accepted.
- Phase 2 is complete and accepted.
- `phase1-complete` is the local milestone tag.
- The accepted Phase 2 control record lives in
  `docs/internal/execution_plan.md`.
- The next macro-step is Phase 3 baselines.
- The Phase 2-specific startup and slicing rules below are retained for
  audit/history and should not be treated as the active implementation queue.

If a thread starts acting as though Mission 1 still needs to be built from
scratch, it is operating from stale context.

## Mandatory startup reading order for Phase 2

For any Phase 2 implementation, planning, review, or audit thread, read these
files in this order:

1. `README.md`
2. `ROADMAP.md`
3. `docs/reference/rules_digest.md`
4. `ASSUMPTIONS.md`
5. `docs/game_spec.md`
6. `docs/state_model.md`
7. `docs/action_model.md`
8. `docs/testing_strategy.md`
9. `docs/development_workflow.md`
10. `docs/internal/execution_plan.md`
11. `docs/internal/codex_workflow.md`
12. `docs/internal/thread_playbook.md`
13. `docs/internal/repo_layout.md`
14. `docs/internal/commit_policy.md`

For a Phase 2 master-thread or closeout audit, also check the current repo state
before planning:

- `git status --short`
- `git log --oneline --decorate -12`
- `git show --no-patch --decorate phase1-complete`
- `.venv/bin/pytest -q`
- `.venv/bin/ruff check src tests`

## Default Phase 2 thread contract

Every Phase 2 thread should operate under these rules:

- do one bounded stage only
- do not expand the game beyond Mission 1 unless the task is an explicitly
  narrow bug fix
- prefer tests, contract checks, and tooling over new engine surface
- do not add baseline, RL, or content-extension work
- update public docs only if stable public truth would otherwise become
  misleading
- leave stage-status updates in `docs/internal/execution_plan.md` to the
  master-thread unless the task explicitly includes a planning update

## Master-thread vs implementation-thread responsibilities

For Phase 2, keep planning / dispatch / audit separate from implementation.

### Master-thread responsibilities

The master-thread should:

- treat `docs/internal/execution_plan.md` as the control document for Phase 2
- keep the Phase 2 status block current
- decide whether a stage is actually complete against its exit criteria
- preserve the new narrowed interpretation of Phase 2
- decide whether a public-roadmap sync is needed after closeout
- stay out of `src/` and `tests/` unless explicitly re-tasked

### Implementation-thread responsibilities

An implementation thread should:

- execute only the currently assigned Phase 2 stage
- avoid opening later dependent work in parallel
- report exactly which contract gaps were closed
- keep any bug fix narrow and paired with protecting tests
- report whether the slice is commit-ready

## Phase 2 thread types

### Type A - Contract hardening

Use when:

- the task is to add or strengthen tests for accepted engine behavior
- a narrow bug fix may be needed if tests expose a real regression risk

Expected output:

- focused tests
- minimal bug fix if needed
- explicit note on which contract was hardened

### Type B - Replay contract hardening

Use when:

- the task touches replay determinism, serialization, or structured trace
  contracts

Expected output:

- focused replay/regression tests
- minimal replay-adapter changes only if necessary
- clear note on what is intentionally treated as stable vs incidental

### Type C - Automation gate

Use when:

- the task is limited to CI / workflow / verification-command automation

Expected output:

- minimal workflow/tooling diff
- no gameplay, replay, or content changes

### Type D - Closeout audit

Use when:

- the goal is to accept or reject the completed hardening cycle

Expected output:

- findings first
- status update in `docs/internal/execution_plan.md`
- explicit recommendation for the next macro-step

## Phase 2 slicing rules

Use the Phase 2 stages from `docs/internal/execution_plan.md` as the default
thread boundaries.

Good one-thread scopes:

- Stage 1 only: engine contract tests and any narrow fixes they expose
- Stage 2 only: replay/reproducibility contract tests and any narrow fixes
- Stage 3 only: minimal CI / automation gate
- Stage 4 only: master-thread closeout audit and dispatch update

Do not mix in one thread:

- Stage 1 contract hardening with Mission 3/4 or other content work
- Stage 2 replay hardening with `GameState` / action-model redesign
- Stage 3 CI work with engine bug-hunting or public-roadmap cleanup
- Stage 4 closeout audit with new implementation work

## Analysis-before-edit rules for Phase 2

Analysis-before-edit is required when a thread proposes to change:

- runtime-state invariants in `state.py`
- decision-context semantics
- resolver automatic-progression behavior
- replay event or serialization schema
- the CI scope beyond the minimal `pytest + ruff` gate

Direct implementation is fine when the task is clearly bounded to:

- adding focused negative-path tests
- freezing an already accepted contract with regression coverage
- adding the minimal CI workflow
- updating stage status after verified completion

## Suggested Phase 2 queue

If no better priority is obvious, use this sequence:

1. harden engine contracts and negative paths
2. harden replay and reproducibility contracts
3. add the minimal CI / automation gate
4. run the closeout audit and dispatch the next macro-step

## What every Phase 2 thread should leave behind

Minimum handoff quality:

- the bounded stage objective is either met or explicitly blocked
- any new or fixed contract is protected by tests or a clearly justified gate
- the response states what remains open
- a short local report exists under `docs/internal/thread_reports/` for
  nontrivial threads
- the next thread can recover from `docs/internal/execution_plan.md` plus the
  local report without reading chat history

## Practical rule for the current repo

If a Phase 2 thread cannot point to:

- the accepted engine contract it is hardening
- the test or automation artifact that protects that contract
- and the exact Phase 2 stage it belongs to

then the work is probably not yet scoped tightly enough.

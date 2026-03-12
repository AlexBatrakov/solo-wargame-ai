# Codex Thread Playbook

## Purpose

This file defines the default cross-thread working rules for the repository.

It should remain valid across phases and later bounded packets.
Phase- or packet-specific planning belongs in `docs/internal/execution_plan.md`.

## Current project context

- Phase 1 is complete and accepted.
- Phase 2 is complete and accepted.
- Phase 3 is complete and accepted.
- Phase 4 is complete and accepted.
- Phase 5 is complete and accepted.
- Phase 6 is complete and accepted.
- The Mission 3 vertical-slice packet is complete and accepted.
- The Mission 3 baselines/search re-establishment packet is complete and
  accepted.
- The Mission 3 search-strengthening packet is complete and accepted.
- `phase1-complete`, `phase2-complete`, `phase3-complete`, and
  `phase4-complete`, `phase5-complete`, `phase6-complete` are the current
  local milestone tags.
- The original numbered phase roadmap is exhausted.
- The next active planning packet should start from the accepted Mission 3
  strengthened local comparison surface:
  Mission 3 env/wrapper extension is now preferred over reopening the closed
  search-strengthening packet, reopening Mission 3 content landing, or another
  default Mission 1 strengthening/search pass.
- Preserved external-audit follow-ups live in
  `docs/internal/independent_audit_followups.md`.

If a thread behaves as though Mission 1 still needs to be built from scratch, it
is operating from stale context.

## Current post-Mission-3 dispatch note

After Mission 3 search-strengthening packet closeout:

- use `docs/internal/execution_plan.md` as the first dispatch surface for the
  next active packet
- treat the Mission 3 content-landing packet, the Mission 3 baselines/search
  re-establishment packet, and the Mission 3 search-strengthening packet as
  archived accepted history unless repeated use exposes a narrow corrective bug
- keep the preserved Phase 3 baseline CLI and accepted 200-seed snapshot
  discoverable as the pre-RL comparison reference during later work
- keep the accepted Phase 5 learned-policy result and aggregate benchmark
  numbers discoverable during later comparison work
- keep the accepted Phase 6 rollout baseline result discoverable:
  `195/200` wins on the preserved benchmark against `heuristic 157/200` and
  learned `best 144/200`
- keep the accepted Mission 3 historical comparison surface discoverable:
  - smoke: `random 0/16`, `heuristic 7/16`, `rollout-search 8/16`
  - benchmark: `random 0/200`, `heuristic 72/200`,
    `rollout-search 105/200`
- keep the accepted strengthened Mission 3 local search result discoverable:
  - smoke: `rollout-search-strengthened 12/16`
  - benchmark: `rollout-search-strengthened 171/200`
- keep the accepted Mission 3 content slice discoverable as the richer
  deterministic domain target that now needs env/wrapper extension rather than
  another default search-quality gate
- do not reopen repo hygiene, another default search-strengthening packet,
  Mission 4 content, or generic search/RL-platform buildout casually as a
  follow-up to the Mission 3 landing
- the current default next packet is:
  Mission 3 env/wrapper extension
- do not reopen the Mission 3 content packet, the Mission 3 baselines/search
  re-establishment packet, the Mission 3 search-strengthening packet, or
  another Mission 1 strengthening/search packet by default unless new repo
  evidence justifies it
- treat Phase 4 Delivery A / B / C work as archived unless repeated use
  exposes a narrow corrective bug

## Core operating model

The repository now uses the orchestration model defined in:

- `docs/internal/orchestration_policy.md`

That means:

- one long-lived Super Master Thread for project-wide control,
- one Phase/Packet Master Thread per active major packet,
- a small number of multi-turn Delivery Threads per phase or packet,
- optional external audit threads only when their cost is justified.

Do not treat "one stage = one chat" as the default anymore.

## Mandatory startup reading order

For any nontrivial new thread, start here:

1. `README.md`
2. `ROADMAP.md`
3. `ASSUMPTIONS.md`
4. `docs/internal/execution_plan.md`
5. `docs/internal/thread_playbook.md`
6. `docs/internal/orchestration_policy.md`
7. `docs/internal/commit_policy.md`

Then add only the docs relevant to the package:

- `docs/reference/rules_digest.md` if the work touches rules
- `docs/game_spec.md` if the work touches domain behavior
- `docs/state_model.md` if the work touches runtime state
- `docs/action_model.md` if the work touches actions or legality
- `docs/reward_design.md` if reward or learning experiments are in scope
- `docs/testing_strategy.md` if tests are in scope
- `docs/development_workflow.md` if workflow/public process may change
- `docs/internal/repo_layout.md` if package/file boundaries may change
- `docs/internal/independent_audit_followups.md` if the next phase or content
  extension is being planned

For a Phase/Packet Master Thread or a closeout audit, also check repo state before
planning:

- `git status --short`
- `git log --oneline --decorate -12`
- the latest relevant milestone tag, if one exists
- the accepted local verification commands for the current phase

## Thread roles in practice

### Super Master Thread

Use for:

- cross-phase planning,
- workflow/process decisions,
- milestone tagging,
- external-audit assimilation,
- deciding when a new Phase/Packet Master Thread is needed.

### Phase/Packet Master Thread

Use for:

- refining one active phase or packet plan,
- maintaining the active phase/packet control surface,
- dispatching Delivery Threads,
- accepting/rejecting completed packages,
- packet/phase closeout and handoff.

### Delivery Thread

Use for:

- one delivery package,
- possibly across multiple turns,
- with package checkpoints rather than constant thread churn.

### Optional External Audit Thread

Use only when an independent review is worth the extra token cost.

## Default Delivery Thread contract

Every Delivery Thread should:

- own one delivery package only,
- stay inside package scope across multiple turns,
- avoid self-expanding into the next package,
- report checkpoint summaries in a copy/paste-friendly format,
- state whether it recommends:
  - continue in the same thread,
  - return to the Phase/Packet Master Thread for review,
  - stop due to a blocker.

## Multi-turn delivery rule

If a package cannot be completed in one prompt/response cycle, continue in the
same Delivery Thread unless one of these is true:

- the subsystem changes materially,
- the architecture boundary changes,
- an independent audit is needed,
- the thread has become too noisy to remain a clean package container.

Do not open a new implementation thread by default for every substep or
follow-up fix.

## Handoff checklist for Delivery Threads

Before sending a package result back to the user for Phase/Packet Master review, make
sure the response says:

- package name or id,
- what was completed,
- what files changed,
- what verification ran,
- what remains open, if anything,
- whether the package is commit-ready,
- what the Phase/Packet Master Thread should decide next.

## Handoff checklist for Phase/Packet Master Threads

When reviewing a Delivery Thread report, the Phase/Packet Master Thread should respond
with one of these outcomes:

1. continue in same Delivery Thread
2. fix in same Delivery Thread
3. accepted and commit-ready
4. escalate to Super Master Thread

The Phase/Packet Master Thread should not require a new implementation chat unless
scope or subsystem genuinely changed.

## Thread boundaries vs commit boundaries

These are not the same thing.

Important rule:

- a new commit does not automatically require a new thread

Preferred pattern:

- Delivery Threads own implementation commits for accepted delivery packages
- Phase/Packet Master Threads own planning/status/docs-only commits
- Super Master Threads own cross-phase/workflow commits

See `docs/internal/commit_policy.md` for the durable rule.

## What every nontrivial thread should leave behind

Minimum handoff quality:

- code or docs live in the repository, not only in chat
- a short local report exists under `docs/internal/thread_reports/`
- stable assumptions are documented if needed
- verification is reported explicitly
- the next thread can recover context without replaying the whole conversation

## Practical rule for this repo

If a thread cannot point to:

- its role,
- its package boundary,
- its verification contract,
- and its handoff target,

then the task is probably not scoped well enough yet.

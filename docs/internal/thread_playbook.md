# Codex Thread Playbook

## Purpose

This file defines how to use Codex threads on this repository in a way that
preserves continuity.

The main problem to avoid is this:
- each thread has only partial memory
- the rulebook is non-trivial
- the project has architecture-sensitive decisions

So every thread needs a repeatable startup and handoff process.

## Mandatory startup reading order

For a narrow implementation thread that touches one bounded subsystem, read
these files in this order:

1. `README.md`
2. `docs/reference/rules_digest.md`
3. `ASSUMPTIONS.md`
4. `docs/game_spec.md`
5. `docs/state_model.md`
6. `docs/action_model.md`
7. `docs/internal/execution_plan.md`
8. `docs/internal/codex_workflow.md`

Also add these when relevant:
- `docs/testing_strategy.md` if tests should be added or updated
- `docs/development_workflow.md` if the thread may affect process or scope rules
- `docs/internal/repo_layout.md` if package/file boundaries may change
- `docs/internal/commit_policy.md` if the thread is likely to end commit-ready

For a major planning, review, or architecture-sensitive Phase 1 thread, use the
extended startup order below:

1. `README.md`
2. `docs/reference/rules_digest.md`
3. `ASSUMPTIONS.md`
4. `docs/game_spec.md`
5. `docs/state_model.md`
6. `docs/action_model.md`
7. `docs/testing_strategy.md`
8. `docs/development_workflow.md`
9. `docs/internal/execution_plan.md`
10. `docs/internal/codex_workflow.md`
11. `docs/internal/thread_playbook.md`
12. `docs/internal/repo_layout.md`
13. `docs/internal/commit_policy.md`
14. `ROADMAP.md`

## Default thread contract

Every implementation thread should operate under these rules:

- do one bounded task only
- do not change architecture casually
- do not implement rules not required by the task
- add tests for non-trivial rule behavior
- update `ASSUMPTIONS.md` if a rule interpretation or simplification was needed
- update public docs if stable behavior changed
- do not start RL/environment work unless the task explicitly calls for it

## Master-thread vs implementation-thread responsibilities

For Phase 1, keep planning / dispatch / review work separate from implementation
work.

### Master-thread responsibilities

The master-thread should:
- treat `docs/internal/execution_plan.md` as the control document for Phase 1
- keep the Phase 1 status block current
- decide whether a stage is actually complete against its exit criteria
- enforce stage-by-stage sequencing
- prevent dependent stages from being opened in parallel
- decide the next commit-sized slice before dispatching the next implementation
  thread
- stay out of `src/` unless it is explicitly re-tasked away from the
  planning/review role

### Implementation-thread responsibilities

An implementation thread should:
- execute only the currently assigned stage or substage
- not self-upgrade its scope to the next stage
- not open dependent later-stage work in parallel
- report what exit criteria were met, what remains open, and whether the slice
  is commit-ready
- leave status changes in `execution_plan.md` to the master-thread unless the
  task explicitly asked for a planning update too

## Recommended prompt structure

When opening a new Codex thread, use a prompt that includes:

- the exact goal
- the specific files or subsystem
- the relevant docs to honor
- what is out of scope
- expected tests or verification
- whether docs must be updated

Minimal template:

```text
Read:
- README.md
- docs/reference/rules_digest.md
- ASSUMPTIONS.md
- docs/game_spec.md
- docs/state_model.md
- docs/action_model.md
- docs/internal/execution_plan.md
- docs/internal/codex_workflow.md
- docs/testing_strategy.md if tests are in scope
- docs/internal/repo_layout.md if package boundaries may change

Task:
- <one bounded task>

In scope:
- <concrete outputs>

Out of scope:
- <explicit exclusions>

Requirements:
- add or update focused tests
- do not refactor unrelated code
- update docs/assumptions if needed
```

## Thread types

### Type A - Analysis-before-edit

Use when:
- rules are ambiguous
- architecture might change
- multiple docs may need updates
- the task could balloon
- the thread is about `state.py`, `actions.py`, `decision_context.py`, replay
  format, or package-boundary changes

Expected output:
- current-state summary
- risks
- implementation proposal
- no code until direction is clear

### Type B - Narrow implementation

Use when:
- the target module is already chosen
- the rule/behavior is already specified
- the action/state contract is already settled for that slice

Expected output:
- code
- tests
- brief note on assumptions

### Type C - Review / bug hunt

Use when:
- a branch already has changes
- the goal is to find defects or regressions

Expected output:
- findings first
- severity-ordered
- no big redesign unless asked

## What every thread should leave behind

A good thread should leave the repo in a state where the next thread can recover
quickly.

Minimum handoff quality:

- code or docs are in the repository, not only in the chat reply
- tests exist for behavior that was added or changed
- assumptions are documented
- the thread response says what changed and what remains
- if the thread was nontrivial, a short local report exists under
  `docs/internal/thread_reports/`

## Handoff checklist

Before finishing a thread, check:

- Were the relevant docs actually read?
- Was the task kept narrow?
- Were rule assumptions surfaced explicitly?
- Were tests added for the new behavior?
- Was unrelated code left alone?
- Does the next thread know the next obvious task?
- Is this now one commit, several commits, or not commit-ready yet?

## Scope guardrails

These are the most important anti-patterns to avoid:

- implementing "the whole simulator"
- silently choosing an interpretation for an ambiguous rule
- adding RL abstractions before the domain engine is ready
- duplicating rule logic in agents or scripts
- creating many empty modules "for later"
- changing public docs and code out of sync

## Decision escalation rule

Stop and switch to an analysis-style thread if the work starts affecting:

- action granularity
- hidden-information semantics
- mission config schema
- replay format
- coordinate/orientation conventions
- package boundaries

These decisions are foundational and should not be smuggled in through a small
code task.

## Phase 1 slicing rules

Use the Mission 1 stages from `docs/internal/execution_plan.md` as the default
thread boundaries.

Good one-thread scopes:
- Stage 1 only: package bootstrap plus `hexgrid` / `terrain` / `rng`
- Stage 2 only: mission schema, loader, and config validation
- Stage 3A only: analysis-before-edit for state / action /
  decision-context contracts
- Stage 3B only: implementation of the agreed state / action /
  decision-context contracts
- Stage 4 only: British activation flow legality
- Stage 5 only: `advance` / `take_cover` / `rally` / `scout` / reveal
- Stage 6A only: British combat and morale
- Stage 6B only: German phase, turn rollover, terminal checks, and integration
  path
- Stage 7 only: replay / trace / manual run path

Do not mix in one thread:
- loader/schema work with state/action redesign
- replay-format work with unresolved resolver redesign
- German phase implementation with package/bootstrap setup
- Mission 1 completion with Mission 3+ extension work
- domain-engine work with agents, environment, or RL scaffolding

Default analysis-before-edit requirement inside Phase 1:
- Stage 3A is mandatory before Stage 3B
- any replay-format redesign
- any mission-schema change beyond Mission 1
- any change that affects package boundaries or action granularity

Phase-order rule:
- do not open a dependent later stage until the master-thread has confirmed the
  current stage complete and updated `docs/internal/execution_plan.md`

## Suggested first thread queue

If no better priority is obvious, use this sequence:

1. implement Stage 1 package bootstrap and board primitives
2. implement Stage 2 Mission 1 schema and loader
3. run Stage 3A analysis-before-edit
4. implement Stage 3B state and decision-context models
5. implement Stage 4 British activation flow and legality
6. implement Stage 5 reveal and non-attack orders
7. implement Stage 6A British combat and morale
8. implement Stage 6B German phase, terminal checks, and integration path
9. implement Stage 7 replay / deterministic trace support
10. move to the Mission 3-4 terrain extension

## Practical rule for this repo

If a thread cannot point to:
- the rule in the digest or PDF,
- the architecture doc it follows,
- and the test that proves the behavior,

then the change is probably not ready.

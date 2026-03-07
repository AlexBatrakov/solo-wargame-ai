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

For any non-trivial thread, read these files in this order:

1. `README.md`
2. `docs/reference/rules_digest.md`
3. `ASSUMPTIONS.md`
4. `docs/game_spec.md`
5. `docs/state_model.md`
6. `docs/action_model.md`
7. `docs/internal/execution_plan.md`
8. `docs/internal/codex_workflow.md`

If the task touches repo structure, also read:
- `docs/internal/repo_layout.md`

If the task touches tests, also read:
- `docs/testing_strategy.md`

If the thread is likely to produce a commit, also read:
- `docs/internal/commit_policy.md`

## Default thread contract

Every implementation thread should operate under these rules:

- do one bounded task only
- do not change architecture casually
- do not implement rules not required by the task
- add tests for non-trivial rule behavior
- update `ASSUMPTIONS.md` if a rule interpretation or simplification was needed
- update public docs if stable behavior changed
- do not start RL/environment work unless the task explicitly calls for it

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

Expected output:
- current-state summary
- risks
- implementation proposal
- no code until direction is clear

### Type B - Narrow implementation

Use when:
- the target module is already chosen
- the rule/behavior is already specified

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

## Suggested first thread queue

If no better priority is obvious, use this sequence:

1. create Python package skeleton and test tooling
2. implement hex-grid primitives
3. implement Mission 1 config loader
4. implement state/mission models
5. implement Mission 1 activation and orders
6. implement Mission 1 reveal/combat/German phase
7. add deterministic replay and end-to-end tests
8. move to the Mission 3-4 terrain extension

## Practical rule for this repo

If a thread cannot point to:
- the rule in the digest or PDF,
- the architecture doc it follows,
- and the test that proves the behavior,

then the change is probably not ready.

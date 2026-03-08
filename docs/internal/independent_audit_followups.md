# Independent Audit Follow-Ups

## Purpose

This file preserves externally-audited findings and follow-up decisions that
should not live only in chat history.

Its role is to capture:

- findings accepted by the project,
- required corrections before the next macro-step,
- deferred but important architecture improvements,
- optional polish that should remain discoverable later.

This is an internal working document.
Stable public truth should still be reflected in tracked public docs where
appropriate.

## External audit record

Current source captured here:

- independent Claude Opus 4.6 audit dated March 8, 2026

High-level verdict accepted from that audit:

- Phases 0-2 are complete by repository evidence.
- The project is ready for Phase 3 baselines with cautions, not blockers.
- The most important follow-ups are architecture-maintenance items that matter
  more for content extension than for the first baseline-agent pass.

## Accepted conclusions

These audit conclusions are accepted project guidance unless later repo
evidence changes them:

1. Phase 3 baselines should come before Mission 3/4 content extension.
2. Replay remains acceptable as an adapter over the resolver path for now.
3. `legal_actions.py` and replay draw-prediction are the two most likely seams
   to become painful under content growth.
4. The engine is deterministic and sufficiently hardened for a first baseline
   simulation/evaluation loop.

## Required follow-ups before Phase 3

These are not Phase 2 blockers, but they are worth addressing early in the
Phase 3 cycle because they improve the agent-facing integration surface.

### P3-R1. Agent-engine API note

Need:
- one short design note or explicit planning decision that names the stable
  agent-facing API surface for Phase 3

Current likely API:
- `get_legal_actions(state)`
- `apply_action(state, action)`
- replay helpers as optional evaluation/debugging adapters rather than agent
  dependencies

Why it matters:
- baseline agents should not reach into internal helper functions or resolver
  internals ad hoc

### P3-R2. Full-game defeat trace

Need:
- at least one deterministic end-to-end trace that reaches
  `TerminalOutcome.DEFEAT` through actual gameplay flow rather than only through
  constructed terminal states

Why it matters:
- closes the only externally-identified end-to-end terminal-path gap before
  repeated simulation work expands

## Important follow-ups before Mission 3/4 extension

These are not blockers for Phase 3 baselines, but they should be revisited
before widening the rule/content surface.

### C1. Replay draw-prediction coupling

Audit finding:
- `io/replay.py` predicts resolver RNG draws explicitly and cross-checks them
  for alignment

Why this matters:
- every future RNG-consuming rule family increases maintenance coupling between
  resolver behavior and replay prediction

Desired review point:
- before Mission 3/4 or other new random mechanics, reassess whether
  draw-by-draw prediction remains worth the maintenance cost

### C2. `legal_actions.py` growth and mixed responsibilities

Audit finding:
- legality generation and state-transition application currently live in the
  same large module

Why this matters:
- Buildings, Hills, German Rifle Squad behavior, and later specialist units are
  likely to make this file grow too quickly

Desired review point:
- before major content extension, consider a bounded refactor that separates
  legality querying from transition application, or otherwise splits the module
  by rule family

### C3. Mission-1-specific start-hex restriction

Audit finding:
- `create_initial_game_state` currently rejects missions with anything other
  than a single start hex

Why this matters:
- Mission 6 introduces multiple start hexes, so the current behavior is a
  deliberate Mission 1 scope guard, not a general engine contract

Desired review point:
- revisit before missions requiring multiple start hexes

### C4. Objective dispatch generalization

Audit finding:
- terminal-outcome evaluation is currently hardcoded to Mission 1 objective
  behavior rather than dispatched by objective kind

Why this matters:
- objective diversity will require a clearer extension seam

Desired review point:
- revisit before adding additional mission objective families

### C5. Synthetic test fixtures

Audit finding:
- all current tests rely on the real Mission 1 config rather than minimal
  in-memory mission fixtures

Why this matters:
- content extension and edge-case testing will benefit from smaller synthetic
  fixtures that are decoupled from TOML schema evolution

Desired review point:
- introduce only when they reduce friction for new content/testing work, not as
  fixture churn for its own sake

## Accepted tradeoffs for now

These were noted by the audit and are acceptable at the current project stage.

### T1. No type checker in CI yet

Accepted for now:
- type hints currently act mostly as design/documentation support plus IDE help

Revisit when:
- Phase 3/4 increases interface surface enough that static checking would
  clearly pay for itself

### T2. CI runs only Python 3.11

Accepted for now:
- the project baseline is explicitly Python 3.11 and the current CI gate is
  intentionally minimal

Revisit when:
- baseline harnesses or later env work justify testing 3.12 as well

### T3. Minimal Ruff rule set

Accepted for now:
- the current rule set keeps the gate lightweight and low-friction

Revisit when:
- code volume grows enough that additional bug-catching rules provide clear
  value

### T4. CPython `random` internal state snapshots

Accepted for now:
- raw RNG state snapshots are an internal detail; the stronger practical replay
  contract remains seed + action sequence + deterministic resolver behavior

Revisit when:
- cross-version or cross-platform replay portability becomes a real goal

## Optional polish backlog

These are worthwhile but should not derail core progress.

- add `mypy` or `pyright` once Phase 3 interfaces stabilize
- add Python 3.12 to CI
- broaden Ruff rules cautiously (for example `W` and `UP`) if the repo stays
  clean
- run one `coverage` pass to identify dead zones without turning coverage into a
  target metric
- consider a `make verify` target if local/CI command unification starts to
  drift
- optionally add a CI badge to public docs later

## Usage rule

When a future master-thread plans Phase 3 or Mission 3/4 work, it should review
this file and explicitly decide:

- which items remain merely noted,
- which items should become active scope,
- which items have been superseded by repo evidence.

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
- independent Claude Opus 4.6 audit dated March 9, 2026
- independent Claude Opus 4.6 audit dated March 10, 2026
- independent Codex CLI audit dated March 12, 2026
- independent Codex CLI future-directions brainstorm dated March 12, 2026

High-level verdict accepted from that audit:

- Phases 0-2 are complete by repository evidence.
- The project was ready for Phase 3 baselines with cautions, not blockers.
- Phase 3 is complete by repository evidence and the project is ready for Phase
  4 RL-environment planning with cautions, not blockers.
- The most important follow-ups are now split between:
  - Phase 4 wrapper-boundary decisions,
  - preservation of the accepted Phase 3 benchmark reference,
  - and architecture-maintenance items that matter more for content extension
    than for the first RL wrapper pass.
- Phase 5 is complete by repository evidence and ready for closeout with minor
  public-doc sync only, not with new implementation blockers.
- The accepted Phase 5 result demonstrates terminal-only learnability on the
  current Mission 1 wrapper, does not justify reopening Package C, and points
  the next macro-step toward stronger baselines/search rather than Mission 3/4
  content extension.
- The currently supported Mission 1 / Mission 3 slice has no newly discovered
  functional blocker, but there are real hardening gaps around checkpoint
  loading and mission-config validation that should not live only in chat
  history.
- The repository still looks correct at the top-level package split, but the
  next growth steps should avoid hardening Mission-1-specific env/eval surfaces
  into the wrong long-term shape.

## Accepted conclusions

These audit conclusions are accepted project guidance unless later repo
evidence changes them:

1. Phase 3 baselines should come before Mission 3/4 content extension.
2. Replay remains acceptable as an adapter over the resolver path for now.
3. `legal_actions.py` and replay draw-prediction are the two most likely seams
   to become painful under content growth.
4. The engine is deterministic and sufficiently hardened for a first baseline
   simulation/evaluation loop.
5. The accepted Phase 3 benchmark snapshot should be preserved as a later
   comparison reference rather than replaced casually during Phase 4/5 work.
6. `HeuristicAgent` coupling to domain internals is acceptable as a
   Mission-1-specific baseline, not as a general contract future agents or RL
   wrappers should copy.
7. The accepted Phase 5 learner result is strong enough to validate the current
   wrapper/action design as learnable without reward shaping.
8. The correct post-Phase-5 default is stronger baselines/search planning, not
   reopening the env boundary or widening immediately into Mission 3/4 content.
9. After the accepted Phase 6 rollout result (`195/200` on the preserved
   benchmark), another default Mission 1 strengthening cycle has sharply
   diminishing strategic value.
10. The next high-value packet should pivot toward richer content, starting with
    a bounded Mission 3 vertical slice plus only the structural prep that slice
    directly requires.
11. Future planning should move to a rolling packet backlog rather than
    precommitting to Phase 7 / Phase 8 / Phase 9.
12. The top-level split `domain / io / env / agents / eval / cli` is still
    correct; the next structural work should be narrow and seam-oriented rather
    than a broad repository reorg.
13. The next useful sequence after Mission 3 search strengthening is:
    one small hardening + env-adapter seam packet,
    then Mission 3 env/wrapper extension,
    then Mission 3 learning,
    then cross-mission reporting/cleanup only when multiple active missions
    justify it.

## Accepted conclusions from the March 12, 2026 future-directions brainstorm

These points are accepted as guidance for the next planning cycle.

### B1. No broad top-level repository reorg is needed now

Accepted conclusion:
- the current macro split `domain / io / env / agents / eval / cli` remains
  the right top-level shape

Why this matters:
- the risk is not that the repo is organized incorrectly overall
- the risk is that a few mission-local or phase-shaped seams could harden into
  the wrong long-term interface if the next packet grows carelessly

### B2. Add a narrow shared env-adapter seam before Mission 3 env work

Accepted conclusion:
- Mission 3 env work should grow through a small shared resolver-backed
  adapter/core seam, not by making `Mission1Env` the permanent center and not
  by creating a second isolated `MissionXEnv` island

Why this matters:
- the next env packet is the first place where the env layer could easily
  solidify into the wrong long-term shape

Desired review point:
- prioritize in the next bounded packet before Mission 3 env/wrapper extension

### B3. Tighten mission schema + semantic validation before broader growth

Accepted conclusion:
- the recently reproduced validation issues (`C8`-`C10`) are worth addressing
  before broader Mission 3 env/content growth makes bad configs harder to
  debug

Why this matters:
- validation debt compounds quickly as mission and wrapper surfaces widen

Desired review point:
- include in the next bounded preparatory packet rather than deferring

### B4. Avoid letting phase-shaped env/eval exports become durable API

Accepted conclusion:
- `env/` and `eval/` should not keep growing around Mission-1-specific or
  phase-shaped exports when a small seam extraction would keep later growth
  cleaner

Why this matters:
- this is a local API-shape problem, not a reason for a broad reorg

Desired review point:
- allow only the minimal export/seam cleanup that directly supports the next
  env-prep packet

### B5. Defer larger maintainability work until the next real forcing function

Accepted conclusion:
- splitting `legal_actions.py`, broader test regrouping, and larger cleanup are
  still worth revisiting, but they are not the immediate next packet by
  default

Why this matters:
- those items become more compelling before additional rule families or broader
  multi-mission growth, not necessarily before one bounded env-prep packet

## Accepted follow-ups from the March 12, 2026 Codex CLI audit

These findings were independently reproduced locally and are accepted as real
repo risks rather than speculative nits.

### C7. Untrusted Phase 5 checkpoint loading is unsafe

Audit finding:
- `load_phase5_checkpoint(...)` currently uses `torch.load(...)` directly on a
  caller-supplied checkpoint path.

Why this matters:
- PyTorch checkpoint loading can execute arbitrary code when the checkpoint
  file is untrusted.
- This is not a blocker for the current repo workflow, where checkpoints are
  local trusted artifacts, but it is a real security boundary if `.pt` files
  ever come from outside the repo or are shared more casually.

Current repo evidence:
- `src/solo_wargame_ai/agents/masked_actor_critic_training.py`
  loads checkpoints with `torch.load(checkpoint_path, map_location="cpu")`
  without a safer serialization policy or an explicit trusted-input boundary.

Desired review point:
- revisit before any broader checkpoint-sharing, model-download, or
  externally-supplied artifact workflow is introduced
- likely fix direction is either a safer loading mode / format or a very
  explicit "trusted local artifacts only" boundary backed by docs and tests

### C8. Mission validation does not enforce important numeric invariants

Audit finding:
- static mission validation currently checks structural consistency but does
  not reject obviously nonsensical numeric values such as `turn_limit = 0` or
  `base_to_hit = -99`.

Why this matters:
- invalid mission data can load cleanly and fail later or behave
  nonsensically, which is exactly the kind of config drift that should be
  caught at the loader/validation boundary.

Current repo evidence:
- `validate_mission(...)` currently validates map/British/German structure but
  not core numeric domains for turns, attack thresholds, German attack values,
  or combat modifiers.
- This was locally reproduced on March 12, 2026:
  - `turn_limit = 0` still loads
  - a British attack `base_to_hit = -99` still loads

Desired review point:
- prioritize before additional mission/content growth creates more config
  surface
- likely fix direction is explicit numeric-domain validation in the static
  mission-validation layer rather than letting runtime behavior surface it

### C9. Loader/runtime mismatch on multi-start missions

Audit finding:
- the mission loader/validator currently accepts multiple start hexes, while
  runtime initialization still hard-rejects anything except exactly one start
  hex.

Why this matters:
- this creates a misleading contract boundary: a mission can "load
  successfully" and still be impossible to initialize.

Current repo evidence:
- static validation only checks that start hexes are playable
- `create_initial_game_state(...)` still raises on anything other than exactly
  one start hex
- this was locally reproduced on March 12, 2026 with a two-start Mission 1
  variant: load succeeds, initialization fails

Desired review point:
- before missions that genuinely need multiple start hexes
- either tighten validation to reject unsupported multi-start missions early or
  widen runtime initialization when that support becomes part of accepted scope

### C10. Mission schema parsing is too lenient on extras and too raw on missing keys

Audit finding:
- schema parsing ignores unknown keys silently and raises raw `KeyError`
  exceptions for missing required fields.

Why this matters:
- silent acceptance of unknown keys makes config drift harder to detect
- raw `KeyError` is a poor UX compared with a structured schema/validation
  error that points to the real problem consistently

Current repo evidence:
- an unexpected top-level mission key is currently accepted without complaint
- removing `map.coordinate_system` currently produces `KeyError('coordinate_system')`

Desired review point:
- medium priority; useful hardening before broader mission/config evolution
- likely fix direction is a stricter parser/validator boundary that reports
  unknown and missing fields as structured mission-schema errors

### C11. Fair-vs-oracle benchmark framing is still too implicit

Audit finding:
- some accepted heuristic/search baselines are reproducible and useful, but
  they are not all fair player-information policies. In particular, several
  Mission 3 agents and rollout/search baselines can rank actions using
  branch-realized randomness from cloned simulator states.

Why this matters:
- this is not a simulator-correctness failure, but it is a benchmark-contract
  and interpretation risk
- without an explicit split, future planning can accidentally compare fair
  observation-based agents, oracle-style search references, and learned
  policies as if they measured the same thing

Current repo evidence:
- the local reports
  `docs/internal/thread_reports/2026-03-14_fairness_analysis_mission1_mission3.md`
  and
  `docs/internal/thread_reports/2026-03-14_rng-branch-peeking_fairness_report.md`
  argue that the accepted Mission 1 heuristic is broadly defensible as
  fair-ish, while Mission 3 heuristic/search surfaces and rollout-style
  baselines should be treated as oracle/clairvoyant references unless later
  work replaces them with honest counterparts

Desired review point:
- before making stronger cross-agent claims on richer content and before
  formalizing the later Mission 1 honest/fair-agent research line
- likely fix direction is an explicit fair-vs-oracle split in benchmark
  framing, observation-based contracts, and future fair-agent packet design

## Resolved follow-ups since the Phase 2 audit

### P3-R1. Agent-engine API note

Resolved by repo evidence:

- the accepted agent-facing contract now lives in `src/solo_wargame_ai/agents/base.py`
- Phase 3 planning and closeout docs also name the resolver-based seam

### P3-R2. Full-game defeat trace

Resolved by repo evidence:

- deterministic defeat coverage exists in replay-contract tests
- repeated-episode Phase 3 work preserved direct defeat-path acceptance through
  the runner surface

## Required follow-ups before Phase 4

These are not Phase 3 blockers, but they are worth addressing early in the
Phase 4 cycle because they define the RL wrapper boundary.

### P4-R1. Observation boundary and partial-information policy

Need:
- one explicit planning decision about the first RL observation family
- if the wrapper leaks simulator truth rather than player-visible information,
  that must be documented as an intentional shortcut, not an accident
- observation shape must remain conditioned on the current staged decision
  context

Why it matters:
- hidden information and staged decision flow are core parts of the game, so
  the first RL wrapper should not blur them implicitly

### P4-R2. RL action exposure and legality contract

Need:
- one explicit decision about whether the first wrapper exposes staged domain
  decisions directly or adds a higher-level action adapter
- one explicit policy for how legal actions are surfaced to RL code
- preserve the principle that legality remains a domain-engine responsibility

Why it matters:
- the project already committed to written staged turn flow in the domain; the
  first RL wrapper should not silently undo that without a documented reason

### P4-R3. Reward contract anchored to mission outcome

Need:
- one explicit first reward contract for the wrapper
- terminal mission success/failure should remain the anchor
- any shaping should be deliberate and documented rather than implicitly copied
  from Phase 3 evaluation metrics

Why it matters:
- reward choices can easily contaminate environment design if they remain
  hand-wavy until implementation

### P4-R4. Preserve the accepted Phase 3 benchmark reference

Need:
- keep the accepted 16-seed smoke path and 200-seed benchmark snapshot
  discoverable and reusable during Phase 4/5 work
- use that baseline surface as a later comparison reference rather than
  replacing it ad hoc

Why it matters:
- the project now has a meaningful pre-RL performance reference and should not
  lose it while opening the env layer

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

### C6. Mission-1-specific heuristic coupling

Audit finding:
- `HeuristicAgent` is intentionally Mission-1-specific and may use
  resolver-based lookahead / synthetic-state assistance

Why this matters:
- this is acceptable for the current baseline, but it should not be mistaken
  for the stable interface future content-general baselines or RL wrappers
  should depend on

Desired review point:
- revisit when stronger baselines or broader mission coverage are introduced

## Accepted tradeoffs for now

These were noted by the audit and are acceptable at the current project stage.

### T1. No type checker in CI yet

Accepted for now:
- type hints currently act mostly as design/documentation support plus IDE help

Revisit when:
- Phase 4/5 increases interface surface enough that static checking would
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

When a future master-thread plans Phase 4+, stronger baseline work, or Mission
3/4 extension, it should review
this file and explicitly decide:

- which items remain merely noted,
- which items should become active scope,
- which items have been superseded by repo evidence.

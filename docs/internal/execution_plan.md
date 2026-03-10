# Execution Plan

## Purpose

This file is the current master control surface for repository-level planning,
dispatch, and closeout.

As of March 10, 2026, Phases 1, 2, and 3 are complete and archived.
Phase 4 is now also complete by repository evidence.
The active planning problem is no longer "how to finish Mission 1", "how to
harden the accepted engine", "how to open Phase 3 baselines", or "how to open
Phase 4 RL-environment planning", but "how to use the accepted Mission 1 env
wrapper to answer whether the current observation/action design is learnable
before widening scope."

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
- preserve the accepted Phase 4 packet and closeout record,
- avoid reopening completed Delivery A / B / C work accidentally,
- recover the accepted baseline, wrapper, and benchmark references quickly,
- point the next planning thread toward Phase 5 and later-phase decision gates.

## Current checkpoint

- Accepted milestones:
  - Phase 1 complete
  - Phase 2 complete
  - Phase 3 complete
  - Phase 4 complete
- Local tags:
  - `phase1-complete`
  - `phase2-complete`
  - `phase3-complete`
  - `phase4-complete`
- Repository state checked on March 10, 2026 before opening this Phase 5
  master-thread:
  - `git status --short` was empty
  - `git log --oneline --decorate -12` showed `HEAD` on
    `0e4a6a8 docs: close phase4 rl-environment`
  - `git show --no-patch --decorate phase1-complete` resolved to
    `d6445d9 docs: sync public handoff after phase1 completion`
  - `git show --no-patch --decorate phase2-complete` resolved to
    `1ef74ab docs: finalize phase2 closeout handoff`
  - `git show --no-patch --decorate phase3-complete` resolved to
    `98519c7 docs: close phase3 baselines`
  - `git show --no-patch --decorate phase4-complete` resolved to
    `0e4a6a8 docs: close phase4 rl-environment`
  - `.venv/bin/pytest -q` passed with `175 passed in 1.84s`
  - `.venv/bin/ruff check src tests` passed with `All checks passed!`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
    succeeded with the preserved `random` `2/16` wins vs `heuristic`
    `11/16` wins reference
  - `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`
    succeeded with `action_catalog_size=32`, `decision_steps=35`,
    `terminal_outcome=defeat`, `final_reward=-1.0`

Accepted runtime surface after Phase 4 closeout:

- `Mission` remains static scenario data loaded from config.
- `GameState` remains runtime truth with explicit staged decision contexts.
- `domain/resolver.py` remains the accepted playable engine entry path.
- `io/replay.py` remains a replay adapter over the resolver path, not a second
  engine.
- `agents/base.py` records the accepted Phase 3 domain-action contract.
- `RandomAgent` and `HeuristicAgent` remain the accepted non-learning Mission 1
  baselines, with the 200-seed snapshot fixed at `11/200` and `157/200`.
- `eval/episode_runner.py`, `eval/metrics.py`, and `eval/benchmark.py` remain
  the accepted baseline harness and comparison-metrics surface.
- `env/normalize_env_state(...)` is the accepted env decision boundary over
  automatic resolver progression.
- `env/observation.py` exposes a structured player-visible observation rather
  than raw `GameState`.
- `env/action_catalog.py` fixes Mission 1 to a 32-id staged-action catalog.
- `env/legal_action_mask.py` derives legal ids and masks from the resolver legal
  set.
- `env/mission1_env.py` is a dependency-free wrapper with deterministic
  `reset(seed=...)`, `step(action_id)`, terminal-only default reward, and
  `terminated` / `truncated` semantics already frozen.
- `cli/phase3_baselines.py` and `cli/phase4_env_smoke.py` remain the accepted
  manual operator surfaces.
- `pyproject.toml` still has `dependencies = []`, and `configs/` currently
  contains only the Mission 1 config rather than experiment presets.

## Strategic update after opening the Phase 5 master-thread

Current planning assumptions for later phases:

- Phase 5 should answer whether the accepted Mission 1 wrapper is learnable
  enough before widening content or architecture scope.
- The accepted Phase 4 env surface should be used as-is unless learning work
  exposes a narrow corrective bug; do not reopen observation/action/reward
  boundary debates casually.
- The accepted Phase 3 baseline benchmark remains the pre-RL comparison
  reference and should not be replaced, reinterpreted, or translated into
  reward.
- Prefer one bounded first learner, one thin learning-side compatibility
  adapter, and one fixed evaluation protocol over generic experiment-platform
  buildout.
- Reward shaping is not the default Phase 5 plan; it is an optional follow-up
  only after the terminal-only first pass is measured honestly.
- If Phase 5 exposes a narrow wrapper bug, treat that as Phase 4 corrective work
  in a separate bounded thread, then resume the blocked learning package.

Phases 1 through 4 should be treated as archived accepted history, not as the
active dispatch target.

## Phase 5 objective

Phase 5 is now defined as:

> Run the first end-to-end learning experiments on the accepted Mission 1 env
> wrapper to determine whether the current observation/action/reward surface is
> learnable enough to justify further investment, while preserving comparability
> with the accepted Phase 3 baselines and avoiding generic RL-platform growth.

Desired outcome:

- one bounded first learner and training setup are chosen explicitly
- the accepted `Mission1Env` can support end-to-end learner runs without
  reopening the wrapper contract
- learned-policy evaluation is compared against the preserved Phase 3
  references using the accepted seed sets and metrics
- the phase ends with an explicit gate between:
  - environment/action iteration
  - stronger baselines/search
  - Mission 3/4 content extension

## Phase 5 planning audit findings

- The accepted env already exposes everything a first masked discrete learner
  needs: deterministic seeded episodes, fixed action ids, legal ids/masks, and
  a structured observation boundary.
- `Mission1Env` is usable directly for learning semantics, but
  `observation.py` returns nested serializable dicts rather than tensor-ready
  features, so a thin learning-side feature adapter is still required.
- Current observation plus `info` is sufficient to reconstruct the accepted
  Phase 3 metrics for learned episodes without changing the default env
  contract:
  - `terminal_outcome` and `turn` come from the terminal observation
  - resolved markers come from initial marker count vs terminal
    `unresolved_markers`
  - removed German count comes from terminal `revealed_german_units`
  - player-decision count already lives in `info["decision_step_count"]`
- The accepted Phase 3 eval stack is domain-action-based and random/heuristic
  specific, so learned-policy evaluation should reuse its seed sets and metric
  schema without overloading the accepted benchmark module itself.
- `pyproject.toml` and `configs/` still contain no learning/runtime layer, so
  Phase 5 should add only the minimum new surface needed for one learner and
  one evaluation protocol.
- The dominant technical risk for the first learning pass is reward sparsity and
  feature representation, not legality plumbing.
- The fixed 32-id action catalog is large enough to require masking but still
  small enough for a first masked learner; the current blocker risk is not raw
  action count.
- `HeuristicAgent` relies on Mission-1-specific lookahead and synthetic state
  fabrication, so it remains a baseline to compare against, not a contract to
  copy into the learning path.

## Active follow-ups and assumptions for Phase 5

Active external audit follow-ups for this phase:

- `P4-R1` through `P4-R3` are resolved by accepted repo evidence and now act as
  frozen constraints rather than open planning work.
- `P4-R4` remains active as a preservation constraint:
  - keep the accepted 16-seed smoke surface and 200-seed snapshot explicit and
    unchanged during learning work
- `C6` remains active as a caution:
  - do not copy `HeuristicAgent` coupling into the learning contract or treat it
    as the stable future-agent interface

Not active by default in Phase 5 unless a concrete blocker appears:

- `C1` replay draw-prediction coupling
- `C2` `legal_actions.py` growth / separation
- `C3` multiple-start-hex support
- `C4` objective-dispatch generalization
- `C5` synthetic fixtures
- `T1` through `T4` optional tooling backlog items

Active assumptions from current public docs:

- `ASSUMPTIONS.md: O2` and `O6` stay active:
  - the accepted structured observation remains the source of truth, but
    learning code may derive a flattened/tensorized representation from it
- `ASSUMPTIONS.md: O3` stays active:
  - do not introduce macro-actions in Phase 5 unless the accepted 32-id staged
    catalog proves a concrete blocker
- `ASSUMPTIONS.md: O4` stays active:
  - shaping is optional and experimental only after a default terminal-only pass
    is measured

## Accepted Phase 5 scope

In scope:

- one bounded first learner and training setup for Mission 1 only
- a thin compatibility/feature adapter over the accepted env observation and
  legal-action surface
- masked discrete action selection using the accepted action ids and masks
- one deterministic local training/evaluation protocol with explicit seed policy
- learned-policy evaluation that preserves the accepted Phase 3 comparison
  metrics and seed sets
- one end-to-end terminal-only learner pass
- one optional follow-up package for shaping or blocker response only if the
  terminal-only pass fails to answer the learnability question cleanly
- internal planning/status docs and a local thread report

Out of scope:

- changing the accepted default Phase 4 env contract without a concrete blocker
- automatic adoption of `gymnasium`, Stable-Baselines3, RLlib, or a generic RL
  framework layer
- generic training-platform, checkpoint-service, dashboard, or experiment-campaign
  scaffolding
- Mission 3/4 or broader content/rule expansion
- broad domain/env cleanup motivated by anticipated scale rather than a narrow
  learning blocker
- rewriting the accepted Phase 3 baselines or benchmark reference
- translating Phase 3 metrics into reward terms
- stronger search/planning baselines inside this phase packet
- implementation commits from this Phase Master Thread

## Phase 5 planning decisions

- First learner / training setup:
  - use one masked episodic actor-critic baseline for the first pass
  - concretely, prefer a small policy/value learner in the style of
    REINFORCE-plus-value-baseline rather than DQN replay infrastructure or a
    PPO-style framework stack
  - train directly against `Mission1Env` episodes; imitation learning is not the
    primary Phase 5 question
  - use the 16-seed smoke set for fast evaluation checkpoints and the accepted
    200-seed set for the final comparison
- Dependency / framework strategy:
  - do not introduce a new env/framework layer in Phase 5
  - no `gymnasium` compatibility work is required for the first pass
  - no full RL framework should be added in this phase packet
  - one bounded numerical/model dependency is acceptable if the chosen learner
    needs it; if so, prefer `torch` over a full RL stack because it adds
    tensor/autograd support without forcing env redesign
- Wrapper usage vs thin adapter:
  - treat `Mission1Env` as the truth surface for learning work
  - add only a thin learning-side adapter for deterministic feature extraction
    and mask shaping
  - do not change the accepted observation schema or fixed action ids merely to
    fit a first learner implementation
- Reward policy for the first pass:
  - the accepted terminal-only reward is sufficient and required for the first
    end-to-end pass
  - Delivery A and Delivery B should not add shaping
  - shaping is admissible only in optional Delivery C after the terminal-only
    pass is evaluated honestly and found insufficient
  - any shaping must be explicit, bounded, and separate from the default env
    reward contract
- Evaluation metrics required for this phase:
  - primary comparison remains mission outcome on the accepted 200-seed set
  - final learned-policy reporting must include the accepted Phase 3 metric row:
    `wins`, `defeats`, `win_rate`, `defeat_rate`, `mean_terminal_turn`,
    `mean_resolved_markers`, `mean_removed_german`, `mean_player_decisions`
  - development-time smoke evaluation may use the fixed 16-seed set
  - track training budget and training seeds separately from reward:
    episodes, env steps, checkpoint step, invalid-action count
- Minimum success criteria for Phase 5:
  - at least one terminal-only learned checkpoint completes end-to-end training
    and reaches `>= 50/200` wins on the accepted benchmark seed set
  - the median result across the planned training seeds must beat the fixed
    random reference of `11/200`
  - if these conditions are not met, Phase 5 has not shown the current wrapper
    to be convincingly learnable
- End-of-phase decision gate:
  - choose `environment/action iteration` if the terminal-only pass and any
    bounded optional follow-up still fail the minimum bar or if failure analysis
    points to observation/action/reward bottlenecks
  - choose `stronger baselines/search` if the first learner clears the minimum
    bar and the wrapper looks learnable, but the remaining question is how much
    headroom exists above heuristic-style play
  - choose `Mission 3/4 content extension` only if learning results approach the
    current heuristic ceiling closely enough that Mission 1 looks saturated
    rather than blocked by the wrapper; use `>= 140/200` wins as the rough
    trigger band for that discussion rather than a casual impression

## Comparability policy with the accepted Phase 3 benchmark

- Keep the accepted Phase 3 baseline CLI, smoke set, and 200-seed snapshot
  unchanged as the comparison anchor.
- Evaluate the learned policy on the same Mission 1 config and the same fixed
  evaluation seed ranges:
  - smoke: `0..15`
  - benchmark: `0..199`
- Keep the accepted baseline numbers explicit in docs and reports:
  - `random`: `11/200`
  - `heuristic`: `157/200`
- Learned-policy reporting should add rows and deltas; it should not replace the
  preserved baseline record.
- Reward remains separate from comparison metrics even if optional shaping is
  later tested.
- Do not revise the accepted baseline benchmark module unless a future thread
  gets explicit approval to do so; learned evaluation can reuse its metric
  schema without overwriting its role.

## Boundary: Phase 5 learning vs Phase 4 corrective work vs later tracks

Phase 5 learning work includes:

- feature extraction over the accepted observation
- masked learner action selection over the accepted action ids/masks
- training-loop implementation for one chosen learner
- learned-policy evaluation on the preserved seed sets
- bounded analysis of failure modes and, if needed, one explicit shaping retry

Phase 4 corrective work begins only when:

- a narrow bug is found in the accepted env boundary itself
- the current legal mask/action catalog is incorrect by repo evidence
- `reset` / `step` determinism or termination semantics are wrong
- the required fix restores the accepted contract rather than redesigning it

If such a bug appears, stop the blocked Phase 5 package, open a narrow
corrective thread, and then return to the learning package.

Stronger search/planning baseline work begins only when:

- a new search, rollout, or planning baseline is being designed
- the baseline comparison matrix is being widened beyond the accepted
  random/heuristic reference plus the first learner
- the project question has shifted from "is the wrapper learnable?" to "what is
  the stronger non-learning ceiling on Mission 1?"

Later Mission 3/4 content extension begins only when:

- new terrain/unit/objective families are being added to the domain engine
- multiple-start-hex support or objective-dispatch generalization is being
  implemented
- Mission 1 is no longer the right content slice for the next answerable
  project question

## Operational rules for Phase 5

- this master-thread owns the Phase 5 packet, status block, acceptance notes,
  and closeout docs
- Delivery Threads own implementation for one package only and normally make
  implementation commits after acceptance
- keep Phase 5 to Delivery A plus Delivery B, with optional Delivery C only if
  the terminal-only pass leaves the learnability decision unresolved
- do not mix learning packages with Mission 3/4 extension, stronger
  search/planning baselines, or generic experiment-platform buildout
- if a package needs to revise the accepted observation/action/reward boundary,
  return to the Phase Master Thread before editing
- routine package verification should continue to include:
  - `.venv/bin/pytest -q`
  - `.venv/bin/ruff check src tests`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`
- rerun the accepted 200-seed baseline benchmark only if a Phase 5 package
  touches the preserved baseline comparison surface directly; otherwise preserve
  the accepted snapshot and compare learned results against it

Allowed status values:

- `pending`
- `in_progress`
- `completed`
- `blocked`

## Phase 5 status block

Update this block only from a planning / audit / master-thread after checking
repo state against the package criteria.

- Package A: completed
- Package B: pending
- Package C: pending / optional
- Phase 5 overall: pending
- Planning audit date: March 10, 2026
- Package A acceptance verification date: March 10, 2026
- Blocking findings before Delivery A: none

## Package A - Learning adapter and experiment contract foundation

Status:

- completed
- accepted by the Phase 5 master-thread; implementation diff is commit-ready

Goal:

- freeze the first learner choice, dependency boundary, feature-adapter seam,
  and evaluation contract on top of the accepted `Mission1Env` surface without
  mixing in reward-shaping or closeout work

Concrete deliverables:

- one thin learning-side observation/feature adapter derived from the accepted
  structured observation
- one masked action-selection seam that consumes the accepted legal ids/masks
- one bounded learner/policy module for the chosen actor-critic baseline
- one narrow training/evaluation configuration surface for this learner only
- one evaluation path for learned policies that emits the accepted Phase 3
  metric schema without rewriting the baseline benchmark module
- only the minimal dependency and packaging changes needed to support the above

Likely files / subsystems touched:

- `pyproject.toml` if Package A adds a bounded numerical/model dependency
- `src/solo_wargame_ai/agents/` for learned-policy modules
- `src/solo_wargame_ai/eval/` for learned-policy episode/eval helpers
- `src/solo_wargame_ai/cli/` for a thin Phase 5 train/eval operator surface
- `configs/experiments/` only if one or two narrow experiment presets clearly
  improve reproducibility
- focused tests under `tests/` for feature extraction, mask handling, and
  learned-policy contract wiring

Required tests / verification:

- focused tests that feature extraction is deterministic and only depends on the
  accepted env observation surface
- focused tests that masked action selection never emits an illegal action id
- focused tests that learned-policy evaluation reproduces the accepted metric
  schema on fixed seeds
- `.venv/bin/pytest -q`
- `.venv/bin/ruff check src tests`
- `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
- `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`

Risks / traps:

- changing the accepted env contract instead of adapting to it
- creating a generic experiment/config platform instead of one learner seam
- coupling the learner to domain internals or `HeuristicAgent` helpers
- introducing multiple algorithms before the first one is even comparable

Completion criteria:

- Package B can train and evaluate one learner without reopening dependency,
  adapter, or metric-comparability questions
- the feature and mask path is deterministic and testable
- the accepted Phase 3 comparison anchor remains intact

Acceptance record:

- accepted implementation surface:
  - `pyproject.toml`
  - `src/solo_wargame_ai/agents/feature_adapter.py`
  - `src/solo_wargame_ai/agents/learned_policy.py`
  - `src/solo_wargame_ai/agents/masked_action_selection.py`
  - `src/solo_wargame_ai/agents/masked_actor_critic.py`
  - `src/solo_wargame_ai/eval/learned_policy_eval.py`
  - `src/solo_wargame_ai/eval/phase5_seed_policy.py`
  - focused Package A tests under `tests/`
- acceptance verification:
  - `.venv/bin/pytest -q tests/test_phase5_feature_adapter.py tests/test_phase5_learned_policy_eval.py tests/test_phase5_masked_actor_critic.py tests/test_phase5_torch_actor_critic.py`
    -> `10 passed in 1.12s`
  - `.venv/bin/pytest -q` -> `185 passed in 2.38s`
  - `.venv/bin/ruff check src tests` -> `All checks passed!`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
    preserved the accepted Phase 3 reference:
    `random` `2/16` wins vs `heuristic` `11/16` wins
  - `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`
    preserved the accepted Phase 4 smoke output:
    `action_catalog_size=32`, `decision_steps=35`,
    `terminal_outcome=defeat`, `final_reward=-1.0`
- accepted boundary notes:
  - Delivery A froze the first learner boundary around a masked episodic
    actor-critic seam, a deterministic observation-only feature adapter, and a
    learned-policy evaluation path that reuses the accepted Phase 3 metric
    schema
  - training seeds remain explicitly separated from accepted evaluation seeds
  - `torch` is the intended learner dependency; `numpy` is also allowed here as
    an operator-approved bootstrap companion dependency for local torch install
    stability and should not be treated as a broader framework decision

Commit shape:

- one commit preferred
- two commits acceptable only if dependency setup and the learning-side adapter
  surface are substantially cleaner to review separately

Analysis-before-edit:

- required

## Package B - Terminal-only first learner pass and baseline comparison

Status:

- pending

Goal:

- implement and run the chosen learner end-to-end on the accepted terminal-only
  Mission 1 env contract and compare the result against the preserved Phase 3
  references

Concrete deliverables:

- the first bounded training loop for the chosen learner
- deterministic training-seed protocol and checkpoint-selection policy
- one accepted train-smoke command and one accepted learned-policy evaluation
  command
- final learned-policy comparison on the fixed 16-seed smoke set and the
  accepted 200-seed benchmark seed set
- a compact report for the Phase Master Thread stating whether the minimum
  success bar was met and whether optional Package C is needed

Likely files / subsystems touched:

- `src/solo_wargame_ai/agents/`
- `src/solo_wargame_ai/eval/`
- `src/solo_wargame_ai/cli/`
- optional narrow presets under `configs/experiments/`
- local `outputs/` artifacts such as checkpoints or reports if the package needs
  them

Required tests / verification:

- focused tests for any nontrivial rollout/training state handling introduced by
  the package
- `.venv/bin/pytest -q`
- `.venv/bin/ruff check src tests`
- `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
- `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`
- one accepted Phase 5 train-smoke run
- one accepted learned-policy evaluation on the 16-seed smoke set
- one accepted learned-policy evaluation on the 200-seed benchmark set

Risks / traps:

- conflating reward optimization with benchmark comparison metrics
- hand-tuning against the preserved benchmark snapshot instead of using a fixed
  protocol
- opening checkpoint-management, reporting, or dashboard architecture that is
  larger than the first learner itself
- declaring success from one lucky seed without the fixed final evaluation

Completion criteria:

- one terminal-only learner runs end-to-end through training and evaluation
- final reporting includes the accepted comparison metrics and an explicit
  success/failure verdict against the minimum bar
- the package returns a clear recommendation about whether Package C is needed

Commit shape:

- one coherent commit preferred
- split only if the training loop and the learned-policy evaluation/reporting
  surface are materially cleaner to review separately

Analysis-before-edit:

- straight to implementation after Package A is accepted

## Package C - Optional shaping or blocker-response pass

Status:

- pending / optional

Goal:

- only if Package B fails to answer the learnability question cleanly, run one
  bounded follow-up that isolates either reward sparsity or a narrow blocker
  without reopening the whole phase

Concrete deliverables:

- exactly one of:
  - one explicit shaped-reward variant on top of the accepted env contract
  - one narrow corrective bridge around a confirmed blocker
- an A/B comparison against the terminal-only Package B result on fixed seeds
- a final recommendation stating whether the next macro-step should be env
  iteration, stronger baselines/search, or later content extension

Likely files / subsystems touched:

- `src/solo_wargame_ai/env/` only if a confirmed Phase 4 corrective bug exists
  or the shaped reward is implemented as an explicit wrapper variant
- `src/solo_wargame_ai/agents/`
- `src/solo_wargame_ai/eval/`
- `src/solo_wargame_ai/cli/`
- narrow doc notes only if the package reveals a stable contract correction

Required tests / verification:

- `.venv/bin/pytest -q`
- `.venv/bin/ruff check src tests`
- `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
- `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`
- fixed-seed comparison between the terminal-only result and the Package C
  variant
- one final learned-policy evaluation on the accepted 200-seed benchmark set

Risks / traps:

- hiding an env redesign inside a "reward shaping" package
- turning Phase 5 into a reward/hyperparameter campaign
- mutating the default `Mission1Env` reward contract instead of adding an
  explicit experimental variant
- mixing a real Phase 4 bug fix with broader learning redesign in the same
  thread

Completion criteria:

- the package isolates whether the failure came from sparse reward or from a
  separate blocker
- the Phase Master Thread can make the end-of-phase decision without opening
  additional learning packages

Commit shape:

- one small commit only if the package is actually opened

Analysis-before-edit:

- required

## Recommended Delivery Thread sequence for Phase 5

Preferred sequence:

1. Delivery A
2. Delivery B
3. Delivery C only if Delivery B reports either:
   - below-minimum terminal-only results with evidence that sparse reward is the
     likely blocker
   - or a narrow confirmed blocker that needs one bounded follow-up

Do not mix in one thread:

- Package A contract/adapter/dependency decisions with Package B training runs
- Package B terminal-only training work with Package C shaping or corrective
  work
- any Phase 5 package with Mission 3/4 content extension
- any Phase 5 package with stronger search/planning baseline design
- any Phase 5 package with generic experiment-platform architecture

Straight to implementation is appropriate when the package scope is:

- implementing Package B on top of an accepted Package A contract
- adding a thin train/eval operator surface that does not redefine env or
  reward contracts

Analysis-before-edit is required when a thread proposes to change:

- the accepted observation boundary
- the fixed staged action-catalog semantics
- legality ownership or invalid-action policy
- reward semantics beyond the accepted terminal-only default
- dependency strategy for the first learner
- the preserved relationship between learned evaluation and the accepted Phase 3
  benchmark reference

## Archived Phase 4 control record

- Accepted implementation commits:
  - `ad57a63 phase4: add mission1 env contract foundation`
  - `a4eadc4 fix: re-ignore env cache artifacts`
  - `5bd81a3 phase4: add mission1 env wrapper semantics`
  - `79f188f phase4: sync env operator surface and public docs`
  - `0e4a6a8 docs: close phase4 rl-environment`
- Final accepted verification:
  - `.venv/bin/pytest -q`
  - `.venv/bin/ruff check src tests`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`
- Accepted wrapper contract summary:
  - structured player-visible observation boundary
  - fixed 32-id Mission 1 action catalog
  - legality derived from the resolver
  - dependency-free `Mission1Env`
  - default terminal-only reward
  - `terminated=True` for victory and defeat, including turn-limit defeat
  - `truncated=True` only for external wrapper limits
- Detailed Phase 4 planning and acceptance history lives in:
  - `docs/internal/thread_reports/2026-03-10_phase4-master-thread.md`
  - `docs/internal/thread_reports/2026-03-10_phase4-package-a-acceptance.md`
  - `docs/internal/thread_reports/2026-03-10_phase4-package-b-acceptance.md`
  - `docs/internal/thread_reports/2026-03-10_phase4-package-c-review.md`
  - `docs/internal/thread_reports/2026-03-10_phase4-closeout.md`

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

## Decision after Phase 4 closeout

Recommended next macro-step:

- Phase 5 learning experiments planning

Rationale:

- the repository now has an accepted Mission 1 env boundary, legality surface,
  reward/termination contract, and thin operator smoke command
- the preserved Phase 3 baseline CLI remains intact as the accepted pre-RL
  comparison reference
- the next project question is no longer wrapper shape, but whether the current
  Mission 1 observation/action design is actually learnable
- Mission 3/4 content extension remains a later content track unless Phase 5
  evidence shows the accepted Mission 1 wrapper is too degenerate to answer the
  learning question cleanly

Closeout note:

- the accepted 200-seed Phase 3 benchmark snapshot remains:
  `random` `11/200` wins vs `heuristic` `157/200` wins
- the benchmark was not rerun at Phase 4 closeout because accepted Phase 4 work
  preserved the baseline comparison surface rather than modifying it directly

## Public docs after Phase 3 closeout

During closeout, `README.md` and `ROADMAP.md` were synced to reflect that:

- Phase 3 is complete
- the next macro-step is Phase 4 RL-environment planning
- the accepted manual Phase 3 rerun commands are now documented in `README.md`

Further public polish can happen later in separate docs-only threads.

## Public docs after Phase 4 closeout

During closeout, public docs were synced to reflect that:

- the first Mission 1 RL-friendly wrapper is accepted
- the default reward remains terminal-only and `terminated` / `truncated`
  semantics are explicit
- the accepted manual Phase 4 env smoke command is now documented
- the preserved Phase 3 baseline CLI remains the comparison reference
- the next macro-step is Phase 5 learning experiments planning

# Execution Plan

## Purpose

This file is the current master control surface for repository-level planning,
dispatch, and closeout.

As of March 10, 2026, Phases 1 through 5 are complete and archived by
repository evidence.
The active planning problem is no longer "how to finish Mission 1", "how to
harden the accepted engine", "how to open Phase 3 baselines", "how to open
Phase 4 RL-environment planning", or "whether the accepted Mission 1 wrapper is
learnable", but "which post-first-RL macro-step is justified next, with
stronger baselines/search as the default target unless new evidence says
otherwise."

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
- preserve the accepted Phase 5 packet, closeout record, and external-audit
  outcome,
- avoid reopening completed Delivery A / B / C work accidentally,
- recover the accepted baseline, wrapper, and benchmark references quickly,
- point the next planning thread toward the post-first-RL macro-step and later
  decision gates.

## Current checkpoint

- Accepted milestones:
  - Phase 1 complete
  - Phase 2 complete
  - Phase 3 complete
  - Phase 4 complete
  - Phase 5 complete
- Local tags:
  - `phase1-complete`
  - `phase2-complete`
  - `phase3-complete`
  - `phase4-complete`
  - `phase5-complete`
- Repository state checked on March 10, 2026 before opening this Phase 6
  master-thread:
  - `git status --short` was empty
  - `git log --oneline --decorate -12` showed `HEAD` on
    `ab20cee docs: refine phase6 roadmap and docs sync`
  - `git show --no-patch --decorate phase1-complete` resolved to
    `d6445d9 docs: sync public handoff after phase1 completion`
  - `git show --no-patch --decorate phase2-complete` resolved to
    `1ef74ab docs: finalize phase2 closeout handoff`
  - `git show --no-patch --decorate phase3-complete` resolved to
    `98519c7 docs: close phase3 baselines`
  - `git show --no-patch --decorate phase4-complete` resolved to
    `0e4a6a8 docs: close phase4 rl-environment`
  - `git show --no-patch --decorate phase5-complete` resolved to
    `9d8beb9 docs: close phase5 learning experiments`
  - `.venv/bin/pytest -q` passed with `197 passed in 3.51s`
  - `.venv/bin/ruff check src tests` passed with `All checks passed!`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
    succeeded with the preserved `random` `2/16` wins vs `heuristic`
    `11/16` wins reference
  - `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`
    succeeded with `action_catalog_size=32`, `decision_steps=35`,
    `terminal_outcome=defeat`, `final_reward=-1.0`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase5_summary --artifact-dir outputs/phase5/train_seed_101_ep_2000 --artifact-dir outputs/phase5/train_seed_202_ep_2000 --artifact-dir outputs/phase5/train_seed_303_ep_2000`
    confirmed `best_benchmark_wins: 144`, `median_benchmark_wins: 133`,
    `heuristic_anchor_wins: 157`, and `package_c_recommendation: Package C not recommended; proceed toward end-of-phase evaluation`

Accepted runtime surface after Phase 5 closeout:

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
- `agents/feature_adapter.py`, `agents/learned_policy.py`,
  `agents/masked_action_selection.py`, and `agents/masked_actor_critic.py`
  remain the accepted Phase 5 learning-side library surface.
- `eval/learned_policy_eval.py` remains the accepted learned-policy evaluation
  seam over the frozen Mission 1 env boundary.
- `cli/phase3_baselines.py` and `cli/phase4_env_smoke.py` remain the accepted
  preserved operator references.
- `cli/phase5_train.py`, `cli/phase5_learned_policy_eval.py`, and
  `cli/phase5_summary.py` remain the accepted Phase 5 operator surfaces.
- `pyproject.toml` now carries the bounded `numpy` / `torch` learning
  dependency pair, while `configs/` still contains only the Mission 1 mission
  config and no broader experiment-platform surface.
- `outputs/phase5/` contains the accepted first-learner artifacts and aggregate
  summary files used as preserved comparison evidence.

## Strategic update after opening the Phase 6 master-thread

Current planning assumptions for the active phase:

- Phase 6 is not a continuation of Phase 5 learning implementation and not a
  default Mission 3/4 extension track.
- The accepted Mission 1 engine, env, random/heuristic baselines, and Phase 5
  learner result are the stable foundation.
- The two active questions are:
  - how much headroom remains on Mission 1 for a stronger non-learning baseline
    or bounded search/planning agent
  - which repo-structure and naming fixes are worth doing now before another
    research/content cycle lands on top of the current layout
- Prefer one bounded stronger baseline/search package over a family of new
  algorithms.
- Prefer one bounded hygiene package over a broad refactor campaign.
- Do not reopen the accepted env observation/action/reward boundary without
  strong repo evidence from Phase 6 work itself.
- Do not open Mission 3/4 content or generic experiment/search infrastructure by
  default.

## Phase 6 objective

Phase 6 is now defined as:

> Use the accepted Mission 1 stack to measure post-first-RL headroom and remove
> the smallest structure/naming frictions that already impede further work,
> without turning the repo into a refactor campaign or widening automatically
> into new mission content.

Desired outcome:

- one bounded hygiene pass leaves the repo easier to navigate and extend
- one stronger Mission 1 non-learning baseline/search result exists on the
  preserved comparison protocol
- the phase ends with a documented gate between:
  - more Mission 1 strengthening/search
  - Mission 3/4 content extension
  - a narrow env/action corrective iteration only if Phase 6 produces strong
    contrary evidence

## Phase 6 planning audit findings

- Current repo state is clean and reproducible from the accepted Phase 5
  baseline:
  - `git status --short` was empty
  - `.venv/bin/pytest -q` passed with `197 passed in 3.51s`
  - `.venv/bin/ruff check src tests` passed with `All checks passed!`
  - the preserved Phase 3 smoke reference and Phase 4 env smoke output still
    match the accepted values
  - `phase5_summary` confirms the accepted aggregate result `best 144/200`,
    `median 133/200`, `heuristic 157/200`
- The domain and env packages are mostly responsibility-named already and are
  acceptable as-is for Phase 6; they are not the main current naming problem.
- The most immediate repo-friction comes from durable library modules that still
  carry phase-history names:
  - `src/solo_wargame_ai/agents/phase5_training.py`
  - `src/solo_wargame_ai/eval/phase5_seed_policy.py`
  - `src/solo_wargame_ai/eval/phase5_reporting.py`
  - `src/solo_wargame_ai/eval/phase5_summary.py`
- Thin operator entrypoints under `src/solo_wargame_ai/cli/phase3_*`,
  `phase4_*`, and `phase5_*` are acceptable as phase-tagged operator surfaces
  and do not need to be renamed in the hygiene pass by default.
- `tests/` is still a single flat directory. That was acceptable during early
  growth, but with more than 40 test files it now materially slows navigation
  and makes phase-history naming linger longer than it should.
- `HeuristicAgent` is already a Mission-1-specific lookahead baseline with
  synthetic-state assistance. The next high-value baseline should therefore be
  an explicit bounded rollout/search/hybrid agent, not "HeuristicAgent v2"
  through more ad hoc scoring rules.
- Known audit items `legal_actions.py` growth and replay draw-prediction
  coupling remain real, but they are still later-scope concerns unless Phase 6
  search work exposes a direct blocker.

## Active follow-ups and assumptions for Phase 6

Active follow-ups from `docs/internal/independent_audit_followups.md`:

- `P4-R4` remains active as a preservation rule:
  - keep the accepted Phase 3 smoke/benchmark references explicit and reusable
- `C6` remains active as a caution:
  - do not promote Mission-1-specific heuristic coupling into the durable future
    agent contract just because a stronger baseline may reuse it as a rollout
    policy or comparison target

Not active by default in this phase unless a concrete blocker appears:

- `C1` replay draw-prediction coupling
- `C2` `legal_actions.py` growth / separation
- `C3` multiple-start-hex support
- `C4` objective-dispatch generalization
- `C5` synthetic fixtures
- `T1` through `T4` tooling backlog items

Active assumptions from current public docs:

- `ASSUMPTIONS.md: O2` / `O6`
  - later agents may derive their own features, but the accepted observation
    boundary stays intact
- `ASSUMPTIONS.md: O3`
  - do not introduce new macro-action abstractions for Phase 6 search/baselines
    by default
- `ASSUMPTIONS.md: O4` and `docs/reward_design.md`
  - Phase 6 does not reopen reward shaping or the default terminal-only env
    contract

## Accepted Phase 6 scope

In scope:

- one bounded repository-hygiene package focused on naming/layout clarity
- one stronger Mission 1 non-learning baseline/search package on top of the
  accepted domain/env stack
- only the minimal evaluation/reporting widening needed to compare that new
  baseline against the preserved references
- internal planning/status docs and local thread reports for the active phase
- Phase Master acceptance, closeout, and next-step gate after the comparison is
  in hand

Out of scope:

- implementation work from this Phase Master Thread
- Mission 3/4 or broader content/rule expansion
- reopening the accepted env observation/action/reward boundary without strong
  new evidence
- reward shaping work
- a generic search, experiment, or benchmark platform
- broad domain refactors motivated mainly by anticipated scale
- renaming accepted thin phase operator CLIs, milestone tags, or archived Phase
  5 artifact directories purely for aesthetics
- tooling/polish backlog such as `mypy`, broader Ruff, coverage, or multi-
  version CI unless separately approved later

## Phase 6 planning decisions

- Delivery order:
  - start with a bounded cleanup package before stronger baseline/search work
- Why cleanup comes first:
  - current phase-history naming in durable library modules and the flat
    `tests/` directory are already obstructing the very next package
  - doing the bounded cleanup before new baseline/search code lands prevents
    another round of imports/tests from immediately being built on confusing
    names
  - the cleanup budget is small enough to avoid becoming a separate refactor
    campaign
- Bounded cleanup target:
  - rename durable library modules by responsibility rather than phase history
  - regroup tests by subsystem when the move clearly improves navigation
  - keep thin phase CLI names, thread reports, milestone tags, and `outputs/`
    artifact names as historical/operator surfaces
  - do not change accepted behavior or public env/domain contracts
- Stronger baseline/search direction:
  - prefer one explicit stochastic rollout/search or hybrid search baseline over
    the accepted domain-action contract
  - concretely, score the current legal action set via bounded forward
    simulation from the resolver/state surface, optionally using the accepted
    heuristic policy as a rollout or leaf policy
  - do not start with another hand-tuned heuristic-only rewrite
  - do not build a generic search framework, MCTS toolkit, or env-level planner
    layer
- Comparison protocol:
  - keep the accepted Phase 3 anchors fixed at `random 11/200` and
    `heuristic 157/200`
  - keep the accepted Phase 5 learned references explicit:
    `best 144/200`, `median 133/200`, plus the recorded seed results
    `101 -> 144/200`, `202 -> 133/200`, `303 -> 121/200`
  - keep the existing `EpisodeMetrics` row mandatory:
    `wins`, `defeats`, `win_rate`, `defeat_rate`, `mean_terminal_turn`,
    `mean_resolved_markers`, `mean_removed_german`, `mean_player_decisions`
  - report search budget separately from outcome metrics:
    for example rollout count, depth cap, leaf policy, or other bounded compute
    knobs
- End-of-phase decision gate:
  - choose `more Mission 1 strengthening/search` only if the new stronger
    baseline beats the heuristic anchor by a material margin and still leaves a
    nontrivial instructive failure set
  - choose `Mission 3/4 content extension` if Phase 6 either:
    - fails to beat the heuristic anchor meaningfully, so more Mission 1
      baseline work is unlikely to pay back
    - or drives Mission 1 close enough to saturation that additional gains would
      mostly be compute-budget polishing rather than new structural insight
  - choose `targeted env/action iteration` only if the stronger-baseline work
    produces concrete evidence that the accepted wrapper/action surface itself is
    the next blocker; that is not the default expectation

## Comparability policy with the accepted Phase 3 and Phase 5 references

- Preserve the accepted Phase 3 smoke and benchmark references as fixed anchor
  values, not moving targets:
  - smoke: `random 2/16` vs `heuristic 11/16`
  - benchmark: `random 11/200` vs `heuristic 157/200`
- Evaluate the stronger Phase 6 baseline on the same Mission 1 config and the
  same fixed env seed sets:
  - smoke: `0..15`
  - benchmark: `0..199`
- Keep the accepted Phase 5 learned-policy aggregate explicit in docs and final
  comparison reports rather than re-measuring Phase 5 from scratch.
- If a Phase 6 package touches the preserved Phase 3 benchmark harness or the
  accepted random/heuristic implementations directly, rerun the full
  `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode benchmark`
  check and confirm the accepted `11/200` and `157/200` anchors are unchanged.
- Reward stays separate from comparison metrics and from search/planning
  scoring.
- Do not reinterpret the accepted Phase 3 or Phase 5 references as training
  targets or reward terms.

## Boundary: cleanup vs stronger baselines vs later tracks

Phase 6 repository cleanup includes:

- responsibility-based renaming of durable library modules
- import updates required by those renames
- regrouping existing tests into clearer subsystem directories
- minimal docs updates needed to explain the intended long-lived repo layout

Phase 6 stronger baselines/search includes:

- one stronger Mission 1 non-learning baseline/search agent
- only the evaluation/reporting code needed to compare it on the preserved seed
  sets and metric schema
- a thin operator surface for Phase 6 comparison runs if the package needs one

Later Mission 3/4 content extension begins only when:

- new terrain/unit/objective families are being added
- Mission 1-only guards such as multiple-start-hex limits or Mission 1
  objective dispatch are being widened
- the project has already decided that another Mission 1 strengthening cycle is
  not the best next investment

Later broader tooling/platform work includes:

- generic experiment config layers
- generic search frameworks or pluggable planning backends
- type-checking and coverage expansion
- wider CI/runtime matrix work
- replay-system redesign for future RNG-heavy content

## Operational rules for Phase 6

- this Phase Master Thread owns the Phase 6 packet, status block, acceptance
  notes, and closeout docs
- Delivery Threads own implementation for one package only and normally make the
  implementation commit after acceptance
- keep Phase 6 to Delivery A plus Delivery B, with Delivery C only if Package B
  does not already produce a closeout-ready comparison/report surface
- do not mix repo cleanup with stronger-baseline implementation in the same
  Delivery Thread
- do not mix any Phase 6 package with Mission 3/4 content work or tooling
  backlog
- if a package proposes to change domain/env/reward contracts, return to the
  Phase Master Thread before editing
- routine Phase 6 verification continues to include:
  - `.venv/bin/pytest -q`
  - `.venv/bin/ruff check src tests`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`
- Package A verification should additionally preserve at least one accepted
  Phase 5 operator surface
- Package B/C verification should include the new Phase 6 smoke/benchmark
  comparison command if introduced

Allowed status values:

- `pending`
- `in_progress`
- `completed`
- `blocked`
- `conditional`

## Phase 6 status block

Update this block only from a planning / audit / master-thread after checking
repo state against the package criteria.

- Package A: pending
- Package B: pending
- Package C: conditional
- Phase 6 overall: pending
- Planning audit date: March 10, 2026
- Blocking findings before Delivery A: none
- Preferred package order: Delivery A -> Delivery B -> Delivery C only if needed
- Closeout/tag gate: not ready

## Package A - Bounded repo hygiene and naming cleanup

Status:

- pending

Goal:

- remove the smallest repo-structure and naming frictions that already impede
  Phase 6 work without changing accepted behavior

Concrete deliverables:

- rename durable library modules in `agents/` and `eval/` by responsibility
  rather than phase history where the current names now describe historical
  origin more than stable purpose
- keep thin phase CLI names and artifact paths unchanged unless a rename is
  required only at the import level
- regroup the flat `tests/` root into clearer subsystem directories such as
  `domain/`, `env/`, `agents/`, `eval/`, `cli/`, and `integration/` if the move
  remains mechanical and low-risk
- update internal layout/control docs to record the intended long-lived naming
  policy

Likely files / subsystems touched:

- `src/solo_wargame_ai/agents/`
- `src/solo_wargame_ai/eval/`
- import sites under `src/solo_wargame_ai/cli/`
- `tests/`
- `docs/internal/repo_layout.md`
- `docs/internal/execution_plan.md`

Required tests / verification:

- `.venv/bin/pytest -q`
- `.venv/bin/ruff check src tests`
- `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
- `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`
- `.venv/bin/python -m solo_wargame_ai.cli.phase5_summary --artifact-dir outputs/phase5/train_seed_101_ep_2000 --artifact-dir outputs/phase5/train_seed_202_ep_2000 --artifact-dir outputs/phase5/train_seed_303_ep_2000`
- one stored-checkpoint Phase 5 learned-policy smoke eval if Package A renames
  imports used by the learned-policy CLI path

Risks / traps:

- letting "cleanup" turn into a broad architecture redesign
- renaming operator-facing phase CLIs or artifact directories that are already
  useful historical anchors
- mixing behavior changes with mechanical moves/renames
- inventing a deep test-fixture refactor instead of a simple directory
  regrouping

Completion criteria:

- durable library/module names are clearer than before the package
- tests are easier to navigate than the current flat dump-style root
- accepted behavior and operator outputs stay intact
- Package B can add a new baseline without immediately adding more phase-history
  naming debt

Commit shape:

- one refactor/docs commit preferred
- split only if test-directory regrouping is materially cleaner to review
  separately from library-module renames

Analysis-before-edit:

- required

## Package B - Stronger Mission 1 rollout/search baseline

Status:

- pending

Goal:

- add one stronger non-learning Mission 1 baseline that measures headroom above
  the accepted heuristic and first learner without widening scope into a search
  platform

Concrete deliverables:

- one bounded stronger baseline/search agent over the accepted domain-action
  contract
- one explicit deterministic search/rollout budget policy
- only the minimal harness/reporting additions needed to evaluate the new agent
  on the preserved smoke and benchmark seed sets
- one thin Phase 6 operator surface for smoke/benchmark comparison if the
  package needs it
- one package report that states whether the new baseline materially changes the
  current headroom picture

Likely files / subsystems touched:

- `src/solo_wargame_ai/agents/`
- `src/solo_wargame_ai/eval/`
- optional thin operator entrypoint under `src/solo_wargame_ai/cli/`
- focused tests under `tests/agents/`, `tests/eval/`, and `tests/cli/`

Required tests / verification:

- focused tests for legality preservation, deterministic seed/budget behavior,
  and the search agent's action-selection contract
- `.venv/bin/pytest -q`
- `.venv/bin/ruff check src tests`
- `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
- `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`
- one Phase 6 stronger-baseline smoke run
- one Phase 6 stronger-baseline benchmark run on `0..199`
- rerun `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode benchmark`
  if Package B touched the preserved Phase 3 benchmark surface directly

Risks / traps:

- implementing another brittle heuristic-only score sheet instead of explicit
  bounded search/rollout
- building a generic search framework rather than one answer-oriented baseline
- coupling the new baseline to RL artifacts or reward shaping
- smuggling env/action redesign into a baseline/search package
- weakening the preserved Phase 3 comparison reference while trying to widen it

Completion criteria:

- one stronger baseline/search result exists on the accepted 200-seed benchmark
- the result is comparable against `random`, `heuristic`, and the accepted
  Phase 5 learned references on the same metric schema
- the package returns a clear verdict about whether heuristic remains the
  practical ceiling on Mission 1

Commit shape:

- one implementation commit preferred
- two commits acceptable only if the new agent and the minimal comparison
  surface are materially cleaner to review separately

Analysis-before-edit:

- straight to implementation after Package A is accepted

## Package C - Optional comparison/reporting finish for the Phase 6 gate

Status:

- conditional

Goal:

- only if Package B does not already leave the Phase Master Thread with a clean
  closeout-ready comparison surface, add the smallest extra reporting/evaluation
  slice needed to make the final macro-step decision cleanly

Concrete deliverables:

- at most one compact comparison/report surface showing:
  - preserved Phase 3 anchors
  - accepted Phase 5 learned references
  - the new stronger Phase 6 baseline result
- any narrow payload/report formatting needed for that matrix
- a closeout-ready recommendation input for the Phase Master Thread

Likely files / subsystems touched:

- `src/solo_wargame_ai/eval/`
- optional thin operator entrypoint under `src/solo_wargame_ai/cli/`
- focused reporting tests under `tests/eval/` or `tests/cli/`
- local report artifacts under `outputs/` if useful

Required tests / verification:

- focused tests for any new summary/report formatting
- `.venv/bin/pytest -q`
- `.venv/bin/ruff check src tests`
- `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
- `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`
- the final Phase 6 comparison command/report if Package C is opened

Risks / traps:

- turning a closeout-support package into another algorithm package
- changing metric schema or anchor values late in the phase
- building a dashboard or generic reporting platform when one compact report
  would answer the question
- mixing phase closeout docs and implementation changes in a way that obscures
  review

Completion criteria:

- the Phase Master Thread can close Phase 6 without opening another
  implementation package
- the comparison matrix is compact, explicit, and anchored to the preserved
  references

Commit shape:

- one small eval/reporting commit only if Package C is actually opened

Analysis-before-edit:

- required

## Recommended Delivery Thread sequence for Phase 6

Preferred sequence:

1. Delivery A
2. Delivery B
3. Delivery C only if Delivery B does not already produce a clean closeout-ready
   comparison/report surface

Do not mix in one thread:

- Package A repo hygiene with Package B stronger-baseline implementation
- Package B search/baseline work with Package C closeout-support reporting
- any Phase 6 package with Mission 3/4 content extension
- any Phase 6 package with broad domain refactors such as `legal_actions.py`
  decomposition unless a concrete blocker is proven first
- any Phase 6 package with generic experiment/search platform buildout

## Archived Phase 5 control record

- Accepted implementation commits:
  - `035d8f1 phase5: add learning adapter and evaluation foundation`
  - `c6d2142 phase5: add bounded learner train and eval flow`
  - `9d8beb9 docs: close phase5 learning experiments`
- Accepted verification at closeout:
  - `.venv/bin/pytest -q`
  - `.venv/bin/ruff check src tests`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase5_summary --artifact-dir outputs/phase5/train_seed_101_ep_2000 --artifact-dir outputs/phase5/train_seed_202_ep_2000 --artifact-dir outputs/phase5/train_seed_303_ep_2000`
- Accepted aggregate result:
  - `101 -> 144/200`
  - `202 -> 133/200`
  - `303 -> 121/200`
  - `best 144/200`
  - `median 133/200`
  - Package C was not opened
- Detailed Phase 5 planning and acceptance history lives in:
  - `docs/internal/thread_reports/2026-03-10_phase5-master-thread.md`
  - `docs/internal/thread_reports/2026-03-10_phase5-delivery-a-dispatch.md`
  - `docs/internal/thread_reports/2026-03-10_phase5-package-a-acceptance-review.md`
  - `docs/internal/thread_reports/2026-03-10_phase5-package-b-acceptance-review.md`
  - `docs/internal/thread_reports/2026-03-10_phase5-closeout.md`

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

## Decision after Phase 5 closeout

Recommended next macro-step:

- stronger baselines/search planning inside the post-first-RL expansion track

Rationale:

- the accepted Mission 1 wrapper/action/reward surface was shown to be learnable
  without shaping
- the best bounded Phase 5 learner reached `144/200` wins and the median across
  accepted training seeds reached `133/200`, comfortably above the preserved
  random reference of `11/200`
- the best learned result remains below the preserved heuristic anchor
  `157/200`, so the next question is headroom above the first learner rather
  than whether the wrapper itself works
- external audit did not justify reopening Package C, env iteration, or Mission
  3/4 content work inside Phase 5

Closeout note:

- the accepted Phase 5 aggregate summary records:
  `101 -> 144/200`, `202 -> 133/200`, `303 -> 121/200`
- the minimum-success verdict is `met`
- Package C remained closed and was not needed for closeout

## Public docs after Phase 5 closeout

During closeout, public docs were synced to reflect that:

- Phase 5 learning experiments are complete
- the repository now includes accepted Phase 5 train / learned-eval / summary
  operator commands
- the next macro-step is stronger baselines/search planning rather than more
  Phase 5 delivery work

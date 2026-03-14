# Execution Plan

## Purpose

This file is the current master control surface for repository-level planning,
dispatch, and closeout.

As of March 12, 2026, the original six-phase roadmap is complete by repository
evidence.
The active planning problem is no longer "whether to open one more Mission 3
search packet," but "how to pause cleanly after Mission 3
search-strengthening, preserve the accepted results, and queue the smallest
next packet that reduces risk before Mission 3 env/wrapper extension."

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
- preserve the accepted Phase 6 packet, closeout record, and decision gate,
- preserve the accepted Mission 3 baselines/search re-establishment packet and
  its historical reference surface,
- preserve the accepted Mission 3 search-strengthening packet and its
  historical-vs-strengthened reference surfaces,
- avoid reopening completed Delivery A / B / C work accidentally,
- recover the accepted baseline, wrapper, and benchmark references quickly,
- point the next planning thread toward the active packet backlog and later
  decision gates.

## Current checkpoint

- Accepted milestones:
  - Phase 1 complete
  - Phase 2 complete
  - Phase 3 complete
  - Phase 4 complete
  - Phase 5 complete
  - Phase 6 complete
  - Mission 3 vertical-slice packet complete
  - Mission 3 baselines/search re-establishment packet complete
  - Mission 3 search-strengthening packet complete
- Local tags:
  - `phase1-complete`
  - `phase2-complete`
  - `phase3-complete`
  - `phase4-complete`
  - `phase5-complete`
  - `phase6-complete`
- Repository state rechecked on March 12, 2026 after Mission 3 search
  strengthening closeout and before the next packet is opened:
  - `git status --short` showed only untracked
    `docs/internal/mission3_cross_mission_probes.md`, intentionally left
    outside the tracked packet closeout pending later Super Master review
  - `git log --oneline --decorate -12` showed `HEAD` on
    `aece79e docs: close mission3 search strengthening packet`
  - `.venv/bin/pytest -q` passed with `236 passed`
  - `.venv/bin/ruff check src tests` passed with `All checks passed!`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
    succeeded with the preserved `random` `2/16` wins vs `heuristic`
    `11/16` wins reference
  - `.venv/bin/python -m solo_wargame_ai.cli.phase6_stronger_baseline --mode benchmark`
    confirmed `rollout 195/200`, versus preserved anchors `random 11/200`,
    `heuristic 157/200`, and accepted learned references `best 144/200`,
    `median 133/200`
  - `.venv/bin/python -m solo_wargame_ai.cli.mission3_comparison --mode smoke`
    confirmed the accepted Mission 3 smoke reference surface:
    `random 0/16`, `heuristic 7/16`, `rollout-search 8/16`
  - `.venv/bin/python -m solo_wargame_ai.cli.mission3_comparison --mode benchmark`
    confirmed the accepted Mission 3 benchmark reference surface:
    `random 0/200`, `heuristic 72/200`, `rollout-search 105/200`
  - `.venv/bin/python -m solo_wargame_ai.cli.mission3_comparison --mode benchmark --surface strengthened`
    confirmed the accepted strengthened Mission 3 benchmark result:
    `rollout-search-strengthened 171/200`

Accepted runtime surface after Mission 3 search strengthening closeout:

- `Mission` remains static scenario data loaded from config.
- `GameState` remains runtime truth with explicit staged decision contexts.
- `domain/resolver.py` remains the accepted playable engine entry path.
- `io/replay.py` remains a replay adapter over the resolver path, not a second
  engine.
- `agents/base.py` records the accepted Phase 3 domain-action contract.
- `RandomAgent` remains the accepted reusable floor baseline on the domain-
  action contract.
- `HeuristicAgent` remains the accepted Mission-1-specific heuristic baseline,
  with the preserved Mission 1 benchmark fixed at `157/200`.
- `eval/episode_runner.py` and `eval/metrics.py` remain the accepted lower-
  level episode runner and aggregate-metrics seams for non-learning
  comparisons.
- `eval/benchmark.py` remains the preserved Mission 1 random-vs-heuristic
  comparison layer, not a generic cross-mission benchmark platform.
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
- `agents/masked_actor_critic_training.py`, `eval/learned_policy_seeds.py`,
  `eval/learned_policy_reporting.py`, and `eval/learned_policy_summary.py`
  are now the accepted responsibility-named durable library paths that replaced
  earlier phase-history module names during Delivery A.
- `agents/rollout_search_agent.py` is the accepted stronger Mission-1-specific
  planner-like baseline surface from Delivery B.
- `eval/rollout_baseline.py` is the accepted Mission 1 comparison layer for the
  stronger baseline against preserved Phase 3/5 anchors, not yet a broader
  multi-mission search/reporting platform.
- `agents/mission3_heuristic_agent.py` is the accepted Mission-3-local
  historical heuristic baseline surface, with the preserved benchmark fixed at
  `72/200`.
- `agents/mission3_rollout_search_agent.py` is the accepted Mission-3-local
  historical-plus-strengthened rollout-search surface, with the preserved
  historical benchmark fixed at `105/200` and the accepted strengthened local
  benchmark fixed at `171/200` under explicit fixed budgets.
- `eval/mission3_comparison.py` is the accepted Mission-3-only comparison layer
  for the preserved historical Mission 3 reference surface and the accepted
  strengthened Mission 3 packet surface, not a generic cross-mission reporting
  platform.
- `cli/phase3_baselines.py` and `cli/phase4_env_smoke.py` remain the accepted
  preserved operator references.
- `cli/phase5_train.py`, `cli/phase5_learned_policy_eval.py`, and
  `cli/phase5_summary.py` remain the accepted Phase 5 operator surfaces.
- `cli/phase6_stronger_baseline.py` is the accepted thin operator surface for
  rerunning the stronger Mission 1 rollout baseline on preserved smoke and
  benchmark seed sets.
- `cli/mission3_comparison.py` is the accepted thin Mission-3-only operator
  surface for rendering preserved historical, strengthened-only, and packet
  comparison reports without turning into a generic reporting platform.
- `pyproject.toml` now carries the bounded `numpy` / `torch` learning
  dependency pair, while `configs/missions/` now contains the accepted Mission
  1 and Mission 3 configs and no broader experiment-platform surface.
- `outputs/phase5/` contains the accepted first-learner artifacts and aggregate
  summary files used as preserved comparison evidence.

## Current post-Mission-3 planning decision

The original six-phase build sequence is finished, the first richer-content
packet has closed, the first Mission 3 comparison packet has closed, and the
bounded Mission 3 search-strengthening packet has now closed as well.
Future planning should therefore continue from the preserved historical Mission
3 surface plus the accepted strengthened local search surface.

The strategic pause after that closeout is now informed by three extra inputs:

- the local exploratory note `docs/internal/mission3_cross_mission_probes.md`,
  intentionally preserved as exploratory evidence rather than accepted
  benchmark truth;
- the independently reproduced March 12 hardening findings (`C7`-`C10`);
- an additional March 12 architecture/brainstorm review that argued for a
  small extension-seam packet before Mission 3 env work, rather than a broad
  reorg or another default Mission 3 tuning loop.

One additional local heuristic investigation is also worth preserving in the
tracked planning record:

- the local reports
  `docs/internal/thread_reports/2026-03-12_mission3_heuristic_isolated_followup.md`
  and
  `docs/internal/thread_reports/2026-03-14_mission3_heuristic_handoff_report.md`,
  which suggest that the strongest Mission 3 heuristic-side idea so far is not
  broad score tuning but current-turn reasoning plus a contestability gate:
  avoid revealing enemies that the current or remaining British units cannot
  realistically contest before handover.

Current recommended next packet:

- Mission 3 env-prep hardening and adapter seam

Why this is now preferred:

- the bounded Mission-3-local strengthening pass already succeeded materially:
  - historical benchmark: `rollout-search 105/200`
  - accepted strengthened benchmark:
    `rollout-search-strengthened 171/200`
- another default search packet would now be harder to justify as a bounded
  local-quality pass; it would more likely be a different research question,
  not a continuation of the just-closed packet
- the March 12 hardening findings (`C8`, `C9`, `C10`) are real and now
  confirmed by local reproduction:
  - mission validation is too permissive on important numeric fields
  - the loader accepts multi-start missions that runtime initialization still
    rejects
  - mission schema parsing is lenient on unknown keys and raw on missing keys
- the current top-level repo split still looks good, so a broad reorg is not
  justified
- however, the next env step should not harden `Mission1Env` into the
  permanent center or create a second isolated `MissionXEnv` island
- the best next move is therefore one bounded preparatory packet that:
  - strengthens the mission-config/schema boundary where recent audits found
    real issues
  - carves a narrow shared env-adapter seam
  - leaves Mission 3 env/wrapper implementation itself for the packet after
    that
- the local exploratory cross-mission probe note remains worth preserving, but
  not strong enough by itself to displace the new bounded prep packet
- the local heuristic reports also remain worth preserving, but they should be
  treated as exploratory evidence for a possible later bounded validation or
  productization question, not as accepted benchmark truth and not as a reason
  to reorder the current next packet

Likely follow-on packets after that:

1. Mission 3 env/wrapper extension
2. Mission 3 learning experiments
3. Cross-mission evaluation/reporting only when more than one mission is
   active enough to justify it
4. Mission 4 or another bounded richer content slice

Ranked backlog beyond the active next packet:

- High value:
  - Mission 3 env-prep hardening and adapter seam
  - Mission 3 env/wrapper extension
  - Mission 3 learning experiments
- Medium value:
  - Mission 4 or another bounded richer content slice once the Mission 3 env
    and learning path are healthier
  - a narrow follow-up on search transfer/localization only if a later thread
    opens that as a new explicit question rather than more generic tuning
  - observation/action redesign only if richer content shows the current
    wrapper is too Mission-1-shaped
  - synthetic fixtures and bounded maintainability work when broader content
    makes them pay back
  - cross-mission evaluation/reporting once more than one mission is active
  - splitting `legal_actions.py` or finishing broader test regrouping before
    additional rule families land, but not as the immediate next packet
- Lower priority:
  - another Mission 1 strengthening packet without a specific new research
    question
  - another default Mission 3 search-strengthening packet
  - generic experiment/search platform work
  - tooling campaigns not directly required by the next content slice
  - visualization/operator UX beyond thin debugging needs

Demoted for now:

- another default Mission 3 search-strengthening packet
- reopening Mission 3 baselines/search re-establishment as an ad hoc quality
  tail
- another default Mission 1 strengthening/search packet
- broad reward/env redesign before richer content creates evidence for it
- a broad top-level repo reorganization
- generic search, experiment, or platform buildout
- tooling campaigns that are not directly required by the next content slice

## Active packet - Mission 3 env-prep hardening and adapter seam

Packet goal:

- make one bounded preparatory pass before Mission 3 env/wrapper extension
- close the reproduced mission loader/schema hardening gaps that now have clear
  repo evidence
- add one narrow shared resolver-backed env-adapter seam so the next env packet
  grows through a small shared core rather than another isolated wrapper stack
- preserve the accepted Mission 1 and Mission 3 reference surfaces unchanged

Planning audit findings:

- Repository state was rechecked on March 14, 2026 before opening this packet:
  - `git status --short` showed local tracked edits in
    `docs/internal/execution_plan.md` plus untracked
    `docs/internal/mission3_cross_mission_probes.md`
  - `git log --oneline --decorate -12` showed `HEAD` on
    `d3188cc docs: capture post-search planning pause`
  - `.venv/bin/pytest -q` passed with `236 passed in 220.40s`
  - `.venv/bin/ruff check src tests` passed with `All checks passed!`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
    preserved `random 2/16`, `heuristic 11/16`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`
    preserved `32` action ids, `35` decision steps, defeat, reward `-1.0`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase5_summary --artifact-dir outputs/phase5/train_seed_101_ep_2000 --artifact-dir outputs/phase5/train_seed_202_ep_2000 --artifact-dir outputs/phase5/train_seed_303_ep_2000`
    preserved best `144` and median `133`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase6_stronger_baseline --mode benchmark`
    preserved `random 11/200`, `heuristic 157/200`, `rollout 195/200`
  - `.venv/bin/python -m solo_wargame_ai.cli.mission3_comparison --mode benchmark`
    preserved the historical Mission 3 benchmark surface
    `random 0/200`, `heuristic 72/200`, `rollout-search 105/200`
- The active hardening risks are the reproduced loader/schema findings `C8`,
  `C9`, and `C10`.
- `C7` unsafe checkpoint loading remains real, but current repo evidence does
  not tie it directly to the env-prep packet:
  it lives on the Phase 5 checkpoint/artifact path rather than on the mission
  loader or shared env-extension seam.
- Current env growth risk is architectural, not performance-related:
  `normalize_env_state(...)` already shows a shared resolver-backed decision
  boundary, but reset/step/session lifecycle still lives inside `Mission1Env`,
  so Mission 3 env work would otherwise either harden `Mission1Env` into the
  wrong center or create a second local wrapper island.
- Current Mission 1 wrapper behavior is accepted and must remain stable through
  this packet:
  the fixed 32-id action surface, legal-id/mask behavior, terminal-only reward,
  and accepted Phase 4 smoke output are preserved reference history.

Small-prep decision:

- yes, open one prep packet before Mission 3 env/wrapper extension

Why this packet must stay small:

- the next question is not whether Mission 3 needs an env; it is whether the
  repo can remove a few known hardening traps and expose one clean extension
  seam before that env lands
- the reproduced issues are localized to the mission loader/schema boundary and
  the env session seam
- widening into Mission 3 wrapper implementation, learning, Mission 4, or a
  generic env/search/reporting platform would mix separate decision gates and
  make acceptance less honest

Accepted scope:

- stricter mission schema parsing for unknown keys and missing required fields
- stricter semantic mission validation for the numeric domains already covered
  by the supported mission slice
- explicit loader/runtime synchronization for unsupported multi-start missions
- one narrow shared resolver-backed env-adapter core below mission-local
  wrappers
- only the smallest `env/` or `eval/` export cleanup directly required to
  expose that seam honestly
- tracked internal docs and packet status/closeout guidance for this packet

Out of scope:

- Mission 3 env/wrapper implementation itself
- Mission 3 learning experiments
- Mission 4 content or genuine multi-start mission support
- broader checkpoint/training security hardening unless a direct env-prep
  linkage is proven
- generic multi-mission env platform, generic action-catalog platform, or
  generic comparison/reporting platform
- broad repo reorganization, replay redesign, `legal_actions.py`
  decomposition, objective-dispatch generalization, or a synthetic-fixture
  program
- reopening accepted Mission 3 search strengthening or replacing accepted
  benchmark history with exploratory notes

Active hardening items now:

- `C8`
  - active and in scope
  - tighten numeric validation for values already covered by the supported
    mission slice, such as `turn_limit`, British `base_to_hit`, German
    `attack_to_hit`, reveal-table roll bounds, and current combat-modifier
    fields
- `C9`
  - active and in scope
  - hard-sync the loader/runtime boundary for multi-start support now rather
    than leaving "loads but cannot initialize" as an implicit contract
- `C10`
  - active and in scope
  - reject unknown schema keys and replace raw missing-key failures with
    structured schema errors
- `C7`
  - not active by default
  - keep recorded in the audit follow-ups, but do not pull checkpoint/training
    hardening into this packet unless a direct env-prep dependency is found

Key planning decisions:

### Validation/schema boundary decision

- Split the loader boundary into two explicit layers:
  - schema parsing should reject unknown keys and report missing required
    fields as structured mission-schema failures
  - semantic validation should enforce cross-field and numeric-domain rules on
    the typed mission model
- Do not build a generic schema framework or generic config platform for this
  packet.
- Keep the change bounded to the currently accepted mission/config surface.
- Missing keys and unknown keys should no longer surface as silent acceptance
  or raw `KeyError` leaks.

### Multi-start handling decision

- Hard-sync loader and runtime now.
- The correct sync direction for this packet is:
  reject unsupported multi-start missions at the loader/validation boundary.
- Do not widen runtime initialization to true multi-start support here.
- Keep the single-start limit explicit as a current scope guard, not as a
  forever engine truth.

### Shared env-adapter seam decision

- Add one shared resolver-backed env core below mission-local wrappers.
- That shared core should own:
  - deterministic reset from `Mission` + seed
  - automatic progression to the env decision boundary
  - current legal staged domain actions
  - step-count / episode-open / optional max-step bookkeeping
  - domain-action application through the resolver path
- That shared core should not own:
  - mission-local action-id catalogs
  - mission-local observation schemas
  - mission-local reward policy
  - a generic multi-mission env registry or env-factory platform
- `Mission1Env` should become a thin Mission-1-specific wrapper over that seam.
- The later Mission 3 env packet should compose the same seam with its own
  Mission-3-local observation/action adapter rather than cloning wrapper
  lifecycle logic.

### Minimal export cleanup decision

- Allow minimal `env/` export cleanup only if it is directly needed to make the
  shared seam visible and to stop Mission-1-local helpers from reading like the
  package-wide future API.
- Allow `eval/` cleanup only if a tiny import or naming update is directly
  required by that seam extraction.
- Do not open a broader `env/` or `eval/` cleanup campaign inside this packet.

### Preserved-surface policy

- Preserve the accepted Mission 1 anchors:
  - `random 11/200`
  - learned best `144/200`
  - `heuristic 157/200`
  - `rollout 195/200`
- Preserve the accepted Mission 3 historical surface:
  - smoke:
    `random 0/16`, `heuristic 7/16`, `rollout-search 8/16`
  - benchmark:
    `random 0/200`, `heuristic 72/200`, `rollout-search 105/200`
- Preserve the accepted strengthened Mission 3 local search result:
  - smoke:
    `rollout-search-strengthened 12/16`
  - benchmark:
    `rollout-search-strengthened 171/200`
- Preserve the accepted operator references:
  - `cli/phase3_baselines.py`
  - `cli/phase4_env_smoke.py`
  - `cli/phase5_summary.py`
  - `cli/phase6_stronger_baseline.py`
  - `cli/mission3_comparison.py`

### Durable API vs implementation-detail decision

- Durable for the current planning cycle:
  - `io.load_mission(...)` / `load_mission_from_data(...)`
  - the typed static `Mission` model after the stricter loader/validation pass
  - `create_initial_game_state(...)` as the runtime-entry seam, while keeping
    the single-start restriction documented as current scope
  - `resolver.get_legal_actions(...)`, `resolver.apply_action(...)`, and
    `resolver.resolve_automatic_progression(...)`
  - `eval/episode_runner.py` and `eval/metrics.py` as the lower-level
    domain-action comparison seam
  - the accepted Mission 1 wrapper behavior for existing callers
- Treat as current implementation detail rather than permanent cross-mission
  contract:
  - the fixed 32-id Mission 1 action catalog as the center of future env
    growth
  - `MISSION_1_ID`, `MissionActionCatalog`, and
    `build_mission1_action_catalog(...)` as package-wide env exports
  - the current `build_observation(...)` Mission 1 payload shape as a future
    cross-mission default
  - broad `env.__init__` re-exports that imply the whole current Mission 1
    helper set is the future shared API
  - any Phase-5-specific learned-eval import surface that happens to point at
    `Mission1Env`

Boundary to later packets:

- This env-prep packet includes:
  - loader/schema/validation hardening
  - single-start contract synchronization
  - one shared env session seam
  - the smallest preservation/export cleanup that seam directly needs
- Mission 3 env/wrapper extension starts only when:
  - a Mission 3 observation boundary is being added
  - a Mission 3 action adapter/catalog/mask surface is being added
  - Mission 3 wrapper semantics are being defined
- Mission 3 learning starts only when:
  - a Mission 3 wrapper already exists and is accepted
- Search/heuristic productization starts only when:
  - a later packet explicitly reopens those exploratory reports as a new
    question
- Mission 4 starts only when:
  - new content beyond Mission 3 is being transcribed or supported
- Generic platform work starts only when:
  - more than one active mission genuinely requires shared abstraction beyond
    the narrow seams above

## Mission 3 env-prep packet status block

- Delivery A: completed (`fe14676`)
- Delivery B: completed (`5e80978`)
- Delivery C: not opened
- Packet overall: closed
- Planning audit date: March 14, 2026
- Closeout audit date: March 14, 2026
- Blocking findings before dispatch:
  - `C8`
  - `C9`
  - `C10`
- Closeout audit findings:
  - none acceptance-blocking
- Not-active-by-default finding:
  - `C7`
- Executed package order:
  - Delivery A
  - Delivery B
- Required preserved Mission 1 anchors:
  - `random 11/200`
  - learned best `144/200`
  - `heuristic 157/200`
  - `rollout 195/200`
- Required preserved Mission 3 historical surface:
  - smoke:
    `random 0/16`, `heuristic 7/16`, `rollout-search 8/16`
  - benchmark:
    `random 0/200`, `heuristic 72/200`, `rollout-search 105/200`
- Required preserved Mission 3 strengthened local result:
  - smoke:
    `rollout-search-strengthened 12/16`
  - benchmark:
    `rollout-search-strengthened 171/200`
- Recommended delivery order:
  - Delivery A
  - Delivery B
  - Delivery C only if Deliveries A/B do not already leave a clean closeout
    surface
- End-of-packet default gate:
  - proceed to Mission 3 env/wrapper extension
  - do not open another preparatory packet by default unless this packet
    exposes a new concrete blocker that was not already visible here

## Delivery A - Mission loader/schema hardening and multi-start sync

Status:

- completed (`fe14676 mission: harden schema parsing and validation`)

Goal:

- tighten the mission loader/validation boundary so current supported missions
  fail early, strictly, and readably instead of loading permissively and
  breaking later

Concrete deliverables:

- structured schema-level rejection of unknown keys
- structured schema-level errors for missing required fields
- explicit numeric-domain validation for current supported mission data
- explicit early rejection of unsupported multi-start missions so loader and
  runtime no longer disagree
- focused tests covering the reproduced `C8`, `C9`, and `C10` cases

Likely files / subsystems touched:

- `src/solo_wargame_ai/io/mission_schema.py`
- `src/solo_wargame_ai/io/mission_loader.py`
- `src/solo_wargame_ai/domain/validation.py`
- `src/solo_wargame_ai/domain/state.py` only if one error message or guard
  wording must be aligned with the loader contract
- focused mission loader/validation tests under `tests/`

Required tests / verification:

- focused tests for:
  - unknown-key rejection
  - missing-key structured errors
  - numeric-domain validation failures
  - unsupported multi-start rejection at load/validation time
- `.venv/bin/pytest -q`
- `.venv/bin/ruff check src tests`
- `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
- `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`
- `.venv/bin/python -m solo_wargame_ai.cli.phase5_summary --artifact-dir outputs/phase5/train_seed_101_ep_2000 --artifact-dir outputs/phase5/train_seed_202_ep_2000 --artifact-dir outputs/phase5/train_seed_303_ep_2000`
- `.venv/bin/python -m solo_wargame_ai.cli.phase6_stronger_baseline --mode benchmark`
- `.venv/bin/python -m solo_wargame_ai.cli.mission3_comparison --mode benchmark`

Risks / traps:

- turning the parser hardening into a generic schema-system project
- widening runtime initialization to real multi-start support instead of
  rejecting unsupported scope early
- mixing objective/general content work into numeric validation changes
- changing accepted mission behavior while trying to improve error UX

Completion criteria:

- unknown keys no longer pass silently
- missing required fields no longer surface as raw `KeyError`
- obviously invalid numeric values are rejected at the loader/validation
  boundary
- multi-start missions no longer load successfully and then fail later at
  runtime initialization

Commit shape:

- one implementation commit preferred
- two commits acceptable only if parser/schema errors and semantic-validation
  sync are materially clearer to review separately

Analysis-before-edit:

- required

## Delivery B - Shared resolver-backed env-adapter seam

Status:

- completed (`5e80978 mission: extract shared resolver env session seam`)

Goal:

- extract one narrow shared env session seam that Mission 1 can delegate to now
  and Mission 3 can reuse later, without committing to a broad env platform

Concrete deliverables:

- one shared env core around reset / normalized state / legal domain actions /
  step / episode bookkeeping
- `Mission1Env` migrated to that core without changing accepted external
  Mission 1 behavior
- only the minimal `env/` or `eval/` import/export cleanup required to keep
  the new seam honest
- focused regression tests proving preserved Mission 1 wrapper behavior

Likely files / subsystems touched:

- `src/solo_wargame_ai/env/`
- `src/solo_wargame_ai/env/mission1_env.py`
- `src/solo_wargame_ai/env/normalized_state.py` or a directly adjacent shared
  replacement seam
- `src/solo_wargame_ai/env/__init__.py`
- `src/solo_wargame_ai/eval/learned_policy_eval.py` only if a tiny import
  cleanup is directly required
- focused env/eval regression tests under `tests/`

Required tests / verification:

- focused tests for:
  - deterministic seeded Mission 1 reset/step preservation
  - legal-id/mask preservation
  - truncation and terminal semantics preservation
  - learned-policy evaluation compatibility if the seam changes a direct import
- `.venv/bin/pytest -q`
- `.venv/bin/ruff check src tests`
- `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
- `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`
- `.venv/bin/python -m solo_wargame_ai.cli.phase5_summary --artifact-dir outputs/phase5/train_seed_101_ep_2000 --artifact-dir outputs/phase5/train_seed_202_ep_2000 --artifact-dir outputs/phase5/train_seed_303_ep_2000`

Risks / traps:

- turning the shared seam into a generic multi-mission env platform
- forcing a new cross-mission observation or action-id abstraction too early
- changing accepted Mission 1 wrapper semantics while extracting the seam
- widening `eval/` into a cross-mission env-evaluation platform

Completion criteria:

- one shared resolver-backed env session seam exists below mission-local
  wrappers
- `Mission1Env` behavior remains compatible with the accepted Phase 4/5
  surfaces
- the next Mission 3 env packet can build on the seam without cloning wrapper
  lifecycle logic

Commit shape:

- one implementation commit preferred
- one narrow follow-up `fix:` commit acceptable only if review finds a clear
  preservation issue

Analysis-before-edit:

- required

## Delivery C - Optional export/preservation cleanup finish

Status:

- not opened

Goal:

- only if Deliveries A and B do not already leave a clean closeout-ready
  surface, add the smallest follow-up needed to clarify shared-vs-local env
  boundaries without widening scope

Concrete deliverables:

- at most one narrow follow-up for:
  - minimal `env/__init__` or `eval/__init__` export cleanup
  - one small wording or helper rename that makes the shared seam easier to
    read
  - one preservation fix if A/B made Mission-1-local helpers look like the new
    default cross-mission contract
- no Mission 3 wrapper work
- no learning/search/content scope

Likely files / subsystems touched:

- `src/solo_wargame_ai/env/__init__.py`
- `src/solo_wargame_ai/eval/__init__.py` only if directly required
- small directly related tests

Required tests / verification:

- focused tests for any new export/helper surface
- `.venv/bin/pytest -q`
- `.venv/bin/ruff check src tests`
- `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`

Risks / traps:

- turning a cleanup finish into a broad naming/export campaign
- reopening Delivery A/B design questions instead of fixing one narrow blocker
- smuggling generic platform work into a preservation pass

Completion criteria:

- the Packet Master Thread can close the packet without another preparatory
  implementation thread
- the shared seam and Mission-local implementation details are clearly
  separated in code and docs

Commit shape:

- one small implementation or docs-and-implementation follow-up commit only if
  the package is opened

Analysis-before-edit:

- required

## Recommended Delivery Thread sequence for the Mission 3 env-prep packet

Preferred sequence:

1. Delivery A
2. Delivery B
3. Delivery C only if Deliveries A/B do not already leave a clean closeout
   surface

Do not mix in one thread:

- loader/schema hardening with shared env seam extraction
- any env-prep package with Mission 3 env/wrapper implementation
- any env-prep package with Mission 3 learning experiments
- any env-prep package with Mission 4 content landing
- bounded env seam extraction with a generic env platform or cross-mission
  reporting buildout
- reproduced hardening fixes with checkpoint/training security work unless a
  direct dependency is found

End-of-packet decision gate:

- Proceed directly to Mission 3 env/wrapper extension if:
  - loader/schema failures are strict and readable
  - unsupported multi-start missions are rejected before runtime
  - the shared env session seam exists and `Mission1Env` delegates to it
    without accepted-surface drift
  - no new blocker appears that clearly belongs in a separate prep packet
- Do not open another preparatory packet by default unless:
  - Deliveries A/B expose a new concrete blocker that was not already visible
    from the current repo evidence
  - or acceptance fails because the shared seam cannot be landed without a
    narrowly justified extra finish package

Closeout audit findings:

- `C8`, `C9`, and `C10` are now addressed in accepted repo history through
  `fe14676`
- the shared resolver-backed env session seam is now present in accepted repo
  history through `5e80978`
- `Mission1Env` remains compatible with the accepted Phase 4/5 Mission 1 env
  surface
- Delivery C was not opened because Deliveries A/B already left a clean
  closeout-ready packet surface
- no Mission 3 wrapper implementation, Mission 3 learning, Mission 4 content,
  generic env platform work, or broad cleanup work was opened in this packet

Archived closeout recommendation:

- close this packet
- proceed to Mission 3 env/wrapper extension by default
- do not open another preparatory packet by default unless a later thread
  finds a new concrete blocker that was not visible during this packet
- preserve the accepted Mission 1 anchors, Mission 3 historical comparison
  surface, and strengthened Mission 3 local result as reference history while
  the next packet extends the env boundary

Archived packet history continues below.

## Archived packet - Mission 3 search strengthening

Packet goal:

- make one bounded non-learning strengthening pass on Mission 3 search
- try to beat the accepted historical `rollout-search 105/200` benchmark
  result
- keep any heuristic work subordinate to the search continuation goal
- end with a clear gate to Mission 3 env/wrapper extension rather than another
  tuning loop

Planning audit basis:

- the accepted Mission 3 historical comparison surface was already stable:
  - smoke: `random 0/16`, `heuristic 7/16`, `rollout-search 8/16`
  - benchmark: `random 0/200`, `heuristic 72/200`,
    `rollout-search 105/200`
- the bounded local headroom was justified by one concrete search-side seam:
  the accepted historical search baseline used
  `mission3_heuristic(depth=0)` continuation even though the accepted Mission 3
  heuristic row already used the stronger default depth surface
- the packet was treated from the start as the default last bounded
  non-learning Mission 3 pass before env/wrapper extension

Accepted implementation result:

- Delivery A landed the accepted implementation commit:
  - `c84b1f0 mission3: strengthen search surface and preserve historical baseline`
- the historical Mission 3 surface remains separate, visible, and rerunnable
- the accepted strengthened local Mission 3 result is:
  - smoke: `rollout-search-strengthened 12/16`
  - benchmark: `rollout-search-strengthened 171/200`
- accepted strengthened search budget:
  - `full_legal_width`
  - `1` rollout per action
  - `mission3_heuristic(depth=2)`
  - rollout depth limit `24` player decisions
  - terminal fallback to frontier-state scoring
- the packet success target was materially exceeded:
  - `171/200` vs target `120/200`
  - `+66` wins vs historical Mission 3 `rollout-search 105/200`
- Delivery B was not opened because Delivery A already produced a clean,
  decisive result
- Delivery C was not opened because Delivery A already left a clear
  historical-vs-strengthened report surface

Closeout audit findings:

- none acceptance-blocking
- preserved Mission 1 anchors remained unchanged
- preserved Mission 3 historical references remained unchanged
- no env/wrapper, learning, Mission 4, or generic search/reporting/platform
  work was opened inside this packet
- do not treat any later exploratory cross-mission evidence as a replacement
  for the accepted historical or strengthened Mission-3-local surfaces unless a
  future packet explicitly reopens that question

## Mission 3 search strengthening packet status block

- Delivery A: completed (`c84b1f0`)
- Delivery B: not opened
- Delivery C: not opened
- Packet overall: closed
- Planning audit date: March 12, 2026
- Closeout audit date: March 12, 2026
- Blocking findings before dispatch: none
- Closeout audit findings: none acceptance-blocking
- Executed package order: Delivery A
- Required preserved Mission 1 anchors:
  - `random 11/200`
  - learned best `144/200`
  - `heuristic 157/200`
  - `rollout 195/200`
- Preserved Mission 3 historical baseline:
  - smoke:
    `random 0/16`, `heuristic 7/16`, `rollout-search 8/16`
  - benchmark:
    `random 0/200`, `heuristic 72/200`, `rollout-search 105/200`
  - historical accepted search budget:
    full legal root width, `1` rollout per action,
    `mission3_heuristic(depth=0)`, rollout depth limit `16` player decisions,
    terminal fallback to frontier-state scoring
- Accepted strengthened Mission 3 result:
  - smoke:
    `rollout-search-strengthened 12/16`
  - benchmark:
    `rollout-search-strengthened 171/200`
  - accepted strengthened budget:
    full legal root width, `1` rollout per action,
    `mission3_heuristic(depth=2)`, rollout depth limit `24` player decisions,
    terminal fallback to frontier-state scoring
- Closeout gate:
  - proceed to Mission 3 env/wrapper extension by default
  - do not open another Mission 3 search packet by default unless a future
    thread opens a clearly different explicit question

## Delivery A - Mission 3 search continuation strengthening

Status:

- completed (`c84b1f0 mission3: strengthen search surface and preserve historical baseline`)

Goal:

- implement the main Mission 3 search-side strengthening lever and rerun the
  Mission 3 comparison surface without overwriting historical truth

Execution outcome:

- strengthened the continuation policy from historical
  `mission3_heuristic(depth=0)` to accepted local strengthened
  `mission3_heuristic(depth=2)`
- accepted one bounded rollout horizon increase from `16` to `24`
- preserved the historical Mission 3 surface as a separate rerunnable operator
  path
- added strengthened-only and packet report surfaces to show historical versus
  strengthened results honestly
- returned a decisive bounded result, so no subordinate heuristic pass was
  needed

Required verification at acceptance:

- `.venv/bin/ruff check src tests`
- `.venv/bin/pytest -q`
- `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
- `.venv/bin/python -m solo_wargame_ai.cli.phase6_stronger_baseline --mode benchmark`
- `.venv/bin/python -m solo_wargame_ai.cli.mission3_comparison --mode smoke --surface historical`
- `.venv/bin/python -m solo_wargame_ai.cli.mission3_comparison --mode benchmark --surface historical`
- `.venv/bin/python -m solo_wargame_ai.cli.mission3_comparison --mode smoke --surface strengthened`
- `.venv/bin/python -m solo_wargame_ai.cli.mission3_comparison --mode benchmark --surface strengthened`
- `.venv/bin/python -m solo_wargame_ai.cli.mission3_comparison --mode smoke --surface packet`

Completion criteria:

- met
- the packet now has a materially stronger Mission-3-local search reference
  while historical truth remains visible

## Delivery B - Conditional narrow heuristic continuation pass

Status:

- not opened

Reason:

- Delivery A already returned a decisive strengthened search result without
  needing a subordinate heuristic-quality pass

## Delivery C - Optional report/preservation finish

Status:

- not opened

Reason:

- Delivery A already produced a clean closeout-ready historical-vs-strengthened
  report surface

## Archived closeout recommendation

- close this packet
- move to Mission 3 env/wrapper extension by default
- preserve the accepted historical Mission 3 reference surface and the accepted
  strengthened local Mission 3 result as separate truths

## Archived packet - Mission 3 baselines/search re-establishment

Packet goal:

- re-establish a first accepted Mission 3 comparison stack before opening
  Mission 3 env/wrapper work, Mission 3 learning, Mission 4 content, or a
  generic multi-mission benchmark platform

Planning audit findings:

- Mission 3 is already a deterministic resolver-playable and replayable slice;
  this packet is not a reason to reopen the content-landing work.
- The reusable lower-level comparison seam already exists:
  - `agents/base.py`
  - `create_initial_game_state(...)`
  - `resolver.get_legal_actions(...)`
  - `resolver.apply_action(...)`
  - `eval/episode_runner.py`
  - `eval/metrics.py`
- `RandomAgent` is reusable as-is for Mission 3.
- The current higher-level comparison/operator surface is still Mission-1-
  specific:
  - `HeuristicAgent` is explicitly Mission-1-specific and fabricates synthetic
    order-choice states for scoring.
  - `RolloutSearchAgent` inherits Mission 1 coupling through its heuristic
    rollout policy.
  - `eval/benchmark.py` and `eval/rollout_baseline.py` hardcode Mission 1
    agent sets, seed surfaces, and/or preserved anchor handling.
  - `cli/phase3_baselines.py` and `cli/phase6_stronger_baseline.py` hardcode
    Mission 1 paths and are preserved historical operator surfaces.
- Mission 3 shares the accepted clear-all-hostiles objective family and the
  current single-start-hex setup assumption with Mission 1, so this packet does
  not need objective-dispatch generalization or multi-start-hex work.
- `C6` remains an active caution:
  Mission-1-specific heuristic coupling is acceptable as a local baseline
  implementation detail, but it must not silently become the future general
  agent contract.
- A generic multi-mission benchmark/reporting platform is still unjustified:
  one bounded Mission-3-local comparison surface is enough for this packet.

Packet planning decisions:

- Minimal accepted Mission 3 comparison stack:
  - `random` floor baseline
  - one bounded Mission 3 heuristic baseline
  - one bounded Mission 3 rollout/search baseline with an explicit fixed budget
- What can be deferred:
  - generic search frameworks or pluggable planner backends
  - additional heuristic families beyond one bounded Mission 3 baseline
  - Mission 3 env/wrapper extension
  - Mission 3 learning experiments
  - Mission 4 content landing
  - cross-mission reporting/platform work
  - reward/env/action redesign absent a direct blocker found during this packet
- Reuse as-is:
  - `agents/base.py`
  - `RandomAgent`
  - `create_initial_game_state(...)`
  - `resolver.get_legal_actions(...)`
  - `resolver.apply_action(...)`
  - `eval/episode_runner.py` and `eval/metrics.py`, with only bounded wording
    or helper cleanup if directly required by Mission 3 comparison work
- Requires bounded adaptation:
  - the Mission 3 comparison/eval/CLI surface, because preserved Mission 1
    phase/operator files should stay as historical references rather than be
    widened into a mixed-mission interface
  - the heuristic baseline, because the accepted `HeuristicAgent` is
    intentionally Mission-1-specific
  - the rollout/search baseline, because its current leaf policy is coupled to
    the Mission 1 heuristic
- Cleanup/refactor decision:
  - no pre-packet cleanup/refactor campaign
  - keep changes maximally narrow and adaptational
  - allow only small helper extraction or wording cleanup inside
    `agents/`, `eval/`, or `cli/` when it directly separates preserved Mission
    1 references from the new Mission 3 surface
- Mission 1 anchors that remain preserved reference history during this packet:
  - `RandomAgent` `11/200`
  - learned policy best `144/200`
  - `HeuristicAgent` `157/200`
  - `RolloutSearchAgent` `195/200`

## Mission 3 comparison protocol

Smoke protocol:

- one thin Mission 3 comparison CLI on fixed seeds `0..15`
- include `random`, Mission 3 heuristic, and Mission 3 rollout/search in one
  Mission-3-only metrics table
- preserve the existing Mission 1 smoke commands unchanged and separate

Benchmark protocol:

- rerun the same Mission 3 trio on fixed seeds `0..199`
- keep the Mission 3 report separate from Mission 1 anchor reports
- do not merge Mission 1 and Mission 3 benchmark tables into one generic
  cross-mission result surface in this packet

Seed policy:

- Mission 3 should use its own named smoke and benchmark seed aliases even if
  the numeric ranges match the preserved Mission 1 ranges
- the fixed cardinalities should remain `16` smoke seeds and `200` benchmark
  seeds for the first accepted Mission 3 reference surface
- numeric seed overlap does not imply cross-mission comparability; report
  Mission 3 outcomes only in Mission-3-local surfaces

Required comparison metrics:

- keep the accepted aggregate metric row unchanged:
  - `wins`
  - `defeats`
  - `win_rate`
  - `defeat_rate`
  - `mean_terminal_turn`
  - `mean_resolved_markers`
  - `mean_removed_german`
  - `mean_player_decisions`
- report search budget separately from outcome metrics:
  - root width
  - rollout policy
  - rollout depth / terminal policy

First accepted Mission 3 reference surface:

- one deterministic smoke result for the Mission 3 `random` / `heuristic` /
  `rollout-search` trio
- one deterministic 200-seed benchmark result for the same trio
- one explicit Mission-3-only report/delta surface recorded in internal docs
  without rewriting the preserved Mission 1 anchor sections
- if search fails to beat heuristic, treat that as a decision input for the
  next packet, not as an automatic packet failure, as long as the comparison
  surface is deterministic, reviewable, and clearly separated from Mission 1

Active follow-ups from `docs/internal/independent_audit_followups.md`:

- `P4-R4` active as a preservation rule:
  - keep the accepted Mission 1 smoke/benchmark/env references explicit and
    unchanged while Mission 3 comparison work lands
- `C6` active as a caution:
  - Mission-1-specific heuristic coupling may be reused locally, but must not
    become an implicit general agent contract

Not active by default in this packet unless a direct blocker appears:

- `C1` replay draw-prediction coupling
- `C2` `legal_actions.py` growth / separation
- `C3` multiple-start-hex support
- `C4` objective-dispatch generalization
- `C5` synthetic fixtures
- `T1` through `T4` tooling backlog

Boundary to later packets:

- This packet includes:
  - bounded Mission 3 baseline/search comparison work only
  - the smallest Mission-3-local eval/CLI/operator surface that makes smoke and
    benchmark reruns honest
  - any minimal agent/eval/CLI adaptation directly required for the comparison
    stack
- This packet does not include:
  - Mission 3 env/wrapper extension
  - Mission 3 learning experiments
  - Mission 4 content landing
  - generic cross-mission benchmark/reporting infrastructure
  - reward/env/action redesign unless a direct blocker is found
  - a broad cleanup/refactor campaign in `agents/`, `eval/`, or `cli/`

## Mission 3 baselines/search packet status block

- Delivery A: completed
- Delivery B: completed
- Delivery C: not opened
- Packet overall: closed
- Planning audit date: March 11, 2026
- Closeout audit date: March 12, 2026
- Blocking findings before dispatch: none
- Closeout audit findings:
  - none acceptance-blocking
  - stronger search quality remains available, but should be treated as a new
    packet rather than a tail on this one
- Required preserved Mission 1 anchors:
  - `random 11/200`
  - learned best `144/200`
  - `heuristic 157/200`
  - `rollout 195/200`
- Accepted Mission 3 reference surface:
  - smoke:
    `random 0/16`, `heuristic 7/16`, `rollout-search 8/16`
  - benchmark:
    `random 0/200`, `heuristic 72/200`, `rollout-search 105/200`
- Executed package order: Delivery A -> Delivery B
- Landed implementation commits:
  - `0e4a8ac mission3: add local comparison surface`
  - `addae5a mission3: add bounded heuristic and search baselines`
- Closeout gate:
  - this packet is closed
  - do not reopen it for stronger heuristic/search behavior unless a
    corrective bug is found
  - treat any search-quality improvement as a new packet

## Delivery A - Mission 3 comparison surface + random floor

Status:

- completed

Goal:

- open the smallest Mission-3-local comparison surface that keeps preserved
  Mission 1 benchmark/operator history untouched while establishing the Mission
  3 random baseline floor

Concrete deliverables:

- one Mission-3-local benchmark/eval/CLI seam rather than widening preserved
  `phase3_*` / `phase6_*` Mission 1 operator files in place
- fixed Mission 3 smoke and benchmark seed aliases plus report formatting
- Mission 3 random baseline smoke/benchmark execution over the accepted domain
  action contract
- only the minimal shared helper or wording cleanup required to reuse the
  lower-level episode/metrics surface honestly

Likely files / subsystems touched:

- `src/solo_wargame_ai/eval/episode_runner.py` only if small wording/helper
  cleanup is directly justified
- `src/solo_wargame_ai/eval/metrics.py` only if a tiny neutral rename/exposure
  change is directly justified
- new or narrowed Mission 3 comparison code under `src/solo_wargame_ai/eval/`
- one thin Mission 3 operator entrypoint under `src/solo_wargame_ai/cli/`
- focused tests under `tests/eval/` and `tests/cli/`

Required tests / verification:

- focused tests for:
  - Mission 3 seed-surface determinism
  - Mission 3 report formatting
  - Mission 3 random baseline execution through the shared runner
- `.venv/bin/pytest -q`
- `.venv/bin/ruff check src tests`
- `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
- `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`
- `.venv/bin/python -m solo_wargame_ai.cli.phase5_summary --artifact-dir outputs/phase5/train_seed_101_ep_2000 --artifact-dir outputs/phase5/train_seed_202_ep_2000 --artifact-dir outputs/phase5/train_seed_303_ep_2000`
- `.venv/bin/python -m solo_wargame_ai.cli.phase6_stronger_baseline --mode smoke`
- the new Mission 3 comparison smoke command

Risks / traps:

- turning Delivery A into a generic multi-mission benchmark platform
- rewriting preserved Mission 1 phase/operator files instead of adding a new
  Mission-3-local surface
- mixing heuristic/search logic into the comparison-surface package
- over-cleaning shared eval helpers before a real Mission 3 blocker exists

Completion criteria:

- a Mission-3-local comparison/operator surface exists and is reviewable
- Mission 3 random smoke/benchmark runs can execute on fixed seed sets
- preserved Mission 1 operator outputs remain unchanged and discoverable
- Delivery B can focus on heuristic/search behavior rather than operator-surface
  invention

Commit shape:

- one implementation commit preferred
- one narrow follow-up `fix:` commit acceptable only if review finds a clear
  separation/preservation issue

Analysis-before-edit:

- required

## Delivery B - Mission 3 heuristic + bounded rollout/search

Status:

- completed

Goal:

- re-establish a useful Mission 3 non-learning comparison stack above the
  random floor using one bounded heuristic and one bounded rollout/search
  baseline

Concrete deliverables:

- one Mission-3-bounded heuristic baseline
- one Mission-3-bounded rollout/search baseline with explicit fixed budget
- Mission 3 smoke and benchmark comparison results for
  `random` / `heuristic` / `rollout-search`
- any minimal eval/report plumbing needed to show the deltas cleanly on the new
  Mission 3 surface

Likely files / subsystems touched:

- `src/solo_wargame_ai/agents/`
- Mission 3 comparison code under `src/solo_wargame_ai/eval/`
- the thin Mission 3 operator entrypoint under `src/solo_wargame_ai/cli/`
- focused tests under `tests/agents/`, `tests/eval/`, and `tests/cli/`

Required tests / verification:

- focused tests for:
  - Mission 3 heuristic action selection in building/hill/wooded-hill and
    multi-marker situations
  - legality preservation for the Mission 3 heuristic and rollout/search
    policies
  - Mission 3 smoke/benchmark determinism on the fixed seed sets
- `.venv/bin/pytest -q`
- `.venv/bin/ruff check src tests`
- `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
- `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`
- `.venv/bin/python -m solo_wargame_ai.cli.phase6_stronger_baseline --mode smoke`
- `.venv/bin/python -m solo_wargame_ai.cli.phase6_stronger_baseline --mode benchmark`
- the new Mission 3 comparison smoke command
- the new Mission 3 comparison benchmark command

Risks / traps:

- turning Mission 3 heuristic adaptation into a hidden general-agent redesign
- letting Mission 1 synthetic-state heuristic tricks become an implicit shared
  contract
- building a generic search framework, MCTS toolkit, or benchmark platform
  instead of one bounded Mission 3 comparator
- mixing in env/wrapper, reward, or learning work because the Mission 3 slice
  is richer
- weakening the preserved Mission 1 anchor surfaces while touching shared code

Completion criteria:

- Mission 3 `random`, `heuristic`, and `rollout-search` all run deterministically
  on the accepted smoke and benchmark seed sets
- the search budget is explicit and stable in the report surface
- the packet returns a clear first Mission 3 reference surface, even if search
  does not beat heuristic
- preserved Mission 1 anchor commands remain unchanged

Commit shape:

- one implementation commit preferred
- two commits acceptable only if the heuristic slice and the search slice are
  materially cleaner to review separately

Analysis-before-edit:

- required

## Delivery C - Optional Mission 3 report/separation finish

Status:

- not opened

Goal:

- only if Deliveries A and B do not already leave a clean closeout-ready
  Mission 3 comparison surface, add the smallest follow-up needed to separate
  preserved Mission 1 history from the new Mission 3 references clearly

Concrete deliverables:

- at most one narrow follow-up for:
  - compact Mission 3 comparison/report formatting
  - one small helper extraction or naming cleanup in `agents/`, `eval/`, or
    `cli/` that A/B clearly made necessary
  - one narrow preservation fix if shared changes blurred Mission 1 and Mission
    3 operator surfaces
- no new baseline families
- no env/wrapper/learning/content scope

Likely files / subsystems touched:

- `src/solo_wargame_ai/eval/`
- `src/solo_wargame_ai/cli/`
- `src/solo_wargame_ai/agents/` only if a tiny helper extraction is directly
  justified
- focused tests under `tests/eval/` and `tests/cli/`

Required tests / verification:

- focused tests for any new report/preservation helper
- `.venv/bin/pytest -q`
- `.venv/bin/ruff check src tests`
- `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
- `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`
- the new Mission 3 comparison smoke command
- the new Mission 3 comparison benchmark command if Delivery C touches that
  surface

Risks / traps:

- reopening Delivery A/B design questions instead of finishing a narrow blocker
- turning a closeout-support package into a broad cleanup pass
- quietly mixing Mission 1 and Mission 3 reports while trying to reduce code
  duplication

Completion criteria:

- the Packet Master Thread can close the packet without another implementation
  package
- Mission 1 preserved anchors and the first Mission 3 reference surface are
  clearly separated in code, operator output, and docs

Commit shape:

- one small implementation/docs follow-up commit only if the package is opened

Analysis-before-edit:

- required

## Recommended Delivery Thread sequence for the Mission 3 baselines/search packet

Preferred sequence:

1. Delivery A
2. Delivery B
3. Delivery C only if Delivery B does not already leave a clean closeout-ready
   Mission 3 comparison surface

Do not mix in one thread:

- Mission 3 comparison-surface work with Mission 3 heuristic/search behavior
  changes
- any Mission 3 baseline/search package with Mission 3 env/wrapper extension
- any Mission 3 baseline/search package with Mission 3 learning experiments
- any Mission 3 baseline/search package with Mission 4 content landing
- bounded Mission 3 eval/CLI adaptation with a generic multi-mission
  benchmark/reporting platform
- bounded heuristic/search adaptation with a broad cleanup/refactor campaign

## Archived Mission 3 baselines/search control record

- Accepted implementation commits:
  - `0e4a8ac mission3: add local comparison surface`
  - `addae5a mission3: add bounded heuristic and search baselines`
- Final accepted verification at closeout:
  - `git status --short` was empty
  - `.venv/bin/pytest -q` passed with `231 passed in 47.35s`
  - `.venv/bin/ruff check src tests` passed with `All checks passed!`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
    preserved `random 2/16`, `heuristic 11/16`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase6_stronger_baseline --mode benchmark`
    preserved `random 11/200`, `heuristic 157/200`, `rollout 195/200`
  - `.venv/bin/python -m solo_wargame_ai.cli.mission3_comparison --mode benchmark`
    confirmed the accepted Mission 3 benchmark reference surface
- Accepted packet result:
  - Delivery A opened a Mission-3-local comparison/eval/CLI surface and
    established the deterministic random floor
  - Delivery B added one bounded Mission 3 heuristic baseline and one bounded
    Mission 3 rollout/search baseline with explicit budget reporting
  - preserved Mission 1 anchors remained separate and unchanged
  - Delivery C was not opened because Delivery B already produced a clean
    closeout-ready comparison surface
- Accepted Mission 3 reference numbers:
  - smoke:
    `random 0/16`, `heuristic 7/16`, `rollout-search 8/16`
  - benchmark:
    `random 0/200`, `heuristic 72/200`, `rollout-search 105/200`
  - current accepted search budget:
    full legal root width, `1` rollout per action,
    `mission3_heuristic(depth=0)`, rollout depth limit `16` player decisions,
    terminal fallback to frontier-state scoring
- Exploratory post-closeout signal for later planning only:
  - local 64-seed diagnostics suggest stronger Mission 3 search is plausible
    inside bounded scope:
    `heuristic_d2 29/64`, `heuristic_d3 30/64`, `rollout_d16_h0 32/64`,
    `rollout_d24_h0 36/64`, `rollout_d16_h2 41/64`,
    `rollout_d24_h2 53/64`
  - these are not accepted benchmark anchors and should not overwrite the first
    accepted Mission 3 reference surface
  - if pursued, open a new packet tentatively named
    `Mission 3 search strengthening`
- Detailed Mission 3 baselines/search planning and acceptance history lives in:
  - `docs/internal/thread_reports/2026-03-11_mission3-baselines-master-thread.md`
  - `docs/internal/thread_reports/2026-03-11_mission3-delivery-a-dispatch.md`
  - `docs/internal/thread_reports/2026-03-11_mission3-delivery-a.md`
  - `docs/internal/thread_reports/2026-03-11_mission3-delivery-b.md`
  - `docs/internal/thread_reports/2026-03-12_mission3-baselines-super-master-handoff.md`

## Archived packet - Mission 3 vertical slice + minimal structural prep

Packet goal:

- prove that the accepted Mission 1 architecture generalizes to one richer
  content slice without opening env/RL work, generic multi-mission
  infrastructure, or a large refactor campaign

Planning audit findings:

- `configs/` still contains only `mission_01_secure_the_woods_1.toml`; no
  richer mission has been transcribed yet.
- The shared domain/io path is partly generic already, but a few seams remain
  materially Mission-1-shaped:
  - `MissionMap` currently stores one terrain tag per hex, while Mission 3
    explicitly includes a wooded hill that should grant both Woods and Hill
    effects.
  - `create_initial_game_state(...)` still requires exactly one start hex.
    This is acceptable for Mission 3 and does not need widening yet.
  - terminal evaluation still implements the clear-all-hostiles victory family
    directly rather than dispatching by objective kind.
  - env/baseline/learning surfaces remain intentionally Mission-1-specific and
    should stay that way in this packet.
- Local rulebook recheck of pages 20-23 confirmed:
  - Mission 3 adds Buildings, Hills, German Rifle Squad, a third British Rifle
    Squad, and a six-turn tracker;
  - Mission 4 adds no new rule or objective family beyond Mission 3;
  - both Mission 3 and Mission 4 keep the same objective text:
    reveal and clear all German units before time runs out.

Packet planning decisions:

- Mission scope:
  - Mission 3 only
- Why not Mission 3 + Mission 4 now:
  - Mission 4 adds no new terrain, unit, or objective family beyond Mission 3
  - bundling Mission 4 would increase transcription and regression surface more
    than it increases architectural evidence
  - Mission 3 already answers the packet's real question: whether the accepted
    engine handles richer terrain/content without reopening platform design
- New content families in scope:
  - terrain: Building defense, Hill attack bonus, and bounded wooded-hill
    semantics where one hex may need to grant both Woods and Hill effects
  - German units: German Rifle Squad
  - British mission data: third Rifle Squad as scenario content only, not as a
    new British unit family
  - objectives: no new objective family; stay on
    `MissionObjectiveKind.CLEAR_ALL_HOSTILES`
- Structural prep required now:
  - widen terrain representation just enough to express wooded-hill hexes
    without building a generic terrain-platform project
  - neutralize Mission-1-only wording/assertions across the shared domain/io
    path that Mission 3 will now reuse
  - allow one narrow clear-all-hostiles helper/guard cleanup in
    `resolver.py` if it improves clarity, but do not build general objective
    dispatch yet
- Mission-1-only guards to widen now:
  - shared domain/io docstrings, error text, and helper names that would become
    misleading once Mission 3 uses the same loader/state/resolver path
  - terrain/combat helpers that currently assume Woods is the only terrain
    modifier family in play
- Mission-1-only guards to keep for now:
  - single-start-hex initial-state guard
  - hidden-marker-id to revealed-German-unit-id coupling
  - `Mission1Env`, Mission 1 action catalog, preserved Phase 3/4/5/6 operator
    CLIs, Mission-1-specific heuristic/rollout baselines, and learned-policy
    surfaces
- Bounded `legal_actions.py` refactor:
  - no dedicated pre-packet refactor package
  - treat `C2` as an in-package watch item only; allow small helper extraction
    inside Delivery A if Mission 3 changes would otherwise make the file less
    reviewable, but do not open a cleanup campaign
- Objective dispatch cleanup:
  - no
  - Mission 3 and Mission 4 still use the same clear-all-hostiles objective
    family, so a full objective-dispatch seam is not required in this packet
- Synthetic fixtures:
  - no by default
  - keep using real mission configs plus focused runtime-state tests unless
    Mission 3 test friction proves that a small fixture helper clearly pays for
    itself

Active follow-ups from `docs/internal/independent_audit_followups.md`:

- `P4-R4` active as a preservation rule:
  - keep the accepted Mission 1 smoke/benchmark/env references explicit and
    unchanged while the new content slice lands
- `C2` active only as a bounded seam review inside Delivery A:
  - no standalone legality/refactor package unless Mission 3 changes prove it
    necessary

Deferred follow-ups for this packet:

- `C1` replay draw-prediction coupling
- `C3` multiple-start-hex support
- `C4` objective-dispatch generalization
- `C5` synthetic fixtures
- `C6` Mission-1-specific heuristic coupling
- `T1` through `T4` tooling backlog

Boundary to later packets:

- This packet includes:
  - Mission 3 config/data transcription
  - the minimal shared domain/io/runtime widening that Mission 3 directly
    forces
  - deterministic Mission 3 load/init/play/replay/test coverage through the
    accepted resolver path
- This packet does not include:
  - Mission 3 baselines/search re-establishment
  - Mission 3 env/wrapper extension
  - Mission 3 learning experiments
  - a generic multi-mission env/eval platform
  - multiple-start-hex work, Minefields, Mortars, PIATs, Half-Tracks,
    Artillery, Rivers/bridges, or replay redesign

## Mission 3 packet status block

- Delivery A: completed
- Delivery B: not opened
- Post-acceptance hardening tail: completed
- Packet overall: closed
- Planning audit date: March 11, 2026
- Closeout audit date: March 11, 2026
- Blocking findings before dispatch: none
- Closeout audit findings: none acceptance-blocking
- Executed package order: Delivery A -> tests-only hardening tail
- Landed commits:
  - `ecda1f4` Implement Mission 3 vertical slice support
  - `c2f9b4c` test: add Mission 3 terminal replay regression
- Closeout gate: packet should not open baselines/env/learning follow-ons until
  deterministic Mission 3 resolver/replay acceptance is in hand

## Delivery A - Mission 3 domain vertical slice + required structural prep

Status:

- completed

Goal:

- land Mission 3 as a deterministic playable mission through the accepted
  resolver path, together with only the structural prep that Mission 3 directly
  forces

Concrete deliverables:

- transcribe `configs/missions/mission_03_secure_the_building.toml`
- extend mission schema/model/validation just enough for Mission 3 static data
- add bounded terrain-representation support for Building, Hill, and wooded-hill
  combinations as required by the Mission 3 map
- land German Rifle Squad support through mission data and German-attack /
  British-attack modifier resolution
- keep the current clear-all-hostiles objective family but make the shared
  terminal-evaluation path honest about that scope
- widen only the shared Mission-1-only domain/io wording and helper seams that
  Mission 3 would otherwise make misleading
- add focused tests and at least one deterministic Mission 3 integration/replay
  proof without opening Mission 3 baselines or env work

Likely files / subsystems touched:

- `configs/missions/`
- `src/solo_wargame_ai/domain/mission.py`
- `src/solo_wargame_ai/domain/terrain.py`
- `src/solo_wargame_ai/domain/state.py`
- `src/solo_wargame_ai/domain/combat.py`
- `src/solo_wargame_ai/domain/german_fire.py`
- `src/solo_wargame_ai/domain/resolver.py`
- `src/solo_wargame_ai/domain/legal_actions.py` only if a small helper
  extraction is justified by the Mission 3 diff
- `src/solo_wargame_ai/io/mission_schema.py`
- `src/solo_wargame_ai/io/mission_loader.py`
- `src/solo_wargame_ai/io/replay.py` only if Mission 3 replay coverage exposes
  a narrow compatibility gap
- focused `tests/domain/`, `tests/integration/`, and replay-related tests
- public docs/assumptions only where Mission 3 rule interpretations or terrain
  representation become stable behavior

Required tests / verification:

- focused tests for:
  - Mission 3 config loading and validation
  - wooded-hill / building / hill combat-threshold behavior
  - German Rifle Squad attack behavior
  - deterministic Mission 3 integration/replay progression
- `.venv/bin/pytest -q`
- `.venv/bin/ruff check src tests`
- `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
- `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`
- `.venv/bin/python -m solo_wargame_ai.cli.phase5_summary --artifact-dir outputs/phase5/train_seed_101_ep_2000 --artifact-dir outputs/phase5/train_seed_202_ep_2000 --artifact-dir outputs/phase5/train_seed_303_ep_2000`
- `.venv/bin/python -m solo_wargame_ai.cli.phase6_stronger_baseline --mode smoke`
- `.venv/bin/python -m solo_wargame_ai.cli.phase6_stronger_baseline --mode benchmark`

Risks / traps:

- turning the required wooded-hill support into a generic terrain-system rewrite
- reopening env/action-catalog work because `env/observation.py` or related
  Mission 1 compatibility code may need a narrow adaptation
- opening a broad `legal_actions.py` cleanup before Mission 3 proves it is
  necessary
- overgeneralizing objective dispatch even though Mission 3 stays on the same
  objective family
- pulling Mission 4 into the package once Mission 3 support is almost done

Completion criteria:

- Mission 3 can be loaded, initialized, played, and replayed deterministically
  through the accepted resolver path
- Mission 1 preserved references and smoke commands still pass unchanged
- any new terrain/mission interpretation needed for wooded-hill or German Rifle
  Squad behavior is documented
- the packet leaves no blocker that would force env/RL work before Mission 3
  baselines/search planning

Commit shape:

- one implementation commit preferred
- one narrow follow-up `fix:` commit acceptable only if a review-requested
  correction lands after the main slice

Execution outcome:

- landed cleanly in `ecda1f4`
- Mission 3 deterministic load/init/play/replay coverage is in place
- required bounded terrain/combat/shared-path widening landed without opening
  env, Mission 4, or generic objective-platform work

Analysis-before-edit:

- required

## Delivery B - Conditional deterministic hardening finish

Status:

- not opened

Goal:

- only if Delivery A does not already leave a clean acceptance surface, add the
  smallest follow-up needed to finish Mission 3 replay/regression hardening or
  one bounded shared-seam cleanup

Concrete deliverables:

- at most one narrow follow-up for:
  - replay compatibility or deterministic trace coverage
  - one small helper extraction in `legal_actions.py` or another shared module
    that Delivery A clearly made too noisy
  - any minimal docs/assumption sync that should not be left implicit
- no new mission content families
- no baseline/search/env/learning work

Likely files / subsystems touched:

- `src/solo_wargame_ai/domain/legal_actions.py`
- `src/solo_wargame_ai/io/replay.py`
- `src/solo_wargame_ai/domain/resolver.py`
- focused tests and any directly related docs

Required tests / verification:

- focused regression tests for the narrowed follow-up
- `.venv/bin/pytest -q`
- `.venv/bin/ruff check src tests`
- `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
- `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`
- rerun any Mission 3-specific deterministic/replay checks added by Delivery A

Risks / traps:

- reopening Delivery A design questions instead of finishing a narrow blocker
- turning a cleanup finish into a second broad refactor package
- mixing packet closeout docs with new implementation scope

Completion criteria:

- the Phase/Packet Master Thread can accept the Mission 3 packet without
  another implementation package
- no unresolved replay/determinism/shared-seam blocker remains for later
  Mission 3 baselines/search planning

Commit shape:

- one small implementation/docs follow-up commit only if the package is opened

Execution outcome:

- not opened
- Delivery A did not leave a concrete replay/shared-seam blocker that justified
  the original Delivery B package
- the only additional hardening that proved worthwhile was a narrower
  post-acceptance tests-only tail, outside the original Delivery B scope

Analysis-before-edit:

- required

## Mission 3 packet closeout

Closeout audit result:

- no acceptance-blocking findings
- Mission 3 packet scope stayed bounded to content-extension plus required
  structural prep
- no Mission 4 content, env/wrapper work, baseline/search reopening, learning
  work, fixture program, or generic multi-mission platform work was opened

Verified on March 11, 2026:

- `.venv/bin/pytest -q` -> `217 passed`
- `.venv/bin/ruff check src tests` -> passed
- `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke` ->
  preserved `random 2/16`, `heuristic 11/16`
- `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0` ->
  preserved `32` action ids, `35` decision steps, defeat
- `.venv/bin/python -m solo_wargame_ai.cli.phase5_summary --artifact-dir outputs/phase5/train_seed_101_ep_2000 --artifact-dir outputs/phase5/train_seed_202_ep_2000 --artifact-dir outputs/phase5/train_seed_303_ep_2000`
  -> preserved best `144`, median `133`
- `.venv/bin/python -m solo_wargame_ai.cli.phase6_stronger_baseline --mode smoke`
  -> preserved `16/16`
- `.venv/bin/python -m solo_wargame_ai.cli.phase6_stronger_baseline --mode benchmark`
  -> preserved `195/200`

Packet outcome:

- Mission 3 now lands as a deterministic resolver-playable and replayable
  content slice
- bounded wooded-hill, building, hill, and German Rifle Squad support is in
  the shared domain/io surface
- the original conditional Delivery B package was not needed
- one extra tests-only hardening tail was accepted after Delivery A because it
  added a terminal end-to-end replay regression without reopening
  implementation scope

Deferred beyond this closed packet:

- Mission 3 baselines/search
- Mission 3 env/wrapper extension
- Mission 3 learning experiments
- Mission 4 content landing
- generic terrain/objective/replay/platform expansion

## Recommended Delivery Thread sequence for the Mission 3 packet

Preferred sequence:

1. Delivery A
2. Delivery B only if Delivery A leaves a concrete replay/shared-seam blocker

Do not mix in one thread:

- Mission 3 content landing with Mission 3 baselines/search
- Mission 3 content landing with Mission 3 env/wrapper extension
- Mission 3 content landing with Mission 3 learning experiments
- required wooded-hill support with a generic terrain-platform redesign
- bounded shared-seam cleanup with objective-platform or multi-start-hex work

## Archived strategic basis for the Phase 6 master-thread

Current planning assumptions used when Phase 6 was active:

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
- The most immediate repo-friction at Phase 6 open came from durable library
  modules that carried phase-history names. Delivery A retired
  those names in favor of responsibility-based paths:
  - `src/solo_wargame_ai/agents/masked_actor_critic_training.py`
  - `src/solo_wargame_ai/eval/learned_policy_seeds.py`
  - `src/solo_wargame_ai/eval/learned_policy_reporting.py`
  - `src/solo_wargame_ai/eval/learned_policy_summary.py`
- Thin operator entrypoints under `src/solo_wargame_ai/cli/phase3_*`,
  `phase4_*`, and `phase5_*` are acceptable as phase-tagged operator surfaces
  and do not need to be renamed in the hygiene pass by default.
- `tests/` started Phase 6 as a single flat directory. That was acceptable
  during early growth, but with more than 40 test files it now materially
  slows navigation and makes phase-history naming linger longer than it
  should.
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

- Package A: complete (`9c73623`)
- Package B: complete (`033ddef`)
- Package C: not opened
- Phase 6 overall: complete
- Planning audit date: March 10, 2026
- Closeout audit date: March 11, 2026
- Blocking findings before closeout: none
- Executed package order: Delivery A -> Delivery B
- Closeout/tag gate: ready for docs closeout commit and later milestone tagging

## Package A - Bounded repo hygiene and naming cleanup

Status:

- complete (`9c73623 phase6: rename learned-policy helpers and regroup tests`)

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

- complete (`033ddef phase6: add stronger rollout baseline for mission 1`)

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

- not opened

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

## Archived Phase 6 control record

- Accepted implementation commits:
  - `9c73623 phase6: rename learned-policy helpers and regroup tests`
  - `033ddef phase6: add stronger rollout baseline for mission 1`
- Final accepted verification:
  - `.venv/bin/pytest -q`
  - `.venv/bin/ruff check src tests`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase5_summary --artifact-dir outputs/phase5/train_seed_101_ep_2000 --artifact-dir outputs/phase5/train_seed_202_ep_2000 --artifact-dir outputs/phase5/train_seed_303_ep_2000`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase6_stronger_baseline --mode smoke`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase6_stronger_baseline --mode benchmark`
- Accepted Phase 6 result:
  - Delivery A retired the most immediate phase-history durable module names and
    partially regrouped `tests/` into clearer subsystem directories without
    behavioral change
  - Delivery B added a bounded root-rollout stronger baseline that reached
    `16/16` wins on smoke and `195/200` wins on the preserved benchmark
  - preserved comparison anchors remained explicit:
    `random 11/200`, `heuristic 157/200`, learned `best 144/200`,
    learned `median 133/200`
  - Package C was not opened because Delivery B already produced a clean
    closeout-ready comparison/report surface
- Detailed Phase 6 planning and acceptance history lives in:
  - `docs/internal/thread_reports/2026-03-10_phase6-master-thread.md`
  - `docs/internal/thread_reports/2026-03-10_phase6-delivery-a-dispatch.md`
  - `docs/internal/thread_reports/2026-03-10_phase6-delivery-a.md`
  - `docs/internal/thread_reports/2026-03-10_phase6-delivery-b-dispatch.md`
  - `docs/internal/thread_reports/2026-03-10_phase6-delivery-b.md`
  - `docs/internal/thread_reports/2026-03-11_phase6-closeout.md`

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

## Historical decision after Phase 6 closeout

Historical closeout recommendation at the moment Phase 6 ended:

- a new bounded Mission 1 strengthening/search planning packet rather than
  immediate Mission 3/4 content extension

This recommendation is preserved here as historical context only.
It was later superseded by the post-Phase-6 strategic review now summarized in
`README.md`, `ROADMAP.md`, and the current planning section near the top of
this file.

Closeout note:

- Package A closed with accepted commit `9c73623`
- Package B closed with accepted commit `033ddef`
- Package C remained closed and was not needed for closeout
- preserved accepted references at closeout are:
  `random 11/200`, `heuristic 157/200`, learned `best 144/200`,
  learned `median 133/200`, stronger rollout `195/200`

## Public docs after Phase 6 closeout

During closeout, public docs were synced to reflect that:

- Phase 6 post-first-RL strengthening is complete
- the repository now includes an accepted Phase 6 stronger-baseline rerun
  command
- the accepted stronger rollout baseline materially exceeds both the preserved
  heuristic anchor and the accepted first learner on Mission 1
- a later strategic review may still revise the next macro-step if the stronger
  baseline meaningfully changes the value of remaining Mission 1 work

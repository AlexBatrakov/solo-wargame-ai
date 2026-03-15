# Execution Plan

## Purpose

This file is the current master control surface for repository-level planning,
dispatch, and closeout.

As of March 15, 2026, the original six-phase roadmap is complete by repository
evidence.
The active planning problem is no longer "how to dispatch the bounded Mission 3
env/wrapper extension cleanly," but "how to move from the now-accepted Mission
3 wrapper contract into Mission 3 learning without blurring fair observation-
based wrapper work, preserved oracle-style Mission 3 history, Mission 4
content, or a generic env platform."

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
- preserve the accepted Mission 3 env-prep packet and its shared-session seam,
- preserve the accepted Mission 3 env/wrapper packet and its observation-based
  wrapper/operator surfaces,
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
  - Mission 3 env-prep hardening and adapter-seam packet complete
  - Mission 3 env/wrapper extension packet complete
- Local tags:
  - `phase1-complete`
  - `phase2-complete`
  - `phase3-complete`
  - `phase4-complete`
  - `phase5-complete`
  - `phase6-complete`
- Repository state rechecked on March 15, 2026 after Mission 3 env/wrapper
  closeout:
  - `git status --short` showed one unrelated local tracked edit:
    `M docs/internal/experiments/README.md`
  - `git log --oneline --decorate -12` showed `HEAD` on
    `faaba99 mission3: add env smoke cli`
  - `git show --no-patch --decorate phase1-complete` still resolved to
    `d6445d9`
  - `git show --no-patch --decorate phase2-complete` still resolved to
    `1ef74ab`
  - `git show --no-patch --decorate phase3-complete` still resolved to
    `98519c7`
  - `git show --no-patch --decorate phase4-complete` still resolved to
    `0e4a6a8`
  - `git show --no-patch --decorate phase5-complete` still resolved to
    `9d8beb9`
  - `git show --no-patch --decorate phase6-complete` still resolved to
    `f80fde5`
  - `.venv/bin/pytest -q` passed with `275 passed in 221.38s`
  - `.venv/bin/ruff check src tests` passed with `All checks passed!`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
    succeeded with the preserved `random` `2/16` wins vs `heuristic`
    `11/16` wins reference
  - `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`
    preserved the accepted Mission 1 wrapper smoke surface:
    `32` action ids, `35` decision steps, defeat, reward `-1.0`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase5_summary --artifact-dir outputs/phase5/train_seed_101_ep_2000 --artifact-dir outputs/phase5/train_seed_202_ep_2000 --artifact-dir outputs/phase5/train_seed_303_ep_2000`
    preserved best `144` and median `133`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase6_stronger_baseline --mode benchmark`
    confirmed `rollout 195/200`, versus preserved anchors `random 11/200`,
    `heuristic 157/200`, and accepted learned references `best 144/200`,
    `median 133/200`
  - `.venv/bin/python -m solo_wargame_ai.cli.mission3_comparison --mode benchmark`
    confirmed the accepted Mission 3 benchmark reference surface:
    `random 0/200`, `heuristic 72/200`, `rollout-search 105/200`
  - `.venv/bin/python -m solo_wargame_ai.cli.mission3_env_smoke --seed 0`
    confirmed the accepted Mission 3 wrapper smoke surface:
    `49` action ids, `72` decision steps, defeat, reward `-1.0`
  - evidence-only local notes remain present under
    `docs/internal/thread_reports/`, but none of them replace the preserved
    accepted benchmark surfaces above

Accepted runtime surface after Mission 3 env/wrapper closeout:

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
- `env/resolver_session.py` is the accepted shared resolver-backed env session
  seam below mission-local wrappers.
- `env/observation.py` remains the accepted Mission-1-local structured
  player-visible observation builder rather than a generic cross-mission
  observation API.
- `env/action_catalog.py` remains the accepted Mission-1-local 32-id staged-
  action catalog surface rather than the center of future env growth.
- `env/legal_action_mask.py` remains the accepted legality-mask helper over the
  Mission 1 catalog; it is not yet a broader multi-mission contract.
- `env/mission1_env.py` is now a thin dependency-free Mission 1 wrapper over
  the shared resolver session seam, with deterministic `reset(seed=...)`,
  `step(action_id)`, terminal-only default reward, and `terminated` /
  `truncated` semantics already frozen.
- `env/mission3_env.py` is now the accepted thin dependency-free Mission 3
  wrapper over the shared resolver session seam, with deterministic
  `reset(seed=...)`, `step(action_id)`, player-visible observation, fixed
  49-id action exposure, opaque contact handles on the public Mission 3
  surface, and terminal-only default reward.
- `env/mission3_observation.py` and `env/mission3_action_catalog.py` are now
  the accepted Mission-3-local observation/action helper surfaces rather than a
  generic cross-mission env API.
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
- `cli/mission3_env_smoke.py` is the accepted thin operator surface for
  rerunning the observation-based Mission 3 wrapper without conflating it with
  historical Mission 3 comparison history.
- `pyproject.toml` now carries the bounded `numpy` / `torch` learning
  dependency pair, while `configs/missions/` now contains the accepted Mission
  1 and Mission 3 configs and no broader experiment-platform surface.
- `outputs/phase5/` contains the accepted first-learner artifacts and aggregate
  summary files used as preserved comparison evidence.

## Current post-Mission-3 planning decision

The original six-phase build sequence is finished, the first richer-content
packet has closed, the first Mission 3 comparison packet has closed, the
bounded Mission 3 search-strengthening packet has closed, and the Mission 3
env-prep packet has also closed.
Future planning should therefore continue from the accepted shared env-session
seam plus the preserved Mission 3 historical and strengthened search surfaces.

The strategic pause after that closeout is now informed by three extra inputs:

- the local exploratory note
  `docs/internal/thread_reports/2026-03-12_mission3_cross_mission_probes.md`,
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

- Mission 3 learning experiments

Why this is now preferred:

- the bounded Mission-3-local strengthening pass already succeeded materially:
  - historical benchmark: `rollout-search 105/200`
  - accepted strengthened benchmark:
    `rollout-search-strengthened 171/200`
- the March 12 hardening findings (`C8`, `C9`, `C10`) were real and are now
  closed in accepted repo history through the env-prep packet
- the current top-level repo split still looks good, so a broad reorg is not
  justified
- the Mission 3 env/wrapper packet is now accepted in repo history, including
  the player-visible observation boundary, opaque contact-handle public
  surface, and thin `mission3_env_smoke` operator
- the next mainline question is now how learnable Mission 3 is under that
  accepted wrapper contract rather than whether the wrapper should exist
- the local exploratory cross-mission probe note remains worth preserving, but
  not strong enough by itself to displace the Mission 3 env mainline
- the local heuristic reports also remain worth preserving, but they should be
  treated as exploratory evidence for a possible later bounded validation or
  productization question, not as accepted benchmark truth and not as a reason
  to reorder the current next packet
- the March 14 fairness reports also remain worth preserving:
  they strengthen the case for an explicit fair-vs-oracle split, but they do
  not displace Mission 3 learning experiments as the current next packet

Likely follow-on packets after that:

1. Mission 3 learning experiments
2. Mission 1 honest/fair-agent lab kickoff after the Mission 3 learning packet
3. Mission 2 same-rules transfer once the Mission 1 fair-agent ladder has a
   usable exact and honest-search surface
4. Mission 3 honest-agent approximation after the repo has both the Mission 3
   wrapper and some fair-agent reference discipline from Missions 1/2
5. Cross-mission evaluation/reporting only when more than one mission is
   active enough to justify it
6. Mission 4 or another bounded richer content slice

Preserved deferred research line beyond the next packet:

- honest/fair-agent research ladder, to be opened only after the Mission 3
  env/wrapper milestone unless project priorities change
- recommended packet sequence inside that ladder:
  1. exact Mission 1 fair-ceiling artifact
  2. honest Mission 1 search baselines
  3. Mission 1 value-function study against exact labels
  4. bounded Mission 1 search-efficiency ideas such as pruning, beam search,
     top-K rollouts, and later MCTS-style work only if the simpler honest
     ladder is already in place
  5. Mission 2 same-rules transfer and exactness check
  6. Mission 3 honest-agent approximation without an exact oracle, likely using
     sampled chance handling, honest rollouts, pruning, and other bounded
     approximations
- Mission 2 deserves special treatment inside this ladder because it uses the
  same rules family as Mission 1, so it can serve as the cleanest bridge
  between an exact small-mission lab and richer-slice honest-agent work
- heavy exact or large seeded runs inside this ladder should prefer a thin
  operator-controlled local command over a long worker-owned terminal session
- if a future exact/benchmark workload is naturally seed-parallel, one bounded
  future packet may add local multi-core execution support so the user can use
  available hardware without changing benchmark meaning

Preserved March 14-15 sandbox idea bank for later packet design:

- benchmark-contract discipline:
  - keep fair player-information agents distinct from oracle/clairvoyant
    references in both naming and interpretation
- honest-search families worth preserving:
  - expected one-step / greedy fair scoring
  - depth-limited expectimax
  - sampled chance evaluation / sampled expectimax
  - rollout-from-top-candidates
  - beam-style bounded search
  - later bounded stochastic tree-search / MCTS-style directions
- specific Mission 3 honest-approximation variants worth preserving:
  - common-random-number rollouts
  - stronger continuation policies before simply increasing rollout count
  - exact German-order solving paired with heuristic British continuation
  - exact chance expansion only at selected stochastic nodes
  - root-only fair action evaluation rather than full exact turn search
- negative-result reminders worth preserving:
  - naive terminal Monte Carlo was too noisy to trust as the main recipe
  - Mission 1 one-turn fair search matched the accepted heuristic rather than
    clearly beating it
  - direct exact fair turn-search did not scale cleanly from Mission 1 to
    Mission 3
  - weak continuation policies made root Monte Carlo look much worse than the
    idea itself might deserve
- state-evaluation / data-modeling ideas worth preserving:
  - exact Mission 1 values as supervised labels
  - manual feature families around tempo, threat, force survival, and
    positional quality
  - regression, boosting, small neural models, and later other bounded
    approximators for `P(win | state)` or aligned value targets
- RL-agent design ideas worth preserving for much later packets:
  - masked legal-action policies
  - hierarchical policies
  - action-scoring networks over legal actions
  - aggregated-feature, fixed-slot, and entity-based state encodings
  - actor-critic / PPO-style baselines
  - imitation learning and search-distilled policies before or alongside later
    RL fine-tuning

Ranked backlog beyond the active next packet:

- High value:
  - Mission 3 learning experiments
  - Mission 1 honest/fair-agent lab kickoff after the Mission 3 learning
    packet
  - Mission 2 same-rules transfer once the Mission 1 fair-agent ladder has a
    usable exact and honest-search surface
- Medium value:
  - Mission 1 exact-ceiling artifact and honest-search baselines
  - Mission 1 value-function study and learned evaluators backed by exact
    labels
  - Mission 2 same-rules transfer and possible exact ceiling check
  - Mission 3 honest-agent approximation after the Mission 3 wrapper/learning
    path is established
  - Mission 4 or another bounded richer content slice once the Mission 3 env
    and learning path are healthier
  - a narrow follow-up on search transfer/localization only if a later thread
    opens that as a new explicit question rather than more generic tuning
  - observation/action redesign only if richer content shows the current
    wrapper is too Mission-1-shaped
  - explicit fair-vs-oracle benchmark framing when the next fair-agent packet
    is opened
  - operator-controlled multi-core local runners for heavy exact or seeded
    experiments once the honest-agent lab starts needing repeated long runs
  - later RL-agent design work around state/action encoding and policy/value
    architecture once the fair-agent ladder has stronger foundations
  - synthetic fixtures and bounded maintainability work when broader content
    makes them pay back
  - cross-mission evaluation/reporting once more than one mission is active
  - splitting `legal_actions.py` or finishing broader test regrouping before
    additional rule families land, but not as the immediate next packet
- Lower priority:
  - another Mission 1 strengthening packet without a specific new research
    question
  - another default Mission 3 search-strengthening packet
  - broad RL-architecture churn before the honest/fair-agent line produces
    clearer evidence
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

## Active packet - Mission 3 learning experiments

Packet goal:

- run one bounded first-pass learning transfer on the accepted `Mission3Env`
  contract
- answer the narrow question:
  does the accepted Phase-5-style learner family transfer at all to Mission 3
  without reward shaping or broad RL redesign?
- produce one first accepted Mission 3 learned result surface while keeping
  preserved historical Mission 3 heuristic/search references visible and
  separately framed

Planning audit findings:

- Repository state was rechecked on March 15, 2026 before opening this packet:
  - `git status --short` showed local tracked docs edits in:
    `ROADMAP.md`
    `docs/internal/execution_plan.md`
    `docs/internal/experiments/README.md`
  - these local diffs were treated as existing worktree context and were not
    silently absorbed into packet scope
  - `git log --oneline --decorate -12` showed `HEAD` on
    `30c3303 docs: close mission3 env wrapper packet`
  - `git show --no-patch --decorate phase1-complete` still resolved to
    `d6445d9`
  - `git show --no-patch --decorate phase2-complete` still resolved to
    `1ef74ab`
  - `git show --no-patch --decorate phase3-complete` still resolved to
    `98519c7`
  - `git show --no-patch --decorate phase4-complete` still resolved to
    `0e4a6a8`
  - `git show --no-patch --decorate phase5-complete` still resolved to
    `9d8beb9`
  - `git show --no-patch --decorate phase6-complete` still resolved to
    `f80fde5`
  - `.venv/bin/pytest -q` passed with `275 passed in 226.57s`
  - `.venv/bin/ruff check src tests` passed with `All checks passed!`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
    preserved `random 2/16`, `heuristic 11/16`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`
    preserved the accepted Mission 1 wrapper smoke surface:
    `32` action ids, `35` decision steps, defeat, reward `-1.0`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase5_summary --artifact-dir outputs/phase5/train_seed_101_ep_2000 --artifact-dir outputs/phase5/train_seed_202_ep_2000 --artifact-dir outputs/phase5/train_seed_303_ep_2000`
    preserved best `144` and median `133`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase6_stronger_baseline --mode benchmark`
    preserved `random 11/200`, `heuristic 157/200`, `rollout 195/200`
  - `.venv/bin/python -m solo_wargame_ai.cli.mission3_comparison --mode benchmark`
    preserved the accepted Mission 3 historical benchmark surface:
    `random 0/200`, `heuristic 72/200`, `rollout-search 105/200`
  - `.venv/bin/python -m solo_wargame_ai.cli.mission3_env_smoke --seed 0`
    preserved the accepted Mission 3 wrapper smoke surface:
    `49` action ids, `72` decision steps, defeat, reward `-1.0`
- The accepted Mission 3 wrapper contract is now real and should not be
  reopened by default:
  - `Mission3Env` exists over `ResolverEnvSession`
  - default observation is player-visible and does not leak raw `GameState`
    or `rng_state`
  - public Mission 3 action exposure uses a fixed `49`-id local catalog with
    opaque contact handles
  - legality remains resolver-owned
  - default reward remains terminal-only
- The active learning-side blockers are now localized and mostly Mission-1-
  specific:
  - `agents/feature_adapter.py` is a Mission-1-shaped observation encoder over
    `terrain`, `unit_id`, and `marker_id` fields from the Mission 1 wrapper
  - `agents/masked_actor_critic_training.py` hardcodes `Mission1Env`,
    Mission-1-shaped feature-adapter construction, Mission 1 action-count
    lookup, and Phase 5 artifact/output framing
  - `eval/learned_policy_eval.py` hardcodes `Mission1Env` and the Mission 1
    observation/info surface
  - `eval/learned_policy_reporting.py`,
    `eval/learned_policy_summary.py`,
    `eval/learned_policy_seeds.py`, and the `phase5_*` CLI entrypoints are
    Mission-1-local historical surfaces rather than the right home for Mission
    3 learning
  - `learned_policy.py` and `masked_actor_critic.py` still point at the
    Mission 1 observation type alias even though the policy/value core itself
    is otherwise mission-neutral
- Lower-level learning pieces already look reusable enough for a bounded port:
  - `MaskedActorCriticNetwork`
  - masked legal-action selection
  - `LearnedPolicy` and legal-id / mask reading helpers
  - `EpisodeMetrics` and the accepted fixed-seed metric schema
- Fairness/planning context is now explicit:
  - the preserved Mission 3 historical and strengthened heuristic/search
    surfaces remain oracle-style or branch-clairvoyant references
  - this packet should not relabel those references as fair learned-policy
    targets
  - the new learned-policy surface should instead be framed as observation-
    based Mission 3 learning on the accepted wrapper contract
- The live question is transfer, not redesign:
  - there is no current repo evidence that the accepted Mission 3 wrapper,
    fixed staged action catalog, or default terminal-only reward must be
    rewritten before trying the first honest transfer pass

Why this packet must stay bounded:

- the wrapper contract is already accepted, so reopening env design would blur
  the question this packet is supposed to answer
- the fastest honest test is to port the existing Phase-5 learner family first,
  not redesign it immediately
- Mission 3 historical heuristic/search surfaces must remain preserved as
  historical references rather than being rewritten inside a learning packet
- the fair-vs-oracle distinction now matters, so this packet should report the
  learned surface clearly instead of widening into the full fair-agent ladder
- heavy training/eval runs can be operator-controlled, which keeps Delivery
  Threads code-bounded rather than terminal-bound
- weak first-pass learning evidence is still a valid packet outcome; it is not
  permission to auto-open reward shaping, architecture churn, or Mission 4

Accepted scope:

- one bounded first-pass Mission 3 learning transfer on the accepted wrapper
  using the current masked actor-critic learner family as the first baseline
- one Mission-3-local feature/observation adapter plus only the smallest
  shared adapter seam needed to host it cleanly
- only the minimal training/eval loop sharing or parameterization directly
  required to run the same learner family on `Mission3Env`
- one Mission-3-local seed policy, artifact root, reporting surface, and thin
  operator commands for train / eval / summary reruns
- one first accepted Mission 3 learned result surface with explicit
  observation-based-vs-historical-reference framing
- focused tests and short in-thread smoke verification for the new learning
  path
- tracked internal planning/status docs and closeout guidance for this packet

Out of scope:

- reward shaping by default
- broad RL redesign:
  policy/value architecture churn, PPO-style replacement, hierarchical
  policies, action-scoring networks, generic entity encoders, or a generic
  multi-mission RL platform
- reopening the Mission 3 env/wrapper contract, Mission 3 historical search
  packet, or Mission 3 search-strengthening packet
- Mission 1 honest/fair-agent lab work, Mission 4 content, or Mission 2 same-
  rules transfer
- generic cross-mission evaluation/reporting buildout beyond the minimal seams
  this packet directly needs
- treating a weak first-pass Mission 3 learned result as automatic
  implementation failure
- broad checkpoint-security hardening (`C7`) unless a direct dependency appears

Learning-side seams that must adapt now:

- observation/feature encoding:
  the current Phase 5 adapter is Mission-1-specific and cannot consume the
  accepted Mission 3 observation shape honestly as-is
- env binding in training/eval:
  the current train/eval/checkpoint path hardcodes `Mission1Env`
- Mission-local seed and artifact policy:
  Mission 3 learning needs its own seed aliases, output root, and result
  surface without overwriting accepted Phase 5 artifacts
- reporting and summary framing:
  Mission 3 learned results need a Mission-3-local comparison surface that can
  keep preserved historical heuristic/search references visible but accurately
  qualified
- thin observation typing/protocol seams:
  the current learned-policy interfaces should stop depending on the Mission 1
  observation alias as the implicit universal learning contract

Key planning decisions:

### Learner-family decision

- Port the existing Phase-5-style masked actor-critic learner family first.
- Do not redesign the learner family immediately.
- The packet should answer transferability first, then only open redesign if
  the result surface clearly justifies it later.
- Packet success is:
  one honest end-to-end Mission 3 training/eval result surface plus a clear
  interpretation of whether transfer exists.
- Packet success is not:
  beating the preserved Mission 3 heuristic/search references by default.

### Feature / observation encoding decision

- Use a Mission-3-local feature adapter.
- Allow one tiny shared adapter seam or protocol if it materially reduces
  duplication between Mission 1 and Mission 3 adapters.
- Do not force the Mission 1 adapter into a generic multi-mission flattened
  schema.
- Do not redesign the accepted Mission 3 observation surface to fit the old
  Mission 1 adapter.
- Mission 1 and Mission 3 may legitimately keep different mission-local
  flattened encodings on top of the shared structured observation family.

### Shared vs Mission-local learning-stack decision

- Shared now, if kept narrow:
  - `MaskedActorCriticNetwork`
  - masked legal-action selection
  - `LearnedPolicy` legal-id / legal-mask helpers
  - the smallest env-factory / adapter-factory / action-count parameterization
    needed for shared train/eval loops
  - `EpisodeMetrics` aggregation and stable metrics-table formatting
- Mission-1-local and preserved:
  - accepted Phase 5 seed aliases/results
  - Phase 5 anchor comparisons against preserved Mission 1 random/heuristic
    numbers
  - `outputs/phase5/`
  - `phase5_*` thin operator surfaces as historical Mission 1 commands
- Mission-3-local for this packet:
  - feature adapter
  - learning seed aliases and artifact root
  - train/eval/report/summary helpers
  - thin train/eval/summary operator surfaces
  - learned-result reporting against preserved Mission 3 history

### Reward decision

- Keep the default terminal-only reward unchanged in this packet:
  victory `+1`, defeat `-1`, nonterminal `0`.
- Do not open reward shaping by default.
- A weak or noisy first-pass result is evidence about transfer, not a reason to
  immediately rewrite the reward contract.

### Fairness / historical reporting decision

- Preserve the Mission 3 historical and strengthened heuristic/search numbers
  as oracle-style or branch-clairvoyant historical references.
- New Mission 3 learned-policy reporting should separate:
  - the observation-based learned result surface for this packet
  - preserved historical Mission 3 comparison references
- Do not rewrite the preserved historical benchmark framing in this packet;
  label it carefully in the new learned-policy-local reporting instead.
- Do not open the full Mission 1 honest/fair-agent research ladder here.

### Result interpretation decision

- The packet should not require a strong Mission 3 win rate for acceptance.
- A result that is clearly above random would be encouraging evidence of
  transfer.
- A weak or even zero-win first pass is still an accepted answer if the run is
  honest, reproducible, and clearly reported.

## Heavy-run workflow for this packet

Delivery Thread-owned verification can include:

- focused unit and integration tests for new learning seams
- `.venv/bin/ruff check src tests`
- `.venv/bin/pytest -q`
- preserved short regression surfaces:
  - `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`
  - `.venv/bin/python -m solo_wargame_ai.cli.mission3_env_smoke --seed 0`
- preserved benchmark/reference commands if a package touches the relevant
  shared code:
  - `.venv/bin/python -m solo_wargame_ai.cli.phase6_stronger_baseline --mode benchmark`
  - `.venv/bin/python -m solo_wargame_ai.cli.mission3_comparison --mode benchmark`
- one short in-thread Mission 3 learning smoke:
  - tiny training run with a small episode count
  - checkpoint load/re-eval smoke
  - short smoke evaluation on a small fixed seed set

Operator-controlled heavy runs should own:

- the first substantive Mission 3 training runs on the accepted training-seed
  set
- full `0..199` benchmark evaluation of the selected checkpoints
- aggregate summary over the accepted Mission 3 artifact dirs
- any repeated reruns or ablations once the first result surface exists

Minimum new in-thread verification that should still run before acceptance:

- one end-to-end short Mission 3 train command that writes a checkpoint
- one short Mission 3 learned-policy eval command that loads that checkpoint
- one summary/report smoke over the short artifacts if the package introduces a
  summary surface

## Mission 3 learning packet status block

- Delivery A: pending
- Delivery B: pending
- Delivery C: conditional
- Packet overall: open
- Planning audit date: March 15, 2026
- Closeout audit date: pending
- Blocking findings before dispatch:
  - none acceptance-blocking
- Active planning risks:
  - Mission-1-shaped adapter drift
  - generic RL-platform creep
  - fairness/oracle reporting blur
  - weak-result overreaction
  - heavy-run ownership confusion
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
- Default result-interpretation rule:
  - a weak first-pass learner result is evidence, not automatic packet failure
- End-of-packet default gate:
  - close the packet once a first Mission 3 learned result surface exists and
    its transfer verdict is explicit
  - after closeout, move by default to the Mission 1 honest/fair-agent lab
    kickoff rather than to reward shaping, Mission 4, or a generic RL-platform
    packet

## Delivery A - Mission 3 learner transfer core

Goal:

- port the existing masked actor-critic learner family onto `Mission3Env`
  through the smallest bounded learning-core seam changes

Concrete deliverables:

- one Mission-3-local feature adapter over the accepted Mission 3 observation
  surface
- only the smallest shared adapter/protocol widening needed so Mission 1 and
  Mission 3 adapters can coexist cleanly
- only the minimal training/eval-loop sharing or parameterization required to
  run the same learner family on `Mission3Env`
- focused tests proving Mission 3 short-train / checkpoint-load / eval smoke
  works without breaking accepted Mission 1 behavior

Likely files / subsystems touched:

- `src/solo_wargame_ai/agents/`
- `src/solo_wargame_ai/eval/learned_policy_eval.py`
- `src/solo_wargame_ai/eval/learned_policy_seeds.py` or a new adjacent
  Mission-3-local seed module
- focused tests under `tests/agents/` and `tests/eval/`

Required in-thread verification:

- focused tests for:
  - Mission 3 feature-adapter determinism
  - Mission 3 short training smoke
  - Mission 3 checkpoint load / policy-factory smoke
  - Mission 1 regression on the preserved Phase 5 learning surface
- `.venv/bin/ruff check src tests`
- `.venv/bin/pytest -q`
- `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`
- `.venv/bin/python -m solo_wargame_ai.cli.mission3_env_smoke --seed 0`
- one short Mission 3 learning smoke command once the package adds it

Explicitly not owned by the Delivery Thread:

- the full substantive Mission 3 training sweep
- the full `0..199` learned-policy benchmark reruns

Risks / traps:

- turning a bounded port into a generic multi-mission RL platform
- reshaping the accepted Mission 3 observation contract to fit Mission 1 code
- silently changing accepted Mission 1 Phase 5 behavior while extracting shared
  seams
- opening reward shaping or policy/network redesign because the first transfer
  pass is not yet strong

Completion criteria:

- the accepted Phase-5-style learner family can complete one short Mission 3
  train/eval/checkpoint smoke on `Mission3Env`
- Mission 1 Phase 5 learning surfaces remain regression-safe
- the packet now has a real learning-core path onto Mission 3 without broad RL
  redesign

Commit shape:

- one implementation commit preferred
- two commits acceptable only if a tiny shared-seam extraction is materially
  clearer to review separately from the Mission-3-local adapter slice

Analysis-before-edit:

- required

## Delivery B - Mission 3 local reporting/operator surface and operator handoff

Goal:

- add the smallest Mission-3-local train/eval/report/operator surface needed to
  rerun the first learning cycle honestly and hand the substantive runs to the
  user as operator-owned commands

Concrete deliverables:

- one Mission-3-local train CLI / operator surface
- one Mission-3-local learned-policy eval CLI / operator surface
- one Mission-3-local summary/report surface over Mission 3 artifact dirs
- explicit learned-result reporting that keeps preserved Mission 3 historical
  heuristic/search references separate and clearly qualified
- focused CLI/report tests plus a short end-to-end smoke over tiny artifacts

Likely files / subsystems touched:

- `src/solo_wargame_ai/eval/`
- `src/solo_wargame_ai/cli/`
- focused tests under `tests/eval/` and `tests/cli/`
- tracked internal docs only where the operator workflow and preserved-surface
  framing need to be recorded

Required in-thread verification:

- focused tests for any new train/eval/summary/report helpers
- `.venv/bin/ruff check src tests`
- `.venv/bin/pytest -q`
- `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
- `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`
- `.venv/bin/python -m solo_wargame_ai.cli.mission3_env_smoke --seed 0`
- one short Mission 3 train smoke command
- one short Mission 3 learned-policy eval smoke command
- one short Mission 3 learning summary/report smoke command

Operator-controlled heavy runs to hand off after Delivery B:

- the accepted first-pass Mission 3 training seeds at the substantive episode
  count chosen by implementation
- full `0..199` benchmark evaluation of the selected checkpoints
- aggregate summary over the resulting Mission 3 artifact dirs

Risks / traps:

- mixing thin operator/reporting work with broad RL-platform buildout
- quietly overwriting or reframing accepted Phase 5 historical surfaces
- presenting preserved Mission 3 heuristic/search references as fair learned
  targets
- smuggling reward shaping or architecture redesign into a reporting package

Completion criteria:

- the user has clear Mission-3-local operator commands for train / eval /
  summary
- the new learned-result report surface is explicit about preserved historical
  Mission 3 references and the fair-vs-oracle distinction
- substantive training/eval work can move to operator-owned runs without more
  code changes by default

Commit shape:

- one implementation/docs commit preferred

Analysis-before-edit:

- required

## Delivery C - Optional results-assimilation or closeout-support finish

Status:

- conditional only

Goal:

- only if Deliveries A/B plus operator-run artifacts do not already leave a
  clean closeout-ready Mission 3 learning surface, add one narrow follow-up to
  finish summary/report assimilation without widening scope

Concrete deliverables:

- at most one narrow follow-up for:
  - one result-summary parsing/reporting fix
  - one explicit preserved-surface wording correction
  - one tiny operator-handoff or closeout-support helper tied directly to the
    first accepted Mission 3 learned result surface
- no reward shaping
- no broad RL redesign
- no Mission 1 fair-agent lab work
- no Mission 4 content

Likely files / subsystems touched:

- `src/solo_wargame_ai/eval/`
- `src/solo_wargame_ai/cli/` only if directly required
- small directly related tests
- tracked internal docs for closeout support

Required verification:

- focused tests for any new result-assimilation helper
- `.venv/bin/ruff check src tests`
- `.venv/bin/pytest -q`
- the short Mission 3 learning smoke commands affected by the fix

Risks / traps:

- turning a closeout finish into another learning-architecture package
- reopening Delivery A/B design questions instead of fixing one narrow blocker
- letting operator-run result assimilation blur preserved historical Mission 3
  references

Completion criteria:

- the Packet Master Thread can close the packet without another implementation
  package
- the first accepted Mission 3 learned result surface is compact, explicit, and
  clearly separated from preserved historical reference tables

Commit shape:

- one small implementation/docs follow-up commit only if the package is opened

Analysis-before-edit:

- required

## Recommended Delivery Thread sequence for the Mission 3 learning packet

Preferred sequence:

1. Delivery A
2. Delivery B
3. Delivery C only if Deliveries A/B plus operator-run artifacts do not
   already leave a clean closeout-ready result surface

Do not mix in one thread:

- the learner-core port with broad reporting/operator work
- any Mission 3 learning package with Mission 3 env redesign
- any Mission 3 learning package with reward shaping by default
- any Mission 3 learning package with Mission 1 honest/fair-agent lab work
- any Mission 3 learning package with Mission 4 content landing
- bounded shared seam extraction with a generic multi-mission RL platform

End-of-packet decision gate:

- Close the packet if:
  - the Phase-5-style learner family can run end-to-end on `Mission3Env`
  - a first accepted Mission 3 learned result surface exists
  - preserved historical Mission 3 heuristic/search references remain separate
    and clearly qualified
  - the transfer verdict is explicit, even if the first-pass result is weak
- Do not open reward shaping or broad RL redesign by default unless:
  - the accepted first-pass result and closeout analysis explicitly justify a
    new packet
- Do not reopen Mission 3 env/wrapper or search packets by default unless:
  - implementation exposes a new concrete blocker that was not visible in the
    March 15 audit

## Archived packet - Mission 3 env/wrapper extension

Closeout summary:

- Delivery A completed and landed in `fe919df mission3: add env wrapper contract`
- Delivery B completed and landed in `faaba99 mission3: add env smoke cli`
- Delivery C was not opened because Deliveries A/B already left a clean
  closeout-ready packet surface
- Packet result:
  Mission 3 now has an accepted observation-based wrapper contract on top of
  `ResolverEnvSession`, plus a thin smoke/operator surface that stays separate
  from preserved historical Mission 3 comparison history

Packet goal:

- extend the accepted env boundary from Mission 1 to Mission 3 on top of the
  shared resolver-backed session seam
- make Mission 3 observation / action / reward / termination semantics
  explicit without opening Mission 3 learning, Mission 4 content, or a broad
  multi-mission env platform
- preserve the accepted Mission 1 anchors plus the preserved historical and
  strengthened Mission 3 search surfaces as separate comparison history while
  the new wrapper introduces an observation-based Mission 3 contract

Planning audit findings:

- Repository state was rechecked on March 15, 2026 before dispatch:
  - `git status --short` showed unrelated local tracked edits only in
    `docs/internal/experiments/README.md`
  - `git log --oneline --decorate -12` showed `HEAD` on
    `f3be20a docs: sync roadmap and local experiment workflow`
  - `.venv/bin/pytest -q` passed with `251 passed in 230.69s`
  - `.venv/bin/ruff check src tests` passed with `All checks passed!`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
    preserved `random 2/16`, `heuristic 11/16`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`
    preserved the accepted Mission 1 wrapper smoke surface:
    `32` action ids, `35` decision steps, defeat, reward `-1.0`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase5_summary --artifact-dir outputs/phase5/train_seed_101_ep_2000 --artifact-dir outputs/phase5/train_seed_202_ep_2000 --artifact-dir outputs/phase5/train_seed_303_ep_2000`
    preserved best `144` and median `133`
  - `.venv/bin/python -m solo_wargame_ai.cli.phase6_stronger_baseline --mode benchmark`
    preserved `random 11/200`, `heuristic 157/200`, `rollout 195/200`
  - `.venv/bin/python -m solo_wargame_ai.cli.mission3_comparison --mode benchmark`
    preserved the historical Mission 3 benchmark surface:
    `random 0/200`, `heuristic 72/200`, `rollout-search 105/200`
- The accepted env growth seam is now real in code:
  - `env/resolver_session.py` owns deterministic reset / step / episode
    bookkeeping over the resolver path
  - `env/mission1_env.py` is already a thin Mission 1 wrapper over that seam
  - `env/observation.py` and `env/action_catalog.py` remain Mission-1-local
    helpers even though their filenames and exports still read package-wide
- No Mission 3 env surface exists yet:
  - there is no `Mission3Env`
  - there is no Mission 3 observation builder
  - there is no Mission 3 action-id catalog or Mission 3 env smoke operator
    path
- The active missing piece is wrapper-contract clarity, not more prep:
  - Mission 3 learning would otherwise either depend on raw `GameState`
    surfaces through `agents/base.py` or force Mission-1-shaped env helpers
    into cross-mission roles prematurely
- Fairness now matters explicitly in planning:
  - the March 14 reports support keeping player-visible observation and
    oracle-style preserved search references conceptually separate
  - this packet should clarify that split in the new wrapper contract without
    rewriting historical benchmark numbers
- Mission 3 itself still does not force generic platform work:
  - it remains a `clear_all_hostiles` mission with one start hex
  - the accepted shared seam is enough for this packet
  - multi-start support, objective-dispatch generalization, and a generic env
    registry remain later gates

Why this packet should go now rather than Mission 3 learning immediately:

- Mission 3 learning without an accepted wrapper would couple experiments to an
  unstable observation/action contract
- the env-prep packet already landed the missing structural seam, so the next
  honest question is the Mission 3 env contract itself
- this packet is the smallest way to make fair-vs-oracle interpretation less
  ambiguous without opening the whole honest-agent research ladder
- delaying wrapper decisions until after learning would make later Mission 3
  learning evidence harder to interpret cleanly

Accepted scope:

- one Mission-3-capable wrapper surface built on `ResolverEnvSession`
- one explicit Mission 3 observation boundary and Mission-3-local action-id /
  legality surface
- one explicit Mission 3 default reward / termination / truncation policy,
  aligned with the current accepted env policy unless a direct blocker appears
- one thin Mission 3 env smoke/operator surface if needed for acceptance
- internal planning/status docs and closeout guidance for this packet

Out of scope:

- Mission 3 learning experiments or learned-policy integration
- Mission 1 honest/fair-agent lab work or Mission 3 honest-agent search work
- Mission 4 content, true multi-start support, or new objective families
- generic multi-mission env registry/platform, generic action-platform, or
  generic cross-mission benchmark/reporting rewrite
- rewriting preserved Mission 3 historical or strengthened search numbers
- broad fair-vs-oracle benchmark-policy overhaul beyond the packet-local
  clarification needed to keep the wrapper honest
- reward shaping, tensorization/feature-adapter redesign, or policy/network
  architecture work

Active risks now:

- Mission-1-shaped helper drift:
  current env helper names/exports can accidentally imply that Mission 1
  observation or action shapes are the future shared API
- Hidden-information contract drift:
  if the first Mission 3 wrapper leaks raw `GameState` or `rng_state`, the new
  wrapper will immediately blur fair-vs-oracle reasoning
- Action-surface overreach:
  generic cross-mission action abstraction or macro compression would mix this
  wrapper packet with broader platform design that has not been justified yet
- Preserved-surface confusion:
  new Mission 3 wrapper smoke or later learning outputs could be misread as
  replacements for the preserved oracle-style Mission 3 search history unless
  docs/operator surfaces stay explicit
- Shared-layer creep:
  if mission-local observation/reward/catalog logic is pushed into the shared
  seam unnecessarily, this packet will become a broad env redesign instead of a
  bounded extension

Active follow-ups from `docs/internal/independent_audit_followups.md`:

- `P4-R4` active as a preservation rule:
  - keep the accepted Phase 3 / Phase 4 / Phase 5 / Phase 6 references
    discoverable and unchanged
- `C6` active as a caution:
  - Mission-1-specific heuristic coupling should not become a future env or
    agent contract
- `C11` active as a planning constraint:
  - keep fair observation-based wrapper work distinct from oracle-style
    benchmark history

Not active by default in this packet unless a direct blocker appears:

- `C1` replay draw-prediction coupling
- `C2` `legal_actions.py` refactor
- `C3` genuine multi-start support
- `C4` objective-dispatch generalization
- `C5` synthetic fixtures
- `C7` checkpoint-loading hardening
- `T1` through `T4` tooling backlog

Key planning decisions:

### Wrapper shape decision

- Implement a separate `Mission3Env` wrapper surface.
- That wrapper should be thin and mission-local, built directly on
  `ResolverEnvSession`.
- Do not harden `Mission1Env` into a polymorphic base class or generic
  `MissionEnv` platform.
- Do not stop at raw shared-session helpers; this packet needs an accepted
  Mission 3 wrapper contract, not just another seam fragment.

### Observation boundary decision

- Default Mission 3 observation must be player-visible only.
- Required visible ingredients:
  current decision context, public mission/map data, British units, revealed
  German units, unresolved marker positions, and already-observed activation
  bookkeeping/roll information.
- Excluded by default:
  raw `GameState`, `rng_state`, unrealized reveal-table outcomes, branch-
  realized future combat/reveal results, and other simulator-only debugging
  truth.
- Allowed simplifications:
  the observation may remain a structured serializable dict and may continue to
  include redundant visible mission metadata for usability/debugging.
- Not allowed in this packet:
  a second simulator-truth-rich default observation surface for learning.

### Action exposure and legality decision

- The first Mission 3 wrapper should expose a Mission-3-local fixed action-id
  catalog over the staged `GameAction` family.
- Legality remains resolver-owned and should surface as legal ids plus a
  fixed-length mask at the wrapper boundary.
- The catalog should stay aligned with the current staged domain decisions:
  British unit selection, double handling, die selection, order execution
  choice, concrete order parameters, and German activation order.
- Do not introduce macro-actions, parameterized action heads, or a generic
  cross-mission catalog framework in this packet.
- Minimal shared helper widening is acceptable only if it stays truly narrow
  and directly prevents duplication of existing session/legality logic.

### Reward and termination decision

- The default Mission 3 wrapper reward should match the accepted Mission 1
  default:
  victory `+1`, defeat `-1`, nonterminal `0`.
- Mission victory and mission defeat, including turn-limit defeat, should map
  to `terminated=True` and `truncated=False`.
- `truncated=True` remains reserved for external wrapper limits such as
  optional `max_steps`.
- Reward shaping stays out of scope until a later Mission 3 learning packet
  provides evidence that the default contract is insufficient.

### Shared vs mission-local env API decision

- Shared env-layer API for this packet:
  `ResolverEnvSession`, `ResolverSessionSnapshot`, `NormalizedEnvState`,
  `normalize_env_state`, and any tiny truly generic legality-selection helper
  if the implementation needs it.
- Mission-local for this packet:
  `Mission3Env`, Mission 3 observation schema/builder, Mission 3 action
  catalog/id semantics, Mission 3 default reward helper, Mission 3 env smoke
  operator surface, and Mission 3-specific tests.
- Treat current Mission 1 observation/action helpers and broad `env.__init__`
  re-exports as local historical API, not as the template for a broad future
  shared surface.

### Fairness and preserved-surface decision

- This packet clarifies:
  the new Mission 3 wrapper is an observation-based interface with a
  player-visible default boundary.
- This packet does not rewrite:
  the preserved Mission 3 historical and strengthened search results or their
  operator surfaces.
- Historical Mission 3 heuristic/search references remain valuable, but they
  stay documented as preserved search/oracle-style comparison history rather
  than as the new wrapper's fairness contract.
- The packet should avoid naming or reporting that makes Mission 3 env smoke or
  later Mission 3 learning results look like replacements for the preserved
  Mission 3 comparison tables.
- The broader fair-agent ladder remains later work:
  honest Mission 1 lab, Mission 2 transfer, and honest Mission 3 approximation
  are not part of this packet.

### Operator-surface decision

- One new thin Mission 3 env smoke command is justified for acceptance and
  regression reruns.
- No Mission 3 env benchmark/reporting platform is justified in this packet.
- Preserve existing operator commands unchanged:
  `cli/phase3_baselines.py`
  `cli/phase4_env_smoke.py`
  `cli/phase5_summary.py`
  `cli/phase6_stronger_baseline.py`
  `cli/mission3_comparison.py`

### Public-doc sync decision

- Do not widen public docs preemptively in this planning thread.
- After implementation acceptance, a bounded public-doc sync is justified:
  `README.md`, `ROADMAP.md`, `ASSUMPTIONS.md`, and `docs/reward_design.md`
  should be revisited only to capture the accepted Mission 3 wrapper contract
  and preserved-surface framing.

Boundary to later packets:

- This packet includes:
  - one observation-based Mission 3 env contract
  - one Mission-3-local action catalog and legality-mask surface
  - one Mission 3 reward / termination / smoke operator surface
  - only the smallest shared helper widening that is directly required
- Mission 3 learning begins only when:
  - an accepted Mission 3 wrapper already exists
- Mission 1 honest/fair-agent lab begins only when:
  - a later packet explicitly opens fair-agent research rather than wrapper
    delivery
- Mission 4 begins only when:
  - new content beyond Mission 3 is being transcribed or supported
- Broad platform work begins only when:
  - more than one active mission genuinely requires shared abstraction beyond
    the narrow seams above

## Mission 3 env/wrapper packet status block

- Delivery A: completed (`fe919df`)
- Delivery B: completed (`faaba99`)
- Delivery C: not opened
- Packet overall: closed
- Planning audit date: March 15, 2026
- Closeout audit date: March 15, 2026
- Blocking findings before dispatch:
  - none acceptance-blocking
- Active planning risks:
  - Mission-1-shaped helper drift
  - hidden-information contract drift
  - preserved-surface confusion
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
- Executed package order:
  - Delivery A
  - Delivery B
- End-of-packet default gate:
  - proceed to Mission 3 learning experiments
  - do not open another preparatory packet by default unless implementation
    exposes one new concrete blocker that was not visible in the March 15 audit

## Delivery A - Mission 3 wrapper contract + mission-local env surface

Status:

- completed (`fe919df`)

Goal:

- land the main Mission 3 wrapper surface on top of the accepted shared
  resolver session seam without widening into a generic env platform

Concrete deliverables:

- `Mission3Env` with deterministic `reset(seed=...)` / `step(action_id)` over
  `ResolverEnvSession`
- one Mission 3 player-visible observation builder
- one Mission-3-local fixed action-id catalog and legality-mask surface
- one Mission 3 default terminal reward helper aligned with the accepted Mission
  1 contract
- focused tests proving seeded reset/step determinism, invalid-action
  rejection, legality-mask correctness, and observation-boundary discipline

Likely files / subsystems touched:

- `src/solo_wargame_ai/env/`
- new Mission 3 wrapper/helper files under `src/solo_wargame_ai/env/`
- `src/solo_wargame_ai/env/legal_action_mask.py` only if a tiny shared helper
  widening is directly required
- `src/solo_wargame_ai/env/__init__.py` only if the Mission 3 wrapper needs a
  minimal explicit export
- focused Mission 3 env tests under `tests/`

Required tests / verification:

- focused tests for:
  - deterministic seeded Mission 3 reset/step preservation
  - Mission 3 legal-id / mask preservation
  - invalid/illegal action-id handling
  - player-visible observation boundary with no `rng_state` / raw `GameState`
    leakage
  - terminal vs truncation semantics preservation
- `.venv/bin/pytest -q`
- `.venv/bin/ruff check src tests`
- `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
- `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`
- `.venv/bin/python -m solo_wargame_ai.cli.phase5_summary --artifact-dir outputs/phase5/train_seed_101_ep_2000 --artifact-dir outputs/phase5/train_seed_202_ep_2000 --artifact-dir outputs/phase5/train_seed_303_ep_2000`
- `.venv/bin/python -m solo_wargame_ai.cli.phase6_stronger_baseline --mode benchmark`
- `.venv/bin/python -m solo_wargame_ai.cli.mission3_comparison --mode benchmark`

Risks / traps:

- turning Mission 3 wrapper work into a generic env platform
- silently compressing the staged domain decision model into macro-actions
- leaking hidden simulator truth or `rng_state` in the default observation
- changing accepted Mission 1 env semantics while widening shared helpers
- letting Mission 3 wrapper naming/reporting blur the preserved historical
  search surfaces

Completion criteria:

- one accepted `Mission3Env` exists on top of `ResolverEnvSession`
- observation, action, legality, reward, and termination contracts are all
  explicit and test-covered
- Mission 1 wrapper behavior remains regression-safe
- the repo has a clean observation-based Mission 3 env boundary for the next
  learning packet

Commit shape:

- one implementation commit preferred
- two commits acceptable only if a tiny shared-helper widening is materially
  clearer to review separately from the mission-local wrapper slice

Analysis-before-edit:

- required

## Delivery B - Mission 3 env smoke/operator and preservation finish

Status:

- completed (`faaba99`)

Goal:

- add the smallest operator/preservation finish needed so the new Mission 3 env
  surface is rerunnable and clearly separated from preserved historical
  Mission 3 comparison history

Concrete deliverables:

- one thin Mission 3 env smoke CLI/operator surface
- only the minimal `env/` export cleanup or naming clarification required to
  keep shared-vs-local env boundaries honest
- focused CLI/tests proving the Mission 3 env smoke path is deterministic and
  discoverable
- any narrow wording/docs sync directly required to keep Mission 3 wrapper
  smoke separate from preserved historical Mission 3 comparison reports

Likely files / subsystems touched:

- `src/solo_wargame_ai/cli/`
- `src/solo_wargame_ai/env/__init__.py` only if directly required
- focused CLI/env tests under `tests/cli/` and `tests/`
- tracked internal docs only where the new accepted operator surface needs to
  be recorded

Required tests / verification:

- focused tests for any new operator/export surface
- `.venv/bin/pytest -q`
- `.venv/bin/ruff check src tests`
- `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`
- the new Mission 3 env smoke command
- `.venv/bin/python -m solo_wargame_ai.cli.mission3_comparison --mode benchmark`
  if Delivery B touches preservation/report wording around the historical
  Mission 3 surface

Risks / traps:

- mixing a thin operator finish with Mission 3 learning scaffolding
- turning export cleanup into a broad env naming campaign
- quietly reframing preserved historical Mission 3 benchmarks while trying to
  document the new wrapper
- adding benchmark/reporting platform work when one smoke operator surface is
  enough

Completion criteria:

- one accepted Mission 3 env smoke rerun path exists
- preserved historical Mission 3 comparison surfaces remain explicit and
  separate
- shared env seams and Mission-local wrapper details are clearer after the
  package than before it

Commit shape:

- one small implementation/docs commit preferred

Analysis-before-edit:

- required if Delivery B changes exports or preserved-surface wording

## Delivery C - Optional shared/local API cleanup finish

Status:

- not opened

Goal:

- only if Deliveries A/B do not already leave a clean closeout-ready packet
  surface, add one narrow follow-up to clarify shared-vs-local env API
  boundaries without widening scope

Concrete deliverables:

- at most one narrow follow-up for:
  - one small shared-helper rename or export cleanup
  - one preservation fix if Delivery A/B made Mission-local helpers look like a
    new generic default API
  - one tiny closeout-support docs clarification directly tied to the wrapper
    boundary
- no Mission 3 learning
- no Mission 4 content
- no benchmark-policy rewrite

Likely files / subsystems touched:

- `src/solo_wargame_ai/env/`
- `src/solo_wargame_ai/cli/` only if directly required
- small directly related tests

Required tests / verification:

- focused tests for any new helper/export surface
- `.venv/bin/pytest -q`
- `.venv/bin/ruff check src tests`
- `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`
- the new Mission 3 env smoke command if Delivery C touches it

Risks / traps:

- turning a closeout finish into a broad env redesign
- reopening Delivery A/B design questions instead of fixing one narrow blocker
- smuggling generic platform work into a preservation pass

Completion criteria:

- the Packet Master Thread can close the packet without another preparatory
  implementation thread
- the shared seam and Mission-local env contracts are clearly separated in code
  and docs

Commit shape:

- one small implementation or docs-and-implementation follow-up commit only if
  the package is opened

Analysis-before-edit:

- required

## Recommended Delivery Thread sequence for the Mission 3 env/wrapper packet

Preferred sequence:

1. Delivery A
2. Delivery B
3. Delivery C only if Deliveries A/B do not already leave a clean closeout-
   ready surface

Do not mix in one thread:

- Mission 3 wrapper implementation with Mission 3 learning experiments
- Mission 3 wrapper implementation with Mission 1 honest/fair-agent lab work
- Mission 3 wrapper implementation with Mission 4 content landing
- Mission 3 mission-local observation/action work with a generic env platform
  or action-platform buildout
- wrapper operator/preservation finish with a broad benchmark-policy rewrite
- bounded shared-helper widening with unrelated replay/objective/multi-start
  work

End-of-packet decision gate:

- Proceed directly to Mission 3 learning experiments if:
  - `Mission3Env` exists and is accepted on top of `ResolverEnvSession`
  - the default Mission 3 observation boundary is explicit, player-visible, and
    test-covered
  - the Mission 3 action-id / legality-mask surface is explicit and stable
  - default reward / termination / truncation semantics are documented and
    rerunnable
  - preserved historical Mission 3 search/oracle surfaces remain separate and
    unchanged
  - no new concrete shared-seam blocker appears
- Do not open another preparatory packet by default unless:
  - implementation exposes a new concrete blocker that was not visible from the
    March 15 repo evidence
  - or Deliveries A/B cannot leave a clean closeout-ready packet surface

## Archived packet - Mission 3 env-prep hardening and adapter seam

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
    `docs/internal/thread_reports/2026-03-12_mission3_cross_mission_probes.md`
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

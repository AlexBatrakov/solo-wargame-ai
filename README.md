# Solo Wargame AI

[![CI](https://github.com/AlexBatrakov/solo-wargame-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/AlexBatrakov/solo-wargame-ai/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/github/license/AlexBatrakov/solo-wargame-ai)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)

Rule-faithful Python simulator, search baselines, and learning experiments for
a stochastic solo hex-based tactical wargame.

This repository is a compact platform for:
- building deterministic simulation infrastructure around a stochastic game;
- comparing heuristic, search, and learning agents on fixed seed suites;
- testing how agent behavior changes as missions become richer and information
  becomes less direct;
- keeping domain rules, environment wrappers, agents, and evaluation tooling
  cleanly separated.

## Why this project matters

The game mixes several engineering and modeling challenges:
- stochastic outcomes with fixed-seed reproducibility requirements;
- partial and delayed information through hidden enemy markers;
- constrained, staged decisions instead of a simple flat action list;
- tactical movement and fire resolution on a hex grid;
- mission-specific objectives and content ladders.

That makes it a useful sandbox for:
- simulation and engine design;
- testing deterministic behavior in stochastic systems;
- search/planning baselines;
- RL-style environment design and first learning experiments.

In practice, the project demonstrates:
- software engineering for a stateful rules engine with replayable transitions;
- experiment design with preserved benchmark anchors and seed-controlled runs;
- ML/RL-oriented interface design through observation-based environment
  wrappers;
- careful handling of the boundary between fair observation-based agents and
  oracle-style planning references.

## Current highlights

- **Mission 1 now has a fair reference plus preserved historical anchors**
  The repo has a regression-checked Mission 1 engine, replay path, baseline
  agents, `Mission1Env`, first learner, a stronger rollout reference, and a
  tracked exact fair-ceiling workflow.
- **Mission 3 now spans domain, wrapper, and first learning transfer**
  The repository supports deterministic Mission 3 load/init/play/replay,
  accepted `Mission3Env`, preserved local search references, and a first
  bounded observation-based learning path.
- **Historical search references stay separate from wrapper/learning surfaces**
  Mission 3 preserves oracle-style local search history while the public env
  and learner path stay observation-based by default.
- **The simulator keeps the written staged turn flow**
  The engine models explicit decision contexts rather than hiding gameplay
  structure behind undocumented macro-actions.
- **Reproducibility is a first-class concern**
  Fixed-seed evaluation, deterministic replay, and CI-backed verification are
  part of the normal workflow.

## Benchmark snapshot

Mission 1 fixed 200-seed benchmark:

| Agent | Wins | Notes |
| --- | ---: | --- |
| `RandomAgent` | 11 / 200 | baseline floor |
| learned policy (best seed) | 144 / 200 | terminal-only reward, masked actor-critic |
| `HeuristicAgent` | 157 / 200 | strong hand-coded baseline |
| `RolloutSearchAgent` | 195 / 200 | bounded stronger search/planning reference |

These numbers are intentionally preserved as comparison anchors while richer
content slices land.

Benchmark framing:
- Mission 1 anchors above are preserved historical references.
- Mission 1 now also has an exact fair reference from the tracked workflow:
  fair ceiling `0.949848647767`, or about `189.97` expected wins per `200`.
- That exact fair reference stays separate from the preserved
  `RolloutSearchAgent 195/200` oracle/planner-like reference.
- Mission 3 historical `heuristic` / `rollout-search` numbers are kept as
  oracle-style planning references rather than as the public wrapper or
  learning contract.

## Technical themes

- **Simulation and state modeling**
  Deterministic transitions, replay support, mission loading/validation, and
  explicit staged decision contexts.
- **Search and baselines**
  Random, heuristic, rollout-search, and strengthened local search references
  on preserved seed sets.
- **Environment and learning**
  Lightweight RL-friendly wrappers, legality masks, fixed action catalogs, and
  first masked actor-critic transfer experiments.
- **Evaluation discipline**
  CLI-driven smoke checks, regression coverage, fixed-seed benchmark surfaces,
  and CI-backed verification.

## Implemented scope

### Mission 1

- deterministic mission loading and initialization;
- explicit staged decision contexts and legal-action generation;
- reveal, combat, morale, German Fire Zones, turn rollover, and terminal
  conditions;
- structured replay / text trace support;
- random, heuristic, learned, and stronger rollout baselines;
- exact Mission 1 fair-ceiling workflow plus Mission-1-local operator/report
  surface under `solo_wargame_ai.eval.mission1_exact_fair_ceiling` and
  `solo_wargame_ai.cli.mission1_exact_fair_reference`;
- dependency-free `Mission1Env` wrapper with fixed 32-id action catalog,
  legality masks, and terminal-only default reward.

### Mission 3

- deterministic config loading and validation;
- deterministic resolver-playable domain slice with Building, Hill, bounded
  wooded-hill semantics, and German Rifle Squad behavior;
- Mission-3-only historical and strengthened local search comparison surfaces
  with fixed smoke and benchmark seed aliases;
- dependency-free `Mission3Env` wrapper with a player-visible default
  observation boundary, opaque contact handles, a fixed 49-id Mission-3-local
  action catalog, resolver-owned legality masks, and terminal-only default
  reward;
- a first bounded Mission 3 learning path with local train / eval / summary
  operator surfaces under `outputs/mission3_learning/`;
- thin `mission3_env_smoke` support for rerunning the accepted wrapper surface
  without mixing it into the preserved historical comparison CLI;
- a shared resolver-backed env session seam that Mission-local wrappers can
  build on without duplicating lifecycle/state progression logic;
- replay/integration coverage through the accepted resolver path.

What is deliberately **not** implemented yet:
- the later Mission 1 honest-search baselines and value-function study beyond
  the exact fair reference;
- broader cross-mission reporting and experiment infrastructure;
- generic search / experiment platform work.

## Architecture at a glance

- `src/solo_wargame_ai/domain/`
  Core game rules, state transitions, legality, combat, terrain, missions, RNG.
- `src/solo_wargame_ai/io/`
  Mission loading, validation, and replay/serialization helpers.
- `src/solo_wargame_ai/env/`
  RL-friendly Mission 1 / Mission 3 wrappers plus a shared resolver-backed env
  session seam.
- `src/solo_wargame_ai/agents/`
  Random, heuristic, rollout-search, and learned-policy code.
- `src/solo_wargame_ai/eval/`
  Episode runner, benchmark harness, metrics, and reporting helpers.
- `tests/`
  Unit, integration, replay, env, agent, and CLI regression coverage.

## Documentation map

- [Roadmap](ROADMAP.md)
- [Architecture](docs/architecture.md)
- [Game specification](docs/game_spec.md)
- [State model](docs/state_model.md)
- [Action model](docs/action_model.md)
- [Testing strategy](docs/testing_strategy.md)
- [Mission config conventions](docs/mission_config.md)
- [Rules digest](docs/reference/rules_digest.md)

## Current planned next step

The current next step is **Mission 1 honest search baselines**.

The Mission 1 honest/fair-agent lab kickoff is now closed:
- the fair-vs-oracle contract is explicit;
- a tracked exact Mission 1 fair-ceiling workflow exists;
- the exact fair reference has been rerun through the tracked operator surface.

The next packet should build on that exact fair reference by trying bounded
non-oracle Mission 1 baselines such as expected one-step scoring, depth-limited
expectimax, sampled expectimax, and bounded rollouts.

Likely follow-on packets after that:
- Mission 1 value-function study after the honest-search baseline packet is
  stable;
- Mission 2 as a same-rules transfer step before moving to harder honest-agent
  work on Mission 3;
- later RL-agent design questions such as state/action encoding and
  policy/value architecture, once the fair-agent line is stronger;
- later Mission 4 or another bounded richer content slice;
- cross-mission evaluation/reporting once more than one active mission needs to
  be compared.

## Development setup

The project keeps development tooling in a local `.venv` created from
`pyproject.toml`.

```bash
make bootstrap
make test
make lint
```

Accepted local verification commands also include:

```bash
.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke
.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0
.venv/bin/python -m solo_wargame_ai.cli.phase5_summary \
  --artifact-dir outputs/phase5/train_seed_101_ep_2000 \
  --artifact-dir outputs/phase5/train_seed_202_ep_2000 \
  --artifact-dir outputs/phase5/train_seed_303_ep_2000
.venv/bin/python -m solo_wargame_ai.cli.phase6_stronger_baseline --mode benchmark
```

## License

This project is released under the [MIT License](LICENSE).

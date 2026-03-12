# Solo Wargame AI

[![CI](https://github.com/AlexBatrakov/solo-wargame-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/AlexBatrakov/solo-wargame-ai/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/github/license/AlexBatrakov/solo-wargame-ai)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)

Rule-faithful Python simulator, search baselines, and learning experiments for
a stochastic solo hex-based tactical wargame.

This repository focuses on:
- deterministic stateful simulation for a stochastic game;
- explicit legal-action generation over staged player decisions;
- reproducible baseline, search, and learning comparisons on fixed seed sets;
- a clean separation between domain rules, environment interfaces, agents, and
  evaluation tooling.

## Why this project is interesting

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

## Current highlights

- **Mission 1 full stack is complete**
  Domain engine, replay path, baseline agents, `Mission1Env`, first learner,
  and a stronger rollout baseline all exist and are regression-checked.
- **Mission 3 domain slice has landed**
  The repository now supports deterministic load/init/play/replay for a richer
  content slice with Buildings, Hills, bounded wooded-hill semantics, and the
  German Rifle Squad.
- **Mission 3 strengthened search stack is in place**
  Mission 3 now has preserved historical `random`, `heuristic`, and
  `rollout-search` references plus an accepted stronger local
  `rollout-search-strengthened` surface.
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

## Current implemented scope

### Mission 1

- deterministic mission loading and initialization;
- explicit staged decision contexts and legal-action generation;
- reveal, combat, morale, German Fire Zones, turn rollover, and terminal
  conditions;
- structured replay / text trace support;
- random, heuristic, learned, and stronger rollout baselines;
- dependency-free `Mission1Env` wrapper with fixed 32-id action catalog,
  legality masks, and terminal-only default reward.

### Mission 3

- deterministic config loading and validation;
- deterministic resolver-playable domain slice;
- support for Building, Hill, bounded wooded-hill semantics, and German Rifle
  Squad behavior;
- Mission-3-only historical and strengthened search comparison surfaces with
  fixed smoke and benchmark seed aliases;
- replay/integration coverage through the accepted resolver path.

What is deliberately **not** implemented yet:
- a shared Mission-3-ready env-adapter seam beyond the accepted Mission 1
  wrapper;
- Mission 3 env/wrapper extension;
- Mission 3 learning experiments;
- broader multi-mission infrastructure;
- generic experiment/search platform work.

## Architecture at a glance

- `src/solo_wargame_ai/domain/`
  Core game rules, state transitions, legality, combat, terrain, missions, RNG.
- `src/solo_wargame_ai/io/`
  Mission loading, validation, and replay/serialization helpers.
- `src/solo_wargame_ai/env/`
  RL-friendly Mission 1 wrapper and observation/action/mask boundary.
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

## Current next step

The next recommended packet is:

**Mission 3 env-prep hardening and adapter seam**

The goal is to make one small preparatory pass before Mission 3 env work:
- tighten mission-config/schema validation where recent audits found real gaps;
- add a narrow shared env-adapter seam so Mission 3 does not become a second
  isolated `MissionXEnv` island;
- keep the work bounded and avoid a broad repository reorganization.

Likely follow-on packets after that:
- Mission 3 env/wrapper extension;
- Mission 3 learning experiments;
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

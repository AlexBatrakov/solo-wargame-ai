# Solo Wargame AI

A Python project for building a rule-faithful simulator of a small stochastic solo hex-based wargame and, later, training agents to play it.

## Project goals

This repository has two main goals:

1. Build a clean, testable simulation engine for a compact solo tactical wargame.
2. Use the simulator as an environment for baseline agents and, later, machine learning / reinforcement learning agents.

The project is intentionally developed in stages. The first milestone is **not** RL.  
The first milestone is a reliable game engine for a minimal scenario.

## Why this project exists

This is both:
- a software engineering project focused on stateful simulation, testing, and clean architecture;
- a machine learning project focused on sequential decision-making under uncertainty.

The game contains several ingredients that make it interesting for AI:
- stochastic outcomes;
- constrained legal actions;
- spatial tactics on a hex grid;
- partial / delayed information;
- mission-based victory conditions.

## Current scope

Current development focuses on:
- maintaining and extending the completed Mission 1 engine slice;
- keeping the domain model aligned with the written staged turn structure rather
  than a simplified macro-action abstraction;
- preserving deterministic tests and replayable traces as the engine grows;
- using the accepted baseline, env, and first-learning stack as the foundation
  for stronger baselines/search and later content-extension decisions;
- keeping repository structure and naming understandable as the implementation
  grows beyond the first RL pass.

## Current engine slice

The current implemented slice supports:
- Mission 1 as a playable scenario;
- mission loading and deterministic initial state creation;
- explicit decision-context / activation-step state;
- legal action generation and state-driven resolution for British and German
  phases;
- reveal, combat, morale, turn rollover, and terminal outcome handling;
- deterministic seeded simulation and structured text replay;
- a minimal Phase 3 agent contract over the resolver facade;
- a dependency-free Phase 4 `Mission1Env` wrapper with structured
  player-visible observation, fixed Mission 1 action ids, resolver-derived
  legal-action ids / masks, deterministic `reset(seed=...)`, and terminal-only
  default reward;
- `RandomAgent`, `HeuristicAgent`, fixed-seed batch evaluation, and a manual
  benchmark CLI that remains the accepted pre-RL comparison reference.

## Non-goals for MVP

The following are explicitly out of scope for the first version:
- graphical UI;
- full campaign support;
- full fidelity implementation of every advanced rule;
- polished RL training pipeline;
- performance optimization beyond what is needed for correctness and repeatability.

## Repository structure

- `docs/` — public project documentation and formal specifications
- `docs/reference/` — source rule materials and reference booklet(s)
- `configs/` — scenario, agent, and experiment configs
- `src/` — Python implementation code
- `tests/` — unit and integration tests
- `outputs/` — logs, replays, checkpoints, and reports

## Development setup

The project keeps development tooling in a local `.venv` created from
`pyproject.toml`.

- `make bootstrap` creates or refreshes `.venv` and installs `.[dev]`
- `make test`, `make lint`, and `make fmt` automatically use `.venv`
- editors that auto-detect a repository-local `.venv` should pick it up without
  extra per-project setup

## Development philosophy

The project is built in layers:

1. **Domain layer**  
   Pure game logic and state transitions.

2. **Environment layer**  
   RL-friendly wrapper around the domain logic.

3. **Agents layer**  
   Random, heuristic, search-based, and later learned agents.

4. **Evaluation layer**  
   Benchmarking, metrics, and experiment reports.

## Design constraints

The repository should preserve a few core engineering constraints from the start:

- engine-first development;
- model in-scope rules exactly as written, including intermediate decision steps;
- deterministic seeded simulations;
- explicit legal-action generation;
- clean separation between domain logic and RL-specific code.

The rule PDF in `docs/reference/` is a reference source.  
Over time, the implementation source of truth should become the public documentation under `docs/` together with the tested code under `src/`.
Mission data conventions are documented in `docs/mission_config.md`.

## Planned implementation order

1. Write formal specs and assumptions.
2. Build the minimal domain engine.
3. Add deterministic tests and reproducibility support.
4. Add baseline agents.
5. Add an RL-friendly environment wrapper.
6. Run training and evaluation experiments.

## Planned milestones

1. Write formal specs and assumptions.
2. Implement minimal domain model.
3. Implement one playable mission with deterministic seeding.
4. Add baseline agents.
5. Add a first RL-friendly environment wrapper.
6. Experiment with RL and compare against baselines.

## Status

Current repository state:
- Phase 1 implementation is complete and captured by the local
  `phase1-complete` milestone tag;
- Mission 1 can be loaded, initialized, and played through the accepted
  resolver path under `src/solo_wargame_ai/domain/`;
- deterministic replay / trace support exists under `src/solo_wargame_ai/io/`;
- Phase 2 hardening is complete: engine contracts, replay/reproducibility
  contracts, and the minimal CI gate are in place;
- Phase 3 baselines are complete: the repository now includes an explicit
  agent-facing contract, random and heuristic baselines, fixed-seed comparison
  metrics, and a manual baseline rerun command;
- Phase 4 Mission 1 wrapper foundations are accepted: `src/solo_wargame_ai/env/`
  now exposes the dependency-free `Mission1Env` surface together with the
  accepted observation, action-id, legality, reward, and termination
  contracts;
- Phase 5 learning experiments are complete: the repository now includes a
  bounded masked actor-critic training/evaluation path, explicit seed-policy
  separation, Phase 5 train/eval/summary CLIs, and an accepted Mission 1
  result with `144/200` best wins and `133/200` median wins on the preserved
  200-seed benchmark;
- Phase 6 post-first-RL strengthening is complete: the repository now includes
  accepted responsibility-based learned-policy helper module names, a bounded
  stronger rollout baseline CLI, and an accepted Mission 1 stronger-baseline
  result with `195/200` wins on the preserved 200-seed benchmark;
- the repository verifies locally with `.venv/bin/pytest -q` and
  `.venv/bin/ruff check src tests`, and the same narrow gate is defined in
  GitHub Actions;
- later milestones such as additional Mission 1 strengthening, broader mission
  coverage, and later tooling/platform decisions remain open.

## Not implemented yet

At this stage, the repository does **not** yet include:
- a `gymnasium` dependency or generic RL experiment platform;
- broader mission and advanced-rule coverage;
- a generic search/planning platform;
- post-Phase-6 strengthening work beyond the accepted rollout baseline and
  first learner path.

## Next macro-step

The first end-to-end Mission 1 learning pass and the first post-learning
strengthening pass are now complete on the accepted env surface.
Phase 6 added a bounded stronger rollout baseline that reached `195/200` wins
on the preserved 200-seed benchmark, above both the accepted heuristic anchor
`157/200` and the accepted learned best `144/200`.
The next macro-step is another bounded Mission 1 strengthening/search planning
pass on top of the preserved Phase 3 comparison reference, the accepted Phase 5
operator surface, and the accepted Phase 6 stronger-baseline result.
Mission 3/4 extension remains later follow-on work by default.

## Manual operator commands

Accepted local commands:

- Phase 4 env smoke:
  `.venv/bin/python -m solo_wargame_ai.cli.phase4_env_smoke --seed 0`
- Phase 3 comparison reference:
  `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode smoke`
- Phase 3 benchmark reference:
  `.venv/bin/python -m solo_wargame_ai.cli.phase3_baselines --mode benchmark`
- Phase 5 train smoke:
  `.venv/bin/python -m solo_wargame_ai.cli.phase5_train --training-seed 101 --episodes 8 --checkpoint-interval 4 --output-dir outputs/phase5/train_smoke_seed_101_ep_8`
- Phase 5 learned-policy smoke eval:
  `.venv/bin/python -m solo_wargame_ai.cli.phase5_learned_policy_eval --checkpoint outputs/phase5/train_seed_101_ep_2000/checkpoints/selected_checkpoint.pt --mode smoke`
- Phase 5 learned-policy benchmark eval:
  `.venv/bin/python -m solo_wargame_ai.cli.phase5_learned_policy_eval --checkpoint outputs/phase5/train_seed_101_ep_2000/checkpoints/selected_checkpoint.pt --mode benchmark`
- Phase 5 aggregate summary:
  `.venv/bin/python -m solo_wargame_ai.cli.phase5_summary --artifact-dir outputs/phase5/train_seed_101_ep_2000 --artifact-dir outputs/phase5/train_seed_202_ep_2000 --artifact-dir outputs/phase5/train_seed_303_ep_2000`
- Phase 6 stronger baseline smoke:
  `.venv/bin/python -m solo_wargame_ai.cli.phase6_stronger_baseline --mode smoke`
- Phase 6 stronger baseline benchmark:
  `.venv/bin/python -m solo_wargame_ai.cli.phase6_stronger_baseline --mode benchmark`

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
- formalizing the rules into a programmable specification;
- fixing the domain model around the written turn structure rather than a
  simplified macro-action abstraction;
- building an MVP engine for a minimal mission;
- creating deterministic tests and replayable simulations;
- implementing simple baseline agents before attempting RL.

## MVP goals

The MVP should support:
- Mission 1 only as the first playable target;
- hex-grid representation;
- core unit representation;
- explicit decision-context / activation-step state;
- game state transitions;
- legal action generation;
- deterministic seeded simulation;
- textual logging / replay;
- random and heuristic agents.

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
5. Add Gymnasium-compatible environment.
6. Experiment with RL and compare against baselines.

## Status

Current repository state:
- documentation and planning files are in place;
- the rulebook has been distilled into a software-oriented digest under
  `docs/reference/`;
- Mission 1 has been transcribed into an initial TOML mission config under
  `configs/missions/`;
- implementation has not started yet;
- the next step is to create the package skeleton and start the Mission 1
  engine foundation.

## Not implemented yet

At this stage, the repository does **not** yet include:
- a playable engine;
- mission loading;
- a baseline evaluation loop;
- an RL environment;
- benchmark results.

## Immediate next steps

The most useful next coding targets are:
- create `src/solo_wargame_ai/`;
- implement core enums, decision-context primitives, and hex-grid helpers.
- implement the Mission 1 config loader;
- implement the first focused unit tests around coordinates and mission loading.

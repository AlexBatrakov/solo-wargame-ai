# Scratch Experiments

This directory is for local throwaway or exploratory experiment code:

- one-off Python runners
- quick benchmark probes
- temporary search / heuristic experiments
- local helper scripts used to generate thread reports

Files here are intentionally gitignored except for this README.

## Usage

- put markdown notes and handoff reports in `docs/internal/thread_reports/`
- put scratch code here
- if an experiment becomes durable, either:
  - promote it into tracked project code under `src/` / `tests/` / `cli/`, or
  - summarize the result in tracked docs and keep the code local

## Suggested naming

- flat files for very small one-off scripts:
  - `mission3_turn_search_experiment.py`
- dated subdirectories for heavier experiments:
  - `2026-03-15_mission1_exact_lab/`

## Scope boundary

This directory is not a stable API surface and not the source of truth for
project behavior or planning decisions.

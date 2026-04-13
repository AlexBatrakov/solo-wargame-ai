# Development Workflow

## Purpose

This file describes project-wide engineering rules for development.

It is public and should contain stable workflow principles, not private prompt details.

## Workflow principles

1. Make architectural changes intentionally.
2. Keep domain logic separate from RL/training code.
3. Prefer small, testable increments.
4. Every nontrivial rule implementation should come with tests.
5. Ambiguous rule interpretations should be documented in `ASSUMPTIONS.md`.
6. Stable design decisions should be reflected in public docs under `docs/`.
7. If an in-scope rule exposes player-visible substeps, model them explicitly in
   the domain layer rather than silently compressing them away.
8. Promote reusable experiment machinery into tracked code only after it has
   proven stable across more than one run or mission; keep one-off scripts and
   round-specific miners local.
9. Preserve historical baseline agents and promoted successor agents as
   separate tracked surfaces rather than silently rewriting benchmark anchors.
10. If the repository exposes computation to an external orchestrator, prefer
    one versioned machine-readable runner contract over coupling external
    systems directly to human-oriented CLIs or heavy research workflows.

## Preferred implementation order

1. specification
2. state / action design
3. domain implementation
4. tests
5. baseline agents
6. RL wrapper
7. training experiments

After that initial build sequence is complete, prefer evidence-driven bounded
packets rather than automatically extending the numbered-phase model forever.

## Change policy

When adding a new feature:
1. update spec if needed;
2. implement the minimal domain change;
3. add or update tests;
4. update assumptions if rule interpretation changed;
5. only then extend agents / environment if required.

Scope control should come from limiting which missions and rule families are
implemented, not from rewriting the flow of in-scope rules.

When experiments produce a reusable evaluation workflow, prefer this migration
shape:

1. keep the raw exploratory script local;
2. extract the durable library surface into `src/`;
3. add one thin CLI/operator surface in `src/solo_wargame_ai/cli/`;
4. keep heavy generated artifacts under local or ignored output directories;
5. only then retire or down-rank the local exploratory script.

When exposing a new orchestration-facing runner surface:

1. keep the first contract narrow and versioned;
2. prefer one stable operation over a broad multi-operation interface;
3. make success and failure payloads explicitly machine-readable;
4. keep aggregate metrics in the top-level result;
5. write optional per-episode detail as an artifact rather than embedding it
   inline by default.

## Refactoring policy

Refactoring is encouraged when it improves:
- clarity,
- separation of concerns,
- testability,
- determinism.

Refactoring should not silently change game behavior without corresponding documentation and tests.

## Notes

Local working notes and helper artifacts may live outside the public
documentation set.

For heavy exact-search or many-seed research runs:

- prefer a thin operator-facing local command when runtime is long enough that
  it should not live in a long interactive session;
- if the workload is naturally seed-parallel or episode-parallel, bounded
  multi-core local execution is acceptable as a future workflow improvement,
  provided reproducibility and accepted benchmark semantics stay explicit.

# Tests Directory

This directory now contains the focused project test suite.

Current durable layout favors subsystem-oriented grouping where it improves
navigation without forcing broad fixture churn:

- `tests/agents/`
- `tests/eval/`
- `tests/cli/`
- `tests/integration/`
- additional domain and env tests may remain at the root until a later
  mechanical regrouping is justified

Current coverage includes:

- grid, terrain, and RNG primitives;
- mission loading and validation;
- runtime-state and legality invariants;
- British activation flow;
- reveal and non-attack orders;
- British combat, German phase, and terminal conditions;
- deterministic replay / trace regression.

Tests should continue to stay narrow, behavior-focused, and aligned with the
public testing strategy in `docs/testing_strategy.md`.

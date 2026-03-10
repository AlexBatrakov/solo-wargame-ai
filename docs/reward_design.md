# Reward Design

## Status

Reward design is no longer "ignore this completely", but it is still not a
domain-layer concern.

At the current project stage, reward design belongs to Phase 4 RL-environment
planning and later Phase 5 experiments rather than to the domain engine.

## Current policy

Until the first RL wrapper is accepted:

- do not optimize the domain architecture around reward shaping;
- keep terminal mission success/failure as the primary reward anchor;
- treat Phase 3 evaluation metrics as analysis signals, not default reward
  terms;
- make any shaping explicit and environment-level rather than implicit or
  scattered across training code.

## When this document should be expanded

This file should be updated when the project reaches:

- Phase 4 - RL environment planning / implementation, and
- Phase 5 - first learning experiments.

## Current open questions

- Should the first RL setup use only terminal reward?
- Is any shaping needed for learning stability on Mission 1?
- Which metrics should remain analysis-only and not be optimized directly?
- Should turn-limit defeat map to the same terminal-reward family as other
  losses, with `truncated` reserved only for external time/step limits?

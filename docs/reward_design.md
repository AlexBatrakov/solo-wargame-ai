# Reward Design

## Status

Reward design is intentionally deferred.

At the current project stage, reward design belongs to the future RL /
environment layer rather than to the domain-engine planning baseline.

## Current policy

Until the simulator is playable and baseline agents exist:

- do not optimize the architecture around reward shaping;
- keep terminal mission success/failure as the primary future reward anchor;
- treat evaluation metrics and reward design as related but distinct topics.

## When this document should be expanded

This file should be updated when the project reaches:

- Phase 4 - RL environment, or
- earlier only if an implementation decision in the environment layer requires a
  stable reward contract.

## Current open questions

- Should the first RL setup use only terminal reward?
- Is any shaping needed for learning stability on Mission 1?
- Which metrics should remain analysis-only and not be optimized directly?

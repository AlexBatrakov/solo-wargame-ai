# Reward Design

## Status

The first reward contract is now accepted for the Mission 1 env wrapper, but
reward is still not a domain-layer concern.

## Accepted default contract

- `Mission1Env` uses terminal-only default reward:
  - victory `+1`
  - defeat `-1`
  - nonterminal states `0`
- mission victory and mission defeat, including turn-limit defeat, map to
  `terminated=True` and `truncated=False`
- `truncated=True` is reserved for external wrapper limits such as
  `Mission1Env(max_steps=...)`
- Phase 3 evaluation metrics remain analysis/comparison signals, not reward
  terms

## Current policy

- do not optimize the domain architecture around reward shaping;
- keep the accepted terminal-only default reward stable unless a later phase
  explicitly changes it;
- treat Phase 3 evaluation metrics as analysis signals, not default reward
  terms;
- make any shaping explicit and environment-level rather than implicit or
  scattered across training code.

## When this document should be expanded

This file should be updated when the project reaches:

- Phase 5 - first learning experiments.

## Current open questions

- Is any shaping needed for learning stability on Mission 1?
- If shaping is added later, which terms should be treated as experimental
  variants rather than new defaults?
- Which metrics should remain analysis-only and not be optimized directly?

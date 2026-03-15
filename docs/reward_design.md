# Reward Design

## Status

The accepted default reward contract now covers both Mission 1 and Mission 3
env wrappers, but reward is still not a domain-layer concern.

## Accepted default contract

- `Mission1Env` and `Mission3Env` use terminal-only default reward:
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
- keep the accepted terminal-only default reward stable unless a later packet
  explicitly changes it;
- treat Phase 3 evaluation metrics as analysis signals, not default reward
  terms;
- make any shaping explicit and environment-level rather than implicit or
  scattered across training code.

## Phase 5 planning boundary

The accepted Phase 5 planning decision is:

- the first end-to-end learner pass on a newly accepted wrapper should use the
  accepted default reward unchanged;
- a failed or weak terminal-only pass is evidence, not permission to
  immediately rewrite the default contract;
- any shaping belongs only in an explicit optional follow-up package after the
  terminal-only result has been evaluated honestly;
- shaped variants must remain clearly separate from the default env reward
  contract.

## If shaping is opened later

The following boundaries apply:

- shaping must remain environment-level or wrapper-level, not domain-level;
- terminal mission outcome must stay the dominant signal;
- shaping should use only narrow mission-progress terms that are auditable
  against the accepted env observation and episode result;
- do not translate the full Phase 3 metric table into reward terms;
- do not reward shorter games, lower decision counts, or other convenience
  metrics unless a later accepted phase packet explicitly changes that policy.

## When this document should be expanded

This file should be updated when the project reaches:

- a later accepted phase packet changes the default reward contract;
- an optional shaped-reward variant becomes stable enough to deserve durable
  documentation beyond internal planning notes.

## Current open questions

- Does the accepted terminal-only reward produce a learnable enough signal on
  Mission 1 for the chosen first learner?
- If shaping is needed later, which single bounded variant is the least
  distorting proxy for mission progress?
- Which comparison metrics remain analysis-only even if optional shaping is
  tested?

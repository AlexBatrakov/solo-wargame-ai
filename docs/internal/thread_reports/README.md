# Thread Reports

This directory is for short local reports created during Codex threads.

These reports are intentionally gitignored, except for this README and the
template file.

Experiment scripts do not belong here. Put scratch runners and one-off helper
code under `docs/internal/experiments/` instead.

## Why this exists

Thread reports are useful for:

- preserving the local plan used inside a thread,
- recording what was inspected and changed,
- making it easier to recover context after interruptions,
- keeping temporary working notes out of tracked project history.

## Important rule

Files here are **not** the project source of truth.

If a thread settles:

- a rule interpretation,
- an architecture decision,
- a workflow rule,
- a roadmap change,
- or any other durable behavior,

that decision must be promoted into tracked docs such as:

- `ASSUMPTIONS.md`
- `ROADMAP.md`
- public files under `docs/`
- tracked internal workflow docs under `docs/internal/`

## Suggested usage

For each nontrivial thread, create one local report from `TEMPLATE.md`.

Suggested filename pattern:

- `YYYY-MM-DD_short-topic.md`

Examples:

- `2026-03-07_phase0-audit.md`
- `2026-03-07_hexgrid-slice.md`

## Recommended contents

Keep reports short.

They should usually capture:

- goal,
- docs read,
- local plan,
- files changed,
- assumptions made,
- verification performed,
- next obvious step.

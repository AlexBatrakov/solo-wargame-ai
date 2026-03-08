# Internal Notes

This directory is for local working notes, prompt drafts, scratch files, and AI
workflow artifacts.

Contents here are not considered the public source of truth.

Any stable architectural, rule, or implementation decision should eventually be
reflected in public documentation under `docs/`.

Recommended starting points:

- `docs/internal/execution_plan.md` - the concrete build order and task queue
- `docs/internal/thread_playbook.md` - how Codex threads should work on this repo
- `docs/internal/orchestration_policy.md` - thread roles, delivery packages, and cross-thread handoff rules
- `docs/internal/codex_workflow.md` - broader workflow guidance
- `docs/internal/repo_layout.md` - intended repository and package structure
- `docs/internal/commit_policy.md` - when and how to group commits
- `docs/internal/independent_audit_followups.md` - preserved findings and deferred improvements from external audits

Local working reports can live under `docs/internal/thread_reports/`.
That subdirectory is intended for gitignored per-thread markdown notes, with
only its README/template tracked.

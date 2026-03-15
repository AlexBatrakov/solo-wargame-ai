# Internal Notes

This directory is for local working notes, prompt drafts, scratch files, and AI
workflow artifacts.

Contents here are not considered the public source of truth.

Any stable architectural, rule, or implementation decision should eventually be
reflected in public documentation under `docs/`.

Recommended starting points:

- `docs/internal/execution_plan.md` - the active planning control surface and
  packet backlog
- `docs/internal/thread_playbook.md` - how Codex threads should work on this repo
- `docs/internal/orchestration_policy.md` - thread roles, delivery packages, and cross-thread handoff rules
- `docs/internal/codex_workflow.md` - broader workflow guidance
- `docs/internal/repo_layout.md` - intended repository and package structure
- `docs/internal/commit_policy.md` - when and how to group commits
- `docs/internal/independent_audit_followups.md` - preserved findings and deferred improvements from external audits

Local working reports can live under `docs/internal/thread_reports/`.
That subdirectory is intended for gitignored per-thread notes, with only its
README/template tracked.

Scratch experiment code, one-off runners, and local helper scripts should live
under `docs/internal/experiments/`, also gitignored except for its README.

Other local-only helper material, such as project/career positioning notes for
resumes, cover letters, or interview prep, can live under
`docs/internal/project_profiles/`.

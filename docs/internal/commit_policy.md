# Commit Policy

## Purpose

This file defines how commits should be grouped and when they should be made
during Codex-assisted work on this repository.

The goal is to keep history readable and to make each commit easy to trust,
review, and revert if necessary.

## Core rule

Prefer small, coherent commits that represent one finished slice of work.

A good commit should usually have:

- one clear purpose,
- a reviewable diff,
- matching docs/tests when behavior changed,
- a commit message that explains the slice accurately.

## When to commit

Make a commit when one of these is true:

1. a planning phase or milestone boundary has been cleanly closed;
2. a narrow implementation slice is complete and locally verified;
3. a risky refactor is complete and the repository has returned to a stable
   state;
4. a stable architecture or workflow decision has been documented and should not
   live only in chat history.

## When not to commit

Avoid committing:

- mixed unrelated changes,
- half-finished speculative code,
- placeholder files with no clear role,
- broken intermediate states unless an explicit WIP checkpoint is desired.

## Preferred grouping

For this repository, default to one commit per bounded slice.

Examples:

- one docs/planning commit for a finished planning pass,
- one engine commit for hex-grid primitives plus their tests,
- one loader commit for mission parsing plus validation tests,
- one rule-slice commit for a specific action/resolution family.

If a thread touched two clearly different concerns, split them into two commits
instead of one large mixed commit.

## Commit ownership by thread role

Commit ownership should follow context locality, not ceremony.

### Super Master Thread

Usually commits only:

- cross-phase planning updates,
- workflow/policy updates,
- external-audit assimilation,
- milestone closeout records if they are not phase-local.

### Phase Master Thread

Usually commits only:

- phase-plan updates,
- phase status updates,
- closeout/handoff docs,
- other docs-only changes tied to phase orchestration.

The Phase Master Thread should not normally re-handle implementation commits
just because it reviewed them.

### Delivery Thread

Usually owns implementation commits for its accepted delivery package because it
has the freshest local context on the diff and verification.

Default rule:

- implementation code and tests are committed from the Delivery Thread after
  Phase Master acceptance
- planning/status docs are committed from the Phase Master Thread

This avoids duplicate re-review and repeated context loading in a different
thread.

## Commit timing inside a delivery package

Do not commit after every micro-step.

Default rule:

- one accepted delivery package should usually become one commit or a small
  coherent commit series
- package-internal substeps should remain uncommitted until the package is
  accepted, unless there is a strong reason to checkpoint earlier

Examples of strong reasons:

- a risky refactor has been stabilized,
- the package naturally contains two clearly separable commit slices,
- the user explicitly wants intermediate checkpoints.

## Fix handling after review

If the Phase Master Thread requests a narrow follow-up fix, keep that fix in the
same Delivery Thread by default.

Preferred handling:

1. if the package is not committed yet, fold the fix into the same final commit
2. if the package is already committed and the fix is narrow, create one small
   follow-up `fix:` commit in the same Delivery Thread

Do not open a new fix-only thread unless the fix changes subsystem or requires
independent audit.

## Commit message style

Use short imperative messages.

Preferred patterns:

- `phase0: close planning handoff`
- `docs: add commit and reporting policy`
- `phase1: add hex-grid primitives`
- `tests: cover mission loader validation`

The first word should communicate the scope of the change quickly.

## Verification before commit

Before committing, check:

1. the diff matches one coherent purpose;
2. relevant docs were updated if the decision became stable;
3. tests were run when code behavior changed, or the commit clearly states that
   it is docs-only;
4. no unrelated local artifacts were accidentally included.

## Codex thread expectation

At the end of a nontrivial thread, Codex should be able to say:

- whether the thread produced a commit-ready slice,
- whether the changes should be one commit or several,
- what verification was performed,
- what the next obvious commit-sized task is.

## Relationship to thread reports

Commits are durable project history.
Local thread reports are temporary working memory.

Stable decisions must be promoted into tracked docs and/or commits.
Gitignored reports must not become the only place where important project truth
exists.

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

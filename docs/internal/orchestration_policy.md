# Orchestration Policy

## Purpose

This file defines how work should be split across Codex threads so that the
project stays coordinated without wasting excessive context or tokens.

## Core problem this policy solves

Earlier phases proved that one thread per micro-stage creates too much repeated
startup cost.

The orchestration benefits were real:

- clear review points,
- narrow task scopes,
- good phase tracking,

but the costs were also real:

- too many new chats,
- repeated rereading of the same docs,
- unnecessary token burn,
- duplicate review/commit handling between planning and implementation threads.

This policy keeps the orchestration benefits while reducing thread count.

## Operating model

Use four thread roles:

1. `Super Master Thread`
2. `Phase/Packet Master Thread`
3. `Delivery Thread`
4. `Optional External Audit Thread`

Not every phase or later bounded packet needs all four at once.

## Thread roles

### Super Master Thread

One long-lived thread for the whole project.

Responsibilities:

- overall roadmap control,
- cross-phase planning,
- workflow/process decisions,
- milestone tagging,
- handling external audits,
- deciding when a new Phase/Packet Master Thread should be opened.

The Super Master Thread should not be used for routine implementation.

### Phase/Packet Master Thread

One thread per phase during the original build sequence, or one thread per
active bounded packet after the numbered roadmap is exhausted.

Responsibilities:

- refine the active plan,
- maintain the active phase/packet control surface,
- define delivery packages,
- generate prompts for Delivery Threads,
- accept/reject completed delivery packages,
- update status and closeout records,
- hand off to the next macro-step.

The Phase/Packet Master Thread should normally stay out of code implementation.

### Delivery Thread

The main execution unit for implementation work.

Responsibilities:

- implement one delivery package,
- work across multiple user-controlled turns if needed,
- keep scope bounded to the package,
- report checkpoints back to the user for the Phase/Packet Master Thread,
- produce a commit-ready slice when the package is done.

### Optional External Audit Thread

Use only when an independent second opinion is worth the extra token cost.

## Delivery packages

### Definition

A delivery package is a bounded work package larger than a single micro-stage
but smaller than a full phase or later bounded packet.

It is the default unit for Delivery Threads.

### Default size

Prefer:

- `2` to `4` Delivery Threads per phase or active packet,
- not one new thread per every tiny stage.

Typical package size:

- one coherent subsystem,
- one vertical slice,
- or two adjacent low-risk stages.

## Active packet

Each Phase/Packet Master Thread should maintain a compact active packet.

This should live in the tracked internal planning surface, usually in
`docs/internal/execution_plan.md` or a closely linked phase section.

The active packet should contain only the active essentials:

- phase goal,
- current package list,
- accepted scope,
- out-of-scope list,
- stable contracts,
- required verification commands,
- next one or two delivery packages,
- critical follow-ups from audits.

Implementation threads should start from the active packet first, then read only
the additional docs and files relevant to the package.

## Multi-turn Delivery Thread protocol

Delivery Threads may span multiple user-controlled turns.
That is the default for any package that cannot be completed in a single pass.

### How a delivery package should start

The Phase/Packet Master Thread should dispatch the package with:

- package goal,
- scope,
- expected deliverables,
- stop conditions,
- verification requirements,
- report format.

### How the Delivery Thread should behave mid-package

At each meaningful checkpoint, it should report:

- package name/id,
- what substeps are done,
- which files changed,
- what verification ran,
- whether it recommends:
  - continue in the same thread,
  - return to the Phase/Packet Master Thread for review,
  - stop because of a blocker.

### When to return to the Phase/Packet Master Thread

Return to the Phase/Packet Master Thread when:

- the package is complete,
- the package is blocked,
- the thread discovered an architecture-affecting ambiguity,
- the thread needs a scope decision before continuing.

Do not bounce back to the Phase/Packet Master Thread after every tiny substep.

## Handoff protocol between threads

The user may copy reports manually between chats.
That is acceptable and expected.

To keep this workable, every nontrivial Delivery Thread report should be short
and structured enough for copy/paste handoff.

Recommended handoff fields:

- package name,
- objective,
- completed substeps,
- files changed,
- verification performed,
- blockers/open questions,
- commit-readiness,
- recommended next action.

## When a new thread is actually needed

Open a new thread when at least one of these is true:

1. the role changes
2. the subsystem changes materially
3. the architectural boundary changes
4. an independent review is needed
5. the current thread has become too noisy to remain a clean package container

Do **not** open a new thread by default for:

- a narrow follow-up fix,
- the next small step in the same package,
- an extra commit in the same bounded subsystem,
- routine back-and-forth inside one package.

## Default thread budget per phase or packet

Preferred:

- `1` Phase/Packet Master Thread
- `2` to `4` Delivery Threads
- `0` or `1` optional external audit threads

## Acceptance states for a delivery package

The Phase/Packet Master Thread should respond to a finished Delivery Thread
report with one of these outcomes:

1. `continue in same Delivery Thread`
2. `fix in same Delivery Thread`
3. `accepted and commit-ready`
4. `escalate to Super Master Thread`

## Relationship to commit policy

Thread boundaries and commit boundaries are related but not identical.

Important rule:

- do not create a new thread just because a new commit is appropriate

One Delivery Thread may produce:

- one commit,
- several closely related commits,
- or one commit plus one narrow follow-up fix commit.

Commit ownership rules live in `docs/internal/commit_policy.md`.

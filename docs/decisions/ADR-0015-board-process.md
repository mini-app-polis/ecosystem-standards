# ADR-0015: The Board Process — A Checked Review, a Complete Column, Work On Hold and Moves by Comment

**Date:** 2026-11-04
**Status:** Accepted
**Repo:** ecosystem-standards
**Supersedes, in part:** ADR-0014 — its Landing and Closing out Review rules

---

## Context

ADR-0014 made Review hold work that was handed off and work that had landed,
closed by a `Landed:` comment that the sweep trusts. Three problems remained.

- **Review means two things.** A finished task stays in Review once it is
  marked complete, so the column mixes work waiting to be checked with work
  that is done, and a task is closed on a merge alone, whether or not it did
  what its Done when asked.
- **Sessions do not move tasks.** Working sessions comment on tasks but often
  leave them where they were, so the board falls behind the work, and no
  written rule says which actor owns each move.
- **Nowhere to park a task.** There is no column the automation leaves alone,
  so a task cannot be set aside without being swept, refined or dispatched.

Two further changes landed in the same review of the process. Grooming is
renamed refining, so the code and the board's Refining column use one word.
Detected problems (failed CI on `main`, cog run reports at ERROR, API 5xx
bursts, conformance findings) proved too noisy as board tasks: they belong
in the repository they are about.

The board stays on Asana's free tier: no custom fields, rules or
dependencies. A task's state is carried by its column and its comments.

---

## Decision

**Review holds work someone says is finished. A mechanical check decides
whether it is: work that passes moves to Complete and only then is marked
complete. Sessions move tasks by comment, one writer applies every move, and
an On Hold column is the owner's alone.**

### Columns

| Column | Holds |
|---|---|
| Inbox | New tasks, not yet refined |
| Refining | Tasks being refined, or waiting on the owner's answers |
| Ready | Tasks that meet the definition of ready |
| In progress | Tasks someone has started |
| Blocked | Tasks waiting only on other tasks or a date |
| On Hold | Tasks the owner has parked; nothing automatic reads or moves them |
| Review | Work someone says is finished, waiting for the Review check |
| Complete | Work that passed the Review check, marked complete |

### One writer per move

The task manager is the only writer to the board. Every move belongs to one
actor:

| Move | Owner |
|---|---|
| New to Refining | the sweep |
| Refining to Ready | the refiner's result, applied by the sweep |
| Ready to In progress | agent dispatch, or a `Started:` comment |
| In progress to Review | a `Handed off:` comment |
| Review to Complete, In progress or Refining | the Review check |
| Blocked to Ready | the sweep, once the blockers are done |
| Into or out of On Hold | the owner only |

### Moves by comment

A session never moves a task itself. It posts a comment, and the next sweep
makes the move:

- `Started:` moves a task from Ready to In progress.
- `Handed off:` moves a task from In progress to Review. It answers every
  item of the task's Done when, point by point, with what was done and where.
  When there is no pull request, each answer carries evidence instead: a
  link, a commit, a run id, or a plain statement from the owner.
- `Refining questions:` holds a task in Refining until a later comment
  answers it. The old `Grooming questions:` prefix is accepted beside it.

### The Review check

The sweep checks each task in Review mechanically, with no model call:

- its pull request, when it has one, is merged and CI on `dev` is green;
- its latest `Handed off:` comment answers every Done when item.

A task that passes moves to Complete and is then marked complete. A task that
fails gets one `Rejected:` comment naming each item not answered and moves to
In progress. A mechanical check cannot tell unfinished work from an unclear
task, so a person moves a rejected task to Refining when the task itself is
the problem. A task marked complete by hand in Review goes through the same
check, and one that fails is reopened. `Landed:` stays as the record that an
agent's pull request merged with green CI on `dev`; it no longer closes a
task on its own.

### On Hold

On Hold is parked work. The sweep never reads, refines, dispatches from, checks
or moves a task there. Only the owner moves a task in or out.

### Manual edits

Anyone may edit a task by hand. The next run polishes the edit rather than
starting over: a person's edit after refining questions counts as an answer,
an edited task that meets the definition of ready moves on without a paid
refining run, and refining keeps the person's content, decisions and
executor, filling in only what is missing.

### Refining

Grooming is renamed refining throughout: the refiner service, its settings,
the sweep's flag, the API's routes, scopes and tables, and the questions
prefix. Old names are accepted as aliases until every repository has moved,
so no two repositories have to deploy together.

### Detected problems are GitHub Issues

Failed CI on `main`, cog run reports at ERROR or worse, bursts of API 5xx
answers and conformance findings at WARN or worse open a GitHub Issue in the
affected repository: one open Issue per streak, updated while the streak
lasts and closed when it clears. Evaluator status rows (a repository not
evaluated, a model check not run) open an Issue in evaluator-cog. Nothing
reaches the board automatically; the owner files a task from an Issue by
hand. Secret-rotation tasks are not detected problems: they are scheduled
work for the owner, and they stay on the board.

---

## Consequences

**Positive**

- Complete means checked: a task is marked complete only after its own Done
  when has been answered and its pull request has landed.
- Review holds only work waiting to be checked, so it stays short.
- The board keeps one writer, and every move has a named owner, so a task
  out of place points at the actor that should have moved it.
- On Hold gives the owner a place to set work aside without fighting the
  automation.
- The board carries planned work; repositories carry their own problems.

**Negative / trade-offs**

- Comment-driven moves lag by up to one sweep.
- The check is mechanical. It confirms that every Done when item is answered,
  not that the answer is right; that judgement is still the reviewer's.
- Prefixes are plain text. A comment that starts with one by accident is read
  as one, and a misspelled one is not.
- Signals in GitHub Issues are one more place to look.

---

## Alternatives Considered

**A model reviews the work in Review.** It could judge quality, but every
check would cost a paid call. The mechanical check plus the point-by-point
`Handed off:` comment catches missing work at no cost.

**Rejected work goes to Blocked.** Blocked means waiting on another task or a
date, and the sweep frees a task when its blockers finish. A rejected task
has no blocker to finish, so it would never move.

**Sessions move tasks directly.** Faster, but a second writer to the board,
and it depends on every session remembering.

**A `hold` tag instead of an On Hold column.** The task would keep its place, but
a tag is easy to miss on the board, and a working session cannot set tags.

**Detected problems as board tasks, promoted from Issues.** Every problem
would reach the board and the noise would return. The owner promotes the few
that warrant planned work.

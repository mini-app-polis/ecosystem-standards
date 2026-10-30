# ADR-0014: Review Holds Handed-Off Work Until a `Landed:` Comment Closes It

**Date:** 2026-10-30
**Status:** Accepted
**Repo:** ecosystem-standards

---

## Context

Work across the fleet is tracked on one Asana task board, kept by
task-manager-cog (task-manager-cog ADR-0001). Three executors finish
tasks: an agent run, which opens a draft pull request into `dev`; a Claude
session working with the owner, which leaves changes in his checkouts or
commits them; and the owner himself. Each moved its task to Review, and a
task left Review only when a person confirmed the change in dev and
completed it by hand.

So Review mixed work handed off and not yet merged with work already on
dev, and nothing on a task said which, or what had been checked. Tasks sat
in Review after their work landed, and a session closing out the column had
no shared test for done.

The board is on Asana's free tier: no custom fields and no rules. A task's
state can be carried only by its column and its comments.

---

## Decision

**Review holds work handed off and work done. A task enters Review with a
`Handed off:` comment and is closed by a `Landed:` comment, which
task-manager-cog's sweep acts on.**

- **Handing off.** Moving a task to Review comes with a comment starting
  `Handed off:` that says what changed, the repository and files, the
  commit message, and whether it is committed yet.
- **Landing.** A task is closed by a comment starting `Landed:` that names
  the repository, branch, commit and CI result, posted by whoever confirms
  green CI on dev: an agent run, a Claude session or the owner.
  task-manager-cog's sweep marks it complete. A later comment reopens it:
  the sweep closes a task only while `Landed:` is its latest comment.
- **Closing out Review.** A session closing out Review checks each
  incomplete task against its own Done when on dev: the change present, CI
  green, and the release out if the task needs one.
  - Landed: it posts `Landed:`.
  - Not landed: it moves the task back to In progress with a comment
    saying what is missing.
  - Can't tell: it comments what could not be confirmed and moves the task
    to Ready as a `cowork` task.
- **Matching work to a task.** Work is matched to its task by the task's
  Where and Done when, not by task ids in commit messages. Board ids stay
  out of code as well (DOC-016).
- **Comments and columns only.** The process uses no custom fields and no
  Asana rules.

The agent workflow follows the same rule: the comment that lands its
result on the task when it opens its pull request starts `Handed off:`.

---

## Consequences

**Positive**

- A task in Review says, in its own comments, what was handed off and
  whether it has landed. Review no longer waits on a person to complete
  each task by hand.
- Closing is one rule for every executor. task-manager-cog reads comments
  and columns only, so closing needs no GitHub access or model.
- A session closing out Review has a fixed test, the task's Done when, and
  a fixed outcome for each result, including the one where it cannot tell.

**Negative / trade-offs**

- `Landed:` is a claim, not a check: the sweep trusts whoever posts it. The
  check is the poster's, against the task's Done when.
- The prefixes are plain text. A comment that starts with them by accident
  is read as one, and one that misspells them is not.
- Matching by Where and Done when takes judgement where an id in a commit
  message would not.

---

## Alternatives Considered

**A custom field or Asana rule for landed.** Not available on the free
tier, and a field would carry no evidence of what was checked.

**Task ids in commit messages.** Would match work to tasks mechanically,
but puts a private tracker's ids into every repository's history, which
DOC-016 already keeps out of code.

**The sweep checks CI itself.** It would need GitHub access per
repository and a mapping from task to commit that the board does not hold.
Whoever confirms green CI already has both.

**A person completes every task.** The process this replaces: Review
filled with work that had already landed.

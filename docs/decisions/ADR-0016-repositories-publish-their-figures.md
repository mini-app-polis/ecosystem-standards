# ADR-0016: Each Repository Publishes the Figures It Owns

**Date:** 2026-11-04
**Status:** Accepted
**Repo:** ecosystem-standards

---

## Context

Figures about the fleet (how many services run where, how many rules the
standards hold, how many secrets are under rotation) get quoted outside the
repositories that hold the data: on a resume, a site, a report. Until now
each of those was counted by hand in a working session, from whatever file
was nearest. The nearest file is often a stale one. The committed
`catalog.json` said 180 rules a month after the sources had grown to 185.

A figure counted by its reader drifts the moment the data moves, and nothing
says it has.

---

## Decision

**The repository that owns the data computes and publishes each figure in a
generated `facts.json`, checked in CI. Readers point at it; nobody recounts.**

- **Declared in the repository.** `facts.yaml` names each figure and how it
  is computed from the repository's own files: a count of entries in a YAML
  or JSON file (optionally filtered or grouped), a count of files, a value
  read from a file, or a count of matches in a file.
- **Generated, never edited.** `facts generate` (miniapppolis-common-utils)
  writes `facts.json`, which follows `schemas/facts.schema.json`: per fact a
  value, a description, the source it was computed from, and the day the
  value last changed.
- **Checked in CI.** `facts check` fails when the committed `facts.json` no
  longer matches what `facts.yaml` computes, so a published figure cannot go
  stale or be edited by hand.
- **Owned once.** A figure is computed only by the repository that owns its
  data. No other repository counts it.
- **Static figures only.** A figure measured at runtime (a restore drill's
  RPO and RTO) is out of scope; it is not computed from a repository's files.
- **Pointed at, not copied.** A reader keeps a map from each figure it uses to
  the repository, file and key that publishes it, and uses no figure outside
  that map.

Whether every repository must publish facts is left open: the rule here is
how a repository that owns quotable figures publishes them, not that each
must.

---

## Consequences

**Positive**

- A quoted figure has one home and a date, and CI keeps it true.
- Counting moves from sessions into code, once per figure.
- Drift in the underlying data shows up as a failing check, not as a wrong
  number somewhere else.

**Negative / trade-offs**

- A change to the data needs `facts generate` in the same commit, or CI fails.
- The four computation kinds cover counting and reading; a figure that needs
  more needs a new kind in the shared generator.

---

## Alternatives Considered

**An API endpoint serving figures.** Always current, and it would cover
runtime figures, but every reader would need a network call, and the figures
would have no history in git.

**Readers recount from the source files.** What happened before: every reader
reimplements the count and none of them notices drift.

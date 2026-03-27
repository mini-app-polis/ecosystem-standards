# Backlog

Open items worth revisiting. These are not standards yet — they are things
that need to be built, decided, or documented when the time is right.

---

## evaluators/ — agent scripts not yet built

The `evaluators/` folder exists as a placeholder. The intention is that
agent scripts implementing the `check_notes` from each rule live here.
When the evaluator is ready to be built, this is where it lands.

Priority: build the first evaluator script once the capture endpoint
(separate repo) is live and the feedback loop is established.

---

## CONTRIBUTING.md — how to add a new standard

The README explains the rule format but not the ritual for adding one.
A short CONTRIBUTING.md or README section should document:

  1. Hit an issue in the ecosystem
  2. Open this repo
  3. Add or update a rule in the relevant standards/*.yaml file
  4. Set status: idea if unvalidated, requirement if the issue proved it necessary
  5. Commit with a message explaining the issue that drove it
  6. Bump version in index.yaml and add a changelog entry

The git history is the audit trail. The origin field on each rule is the
permanent record of why it exists.

---

## Capture endpoint — backlog items not yet auto-routed here

The planned capture system (POST /capture on kaiano-api → GitHub Issue
in this repo) is not yet built. Until it is, new issues must be manually
added to this file or directly as GitHub Issues.

Once built, mid-flow captures will automatically land as labeled Issues
in this repo for processing into standards when there is headspace.

Reference: capture system design is in a separate conversation.

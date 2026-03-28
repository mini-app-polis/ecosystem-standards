# Backlog

Open items worth revisiting. These are not standards yet — they are things
that need to be built, decided, or documented when the time is right.

---

## playbooks/ — bootstrap guides for new repos

The python-project-template is retired. Its replacement is a set of
playbooks in playbooks/ — one per artifact type. Each playbook
documents the exact steps to go from empty repo to first green CI.

Artifact types needing playbooks:
  - ✅ new-cog.md (Python worker service) — complete
  - new-fastapi-service.md
  - new-astro-site.md
  - new-react-app.md
  - new-hono-service.md

Priority: new-cog.md first — it is referenced by the new_cog DoD
checklist and watcher-cog was the first cog built without it.

---

## evaluators/ — agent scripts not yet built

The `evaluators/` folder exists as a placeholder. Agent scripts implementing
the check_notes from each rule live here.

First candidate: a DoD evaluator that reads `definitions-of-done.yaml`,
determines the artifact type being evaluated, and runs the appropriate
checklist post-PR or post-deploy.

Priority: build once the capture endpoint is live and the feedback loop
is established.

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

The planned capture system (POST /capture on api-kaianolevine-com → GitHub Issue
in this repo) is not yet built. Until it is, new issues must be manually
added to this file or directly as GitHub Issues.

Once built, mid-flow captures will automatically land as labeled Issues
in this repo for processing into standards when there is headspace.

Reference: capture system design is in a separate conversation.

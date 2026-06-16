## Heartbeat: Structured Experiment Knowledge

Pause your current work and update the structured experiment knowledge bundle at
`{shared_dir}/notes/structured/`. This is a global team memory surface: it should
help every agent decide whether to stay with an idea, branch from it, or abandon
it.

The structured bundle uses an OKF-style Markdown format: ordinary Markdown files
with YAML frontmatter, directory structure, and links. Do not create a separate
JSON or YAML graph manifest. The Markdown files are the source of truth.

### Required bundle shape

Maintain these paths when relevant:

```text
notes/structured/
  index.md
  log.md
  experiments/<commit>.md
  ideas/<slug>.md
  directions/<parent>--<child>.md
```

Use short, stable filenames. Commit hashes may be shortened when unambiguous.

### Concept frontmatter

Every concept file under `experiments/`, `ideas/`, and `directions/` must start
with YAML frontmatter:

```yaml
---
type: Experiment
title: Short human-readable title
description: One sentence summary.
status: active
confidence: low
created: 2026-06-16T00:00:00Z
updated: 2026-06-16T00:00:00Z
evidence:
  - attempts/<commit>.json
---
```

Allowed `type` values:
- `Experiment`
- `Idea`
- `Direction`

Allowed `status` values:
- `active`
- `branched`
- `confirmed`
- `weakened`
- `abandoned`
- `superseded`

Allowed `confidence` values:
- `low`
- `medium`
- `high`

Preserve existing unknown frontmatter keys when editing a concept.

### Step 1: Read evidence

Read recent attempts and the current knowledge base:

- Run `coral log -n 10 --recent` and inspect recent attempt hashes, scores,
  titles, parent hashes, and feedback.
- Read raw experiment notes in `{shared_dir}/notes/experiments/`.
- Read synthesis/open-question notes if they exist.
- Read all existing files under `{shared_dir}/notes/structured/`.

Prefer real-mode attempts over tune-mode attempts when deciding confidence.
Treat one-shot score deltas near the task's observed noise floor as low
confidence unless repeated evidence supports them.

### Step 2: Create or update experiment nodes

For each recent evaluated commit that is not represented yet, create
`experiments/<commit>.md`.

Each experiment node should include:
- Commit hash and parent hash when known.
- Score, status, title, and brief feedback summary.
- What changed.
- Which idea or direction it belongs to.
- Links to parent and child experiments when known.
- Confidence in what this experiment proves.

Do not overclaim. A regression is evidence about the transition and conditions,
not proof that the whole idea is dead.

### Step 3: Create or update direction nodes

For meaningful transitions such as `A -> B` or `B -> C`, create or update
`directions/<parent>--<child>.md`.

Each direction node should answer:
- What hypothesis motivated the transition?
- Did the child strengthen or weaken the parent idea?
- Was the score change large enough to trust?
- Should the team Stay, Branch, or Abandon from this direction?
- What follow-up would most reduce uncertainty?

Use links to the experiment nodes instead of copying long details.

### Step 4: Propagate findings backward

Later results can change confidence in earlier nodes. If C changes the
interpretation of B or A, update the relevant parent experiment, idea, or
direction:

- Downgrade confidence when a child contradicts the parent's rationale.
- Upgrade confidence when independent children support the same mechanism.
- Mark a direction `branched` when evidence supports a related but different
  hypothesis.
- Mark a direction `abandoned` only when repeated real-mode evidence rules it
  out under clear conditions.

Example: if a comment-only child changes score but reruns reverse the ordering,
the correct propagated finding is "wall-clock stochastic search is noisy", not
"bytecode layout uniquely determines the score".

### Step 5: Maintain the decision surface

Always update `{shared_dir}/notes/structured/index.md`. It is the part agents
should read before planning their next experiment.

It must contain:

```markdown
# Structured Experiment Knowledge

## Current Guidance

### Stay
- ...

### Branch
- ...

### Abandon
- ...

## Top Unresolved Uncertainties
- ...

## Claims Whose Confidence Changed
- ...

## Recent Experiment Lineage
- [A](experiments/A.md) -> [B](experiments/B.md) -> [C](experiments/C.md)
```

Keep Current Guidance short and actionable. Link to deeper experiment, idea,
and direction files for details.

### Step 6: Update the log

Append a brief dated entry to `{shared_dir}/notes/structured/log.md` describing
what changed in the structured bundle and why.

After updating structured knowledge, resume optimizing.

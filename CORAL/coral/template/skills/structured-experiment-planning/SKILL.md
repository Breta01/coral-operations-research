---
name: structured-experiment-planning
description: Use this skill when notes/structured/index.md exists and you are choosing the next experiment, especially after a reflect, pivot, or structure heartbeat. It teaches agents to consume structured Stay / Branch / Abandon guidance, select a direction, and commit to a concrete 3-eval branch instead of drifting into incremental tweaks.
---

# Structured Experiment Planning

Use this skill to turn `notes/structured/index.md` into the next experiment.
The structured index is a decision surface, not an archive: it should change
what you try next.

## When to Use

Use this skill whenever:

- `notes/structured/index.md` exists and you are planning the next eval.
- A heartbeat asks you to reflect, pivot, or update structured knowledge.
- Recent attempts are clustered around the same score and you need to decide
  whether to stay, branch, or abandon a direction.
- You are about to submit an incremental tweak to the current best approach.

Do not use this skill for ordinary note cleanup or broad literature review.

## Inputs to Read

Read these in order:

1. `notes/structured/index.md`
2. Any experiment, idea, or direction files linked from Current Guidance
3. Your recent attempts with `coral log --agent <agent_id> -n 5 --recent`
4. Team leaderboard with `coral log -n 10`
5. Relevant raw notes only if the structured files leave a concrete ambiguity

The index should be treated as guidance, not law. You may disagree with it, but
only if you can name the evidence that changes the decision.

## Decision Procedure

### 1. Classify the next move

Choose exactly one:

- **Stay**: Continue the current direction because recent evidence supports it
  and the next eval tests a specific uncertainty inside that direction.
- **Branch**: Start a related but distinct direction because the current line is
  plateauing or evidence points to a new mechanism.
- **Abandon**: Stop spending evals on a direction because repeated evidence or a
  large trusted regression makes it low-value.

Avoid "soft stay" behavior: tiny parameter tweaks after a plateau are usually
unlabeled Stay decisions. If you cannot explain what uncertainty the tweak
tests, choose Branch instead.

### 2. Calibrate confidence

Before trusting a conclusion, check the evidence strength:

- One-shot delta near the task noise floor: low confidence.
- Repeated same-direction results or a large delta: medium/high confidence.
- Tune-mode result without real-mode confirmation: low confidence.
- Regression from a slower implementation: evidence about speed/overhead, not
  necessarily evidence against the algorithmic idea.

If confidence is low, plan an eval that reduces uncertainty rather than one that
optimizes around the apparent result.

### 3. If Branch, commit to 3 evals

A branch is not a dabble. Write the next three eval intentions before coding:

```markdown
Branch: <short name>
Base commit: <hash>
Hypothesis: <what mechanism should improve score>
Eval 1: <minimal correct implementation / smoke test>
Eval 2: <fix or strengthen the mechanism>
Eval 3: <tune or combine once correctness is established>
Abandon if: <specific failure pattern or score evidence>
```

Use commit/eval messages like:

- `structural branch 1/3: <name> - <change>`
- `structural branch 2/3: <name> - <change>`
- `structural branch 3/3: <name> - <change>`

Do not abandon after eval 1 unless it is clearly invalid, impossible, or
dominated by a simpler implementation.

### 4. If Stay, make the uncertainty explicit

Write:

```markdown
Stay direction: <linked direction or idea>
Why stay: <evidence from structured index>
Uncertainty being tested: <one sentence>
Expected result: <score/mechanism prediction>
Stop condition: <what would move this to Branch or Abandon>
```

If the uncertainty is just "maybe this parameter is better", and the run is
already plateaued, this is probably not a good Stay.

### 5. If Abandon, preserve the lesson

Before abandoning, ensure the structured index or a direction file says:

- What was tried
- Why it failed or stopped being worth the budget
- What evidence would reopen it

Abandoning is useful only if future agents can avoid repeating the same path.

## Output in Your Reflection or Focus Note

When this skill influences your plan, include this compact block in your note:

```markdown
## Structured Planning Decision

- Decision: Stay | Branch | Abandon
- Structured source: `notes/structured/index.md` and <linked files>
- Confidence: low | medium | high
- Base commit: <hash>
- Next eval: <specific change>
- If Branch, 3-eval plan: <eval 1>; <eval 2>; <eval 3>
- Evidence that would change my mind: <specific condition>
```

Then continue with implementation.

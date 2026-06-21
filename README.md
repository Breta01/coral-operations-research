# CORAL for Operations Research

I use [CORAL](https://github.com/Human-Agent-Society/CORAL) as the base system and apply it to a 3D bin-packing optimization task.

The assessment brief asks for six parts:

1. Replicate one CORAL example task.
2. Apply CORAL to a classic OR problem.
3. Run ablations on knowledge accumulation and heartbeats.
4. Improve CORAL's knowledge and memory mechanism.
5. Propose a product plan for enterprise optimization.
6. Add any extra observations.

## Installation

I install CORAL as an editable package in a local virtual environment. This lets me modify CORAL and test those changes directly.

```bash
uv venv --python 3.13 .venv
uv pip install --python .venv/bin/python -e ./CORAL
```

## 1. Task - Replicate Results

I first ran CORAL on the repository example task `drug_design`.

```bash
coral start -c example_task/drug_design/task.yaml
```

I used the Cursor runtime with the `claude-opus-4-6` model.

### Result

| Source | Task | Final score | Evals | Notes |
|---|---|---:|---:|---|
| My run | `drug_design` | 1.0000 | 41 | Full score on the local grader. |

The run showed that the local CORAL setup worked end to end. I also found that the agent could exploit the grader. I made a small grader-side fix so later results were based on valid behavior rather than a scoring loophole.

## 2. Task - OR Problem Application

I chose the 3D bin-packing problem. The goal is to fit as many boxes as possible into larger containers. Each item has length, width, height, value, and quantity. Rotations are allowed.

This is a classic OR problem with direct logistics applications, such as shipping container loading and warehouse packing.

The task is implemented in [`bin_packing`](./bin_packing/).

### Files

| File | Purpose |
|---|---|
| `bin_packing/grader/src/bin_packing_grader/grader.py` | Validates placements and computes the score. |
| `bin_packing/seed/solution.py` | Provides the initial heuristic solution. |
| `bin_packing/task.yaml` | Configures the CORAL task. |
| `bin_packing/seed/data/public_instances.json` | Public instances visible to the agent. |

### Data

The instance format is inspired by existing 3D bin-packing datasets:

- <https://github.com/dwave-examples/3d-bin-packing>
- <https://data.mendeley.com/datasets/9ts4rvkc5s/1>

The grader uses 5 public instances and 20 private instances. Public feedback is detailed. Private feedback is aggregated.

### Scoring

The grader checks that each placement:

- stays inside the selected bin,
- uses an available item type and quantity,
- uses a valid rotation,
- does not overlap an accepted placement in the same bin.

The score is the average across all 25 instances:

```text
0.5 * packed_volume_ratio + 0.5 * packed_value_ratio
```

To make the problem more complicated, agent needs to find solution which is able to solve the 25 instances under 60 seconds.

### Result

| Solver | Final score | Improvement vs seed |
|---|---:|---:|
| Seed solution | 0.4879 | - |
| py3dbp (off-the-shelf) | 0.699964 | +43.45% |
| Best CORAL run | 0.749783 | +53.66% |
| Upper bound (provable) | 0.792455 | +62.41% |

CORAL improved the naive seed. The best run came from the `no_heartbeats` ablation, which suggests that this task is noisy and that short-run comparisons need repeated runs.

The last two rows bound the problem. `py3dbp` is an off-the-shelf 3D packer (value-density ordering, no time limit) and is the achievable floor that any solver should clear. The `Upper bound` is a provable ceiling: a per-instance bounded knapsack (HiGHS) that keeps only the volume-capacity and quantity constraints and drops all geometry, so no feasible packing can exceed it. The public instances are provably optimal at 1.0 (exact 3D MIP for problem_1/4/5; py3dbp meets the ceiling on problem_2/3), so the entire remaining gap lives in the 20 oversubscribed private instances, where the optimum is bracketed in [0.625, 0.741]. CORAL's 0.749783 therefore captures ~86% of the headroom available above the seed.

## 3. Task - Ablation Study

I evaluated three conditions on the same bin-packing task:

- Full CORAL.
- No knowledge accumulation.
- No heartbeats.

Each condition was run up to 3 times with a target budget of 100 evaluations.

```bash
./scripts/run_ablation.sh
```

### Conditions

For `task.no_knowledge.yaml`, I disabled the knowledge features:

```yaml
knowledge: false
sharing:
  notes: false
  skills: false
```
_Note: I added the `knowledge` setting to completely disable knowledge storage._

For `task.no_heartbeats.yaml`, I set all heartbeat intervals to a very large number:

```yaml
heartbeat:
  - name: reflect
    every: 1000000000
```

This keeps the config shape valid while making the heartbeats effectively unreachable during the evaluation budget.

### Results

The table below uses the final score from each run.

| Condition | Run scores | Mean +/- std |
|---|---:|---:|
| Full CORAL | 0.745681, 0.734481, 0.737544 | 0.739235 +/- 0.005789 |
| No knowledge | 0.743374, 0.724557, 0.717578 | 0.728503 +/- 0.013343 |
| No heartbeats | 0.749783, 0.740116, 0.738883 | 0.742927 +/- 0.005969 |

### Observation

The differences are small relative to the noise of this benchmark. The `no_heartbeats` condition had the best mean score. The `no_knowledge` condition had the lowest mean and highest variance.

My interpretation is that the default memory and heartbeat system was not always helping this OR task. The agents often wrote many detailed notes, and those notes did not always guide the next useful experiment. Additionally, `no_heartbeats` does not restart sessions, so the agent keeps expanding the same session context across multiple evaluations instead of starting a new session each time.

## 4. Task - Improve CORAL

### Failure Mode

I observed several issues in the current notes and skills system:

- Agents wrote notes saying no further improvement was possible, even when later attempts did improve.
- Heartbeat sessions added new context and notes repeatedly, which increased overhead.
- Most experiments were stored as flat files in `notes/experiments`, making it harder to see which ideas depended on earlier ideas.
- Fine-tuning attempts created many similar notes, which made the useful signal harder to retrieve.

The supporting evidence is collected in [`evidence/coral-memory-failure-evidence.md`](./evidence/coral-memory-failure-evidence.md). It uses only the recent `full`, `no_knowledge`, and `no_heartbeats` runs under `results/`.

### Proposed Solution

I implemented structured experiment memory. The main idea is to track experiments as a tree instead of a flat list.

For example:

```text
A: apply MIP
  -> B: split into subproblems
      -> C: tune parameters of B
```

If `C` fails, the agent should update not only `C`, but also the parent idea `B` and the original direction `A`. This helps later agents decide whether to stay on a branch, start a new branch, or abandon the branch. This also simplifies aggregation as agent can aggregate whole branch (at any level) into a single node.

### Implementation

I added a structured memory path using CORAL's existing heartbeat and skill mechanisms:

- `CORAL/coral/workspace/project.py` initializes `notes/structured/` when the task uses the `structure` heartbeat.
- `CORAL/coral/hub/prompts/structure.md` tells the heartbeat how to maintain experiment nodes, direction nodes, active branches, fine-tuning summaries, and compressed abandoned branches.
- `CORAL/coral/template/skills/structured-experiment-planning/SKILL.md` tells agents to read the structured index before choosing the next experiment.
- `bin_packing/task.structured.yaml` enables the `structure` heartbeat for the bin-packing task.
- `CORAL/tests/test_workspace.py` checks that the structured index is created with the expected sections.

This is a code-level change to CORAL, not only a prompt or hyperparameter change.

### Comparative Result

| Condition | Run scores | Mean +/- std |
|---|---:|---:|
| Vanilla full CORAL | 0.745681, 0.734481, 0.737544 | 0.739235 +/- 0.005789 |
| Structured memory | 0.744003, 0.745066, 0.732386 | 0.740485 +/- 0.007035 |

The structured-memory version was slightly better in mean score, but it also had higher variance than full CORAL. The result is not large enough to claim a decisive win, but it is a useful sign that explicit experiment structure can reduce memory noise.

## 5. Task - Product Plan

This is my architecture plan for an LLM-driven autonomous optimization tool for enterprise OR problems.

### 1. System Architecture

I would build the system around these modules:

- Problem intake: imports customer data, validates schemas, and identifies the problem type and objective.
- Solver workspace: creates an isolated repository for each optimization project.
- Evaluator service: runs deterministic scoring, constraint checks, and simulation tests.
- Agent runner: runs CORAL agents in isolated branches or worktrees.
- Knowledge service: stores attempts, notes, skills, datasets, and reusable solver patterns.
- Human review UI: lets users compare candidate solutions, give feedback, and approve deployment.
- Deployment API: exports final schedules, routes, or packing plans back to the customer's systems.

The data flow is:

```text
Customer data -> Problem model -> Evaluator -> Agent runs -> Candidate solutions -> Human review -> Deployment
```

### 2. Knowledge Accumulation Mechanism

I would separate general knowledge from enterprise-specific knowledge.

General knowledge:

- Standard problem types
- Common formulations
- Baseline heuristics
- Solver templates
- Public benchmark lessons
- Reusable evaluation patterns

_These would be part of the solver knowledge base, which can expand over time and act as a source of ideas and templates._

Enterprise-specific knowledge:

- Customer constraints
- Historical solving attempts
- Rejected solutions
- Domain-specific tradeoffs
- User feedback
- Final approved solutions

Structured experiment memory should be stored in a database, but exposed to agents as a file-like tree. For knowledge storage I would follow [Open Knowledge Format](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing). There should be agent mechanism which reviews the enterprise specific knowledge and proposes updates to the general knowledge base (e.g., if major improving strategy is found). These updates should contain only general ideas, heuristics, and approachase. This keeps the agent workflow simple while allowing indexing, retrieval, pruning, and audit trails.

### 3. Multi-Enterprise Isolation Strategy

Each enterprise customer should have isolated:

- Raw data
- Solver repositories
- Evaluation logs and notes
- User feedback
- Generated candidate solutions

Evaluation logs and notes can be stored in database similar to general knowledge base (providing file-like interface). The solver repository should be stored as `git` repository with current solution and commits (as it is done right now when you run coral task). There should be authorization mechanism which ensures that enterprise specifc auth key has only read access to general knowledge and read/write access to the evaluation logs and notes.

I imagine that each task CORAL task will be instantiate as isolated docker which will have necessary authenticatin keys for access to both general and enterprise specific knowledge base, and acess to solution repository. We could also implement mechanism for forking enterprise database before each run and updating the main enterprise database only if significant progress is made (preventing any unwanted loss of data).

Updateing general knowledge base should be separate mechanism from CORAL task and should be carefuly reviewed to prevent leakage of any sensitive data.

### 4. Fuzzy User Feedback Driving Self-Evolution

Enterprise users often give feedback like "drivers are too tired" or "this schedule does not work." I would consider following approaches to handling this feedback:

- Translate feedback into candidate constraints or objectives.
- Ask the user to confirm the interpretation when needed.
- Allow for dynamic change of objective/scoring and have mechanism to re-evaluate past solutions.
- Provide user with multiple candidate solutions and let user rank them (users might find this easier than explaining the objective exactly)

Overall, I would imagine that for some problem we keep multiple objetives/graders and keep the best candidate for each of them. Based on the user feedback (as described above), we can infer underlaying objetive function and refine the grader.


### 5. Foreseeable Failure Modes

| Failure mode | Mitigation |
|---|---|
| Agents get stuck in local optima | Run multiple branches, require explicit pivot criteria, and keep strong baselines. |
| Knowledge base fills with weak or repeated notes | Use structured memory, compression, confidence scores, and pruning. |
| Agent deletes important notes or code | Keep active and backup database and update only after successful run of CORAL. | 
| Agents overfit to noisy evaluator results (e.g., when grader is non-deterministic) | Use repeated evaluations, confidence intervals, and deterministic baselines. |
| User feedback is ambiguous | Convert feedback into candidate constraints and ask for confirmation. |
| Tenant data leaks into shared memory | Enforce tenant isolation, sanitize general knowledge base, and audit every promotion to global memory. |
| Solver returns infeasible plans | Keep a deterministic constraint validator outside the agent loop. |
| Runtime cost grows too high | Use budgets, caching, warm starts, and early stopping. |

## 6. Task - Additional Notes

One important efficiency issue I noticed is that CORAL starts fresh agent sessions basically every evaluation (unless heartbeats are turned off). This turns out to be very expensive because it does not fully reuse prior context or cache. For longer OR runs, I would focus on:

- Reducing session restart overhead and caching evaluator setup
- Trying to separate implementation agents and planning agents

The bin-packing experiments also showed that one-shot scores can be misleading when the solver uses randomized search. Due to usage of wall-clock time for timeouts, scores can than sligtly differe for single solution. For serious comparisons, I would report repeated runs and use mean, median, and variance instead of relying on a single best attempt.


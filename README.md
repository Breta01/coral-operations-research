# CORAL for OR
Autonomous AI research for Operatins Research problem. Based on CORAL repository: <https://github.com/Human-Agent-Society/CORAL>.

## Installation
We install [CORAL](https://github.com/Human-Agent-Society/CORAL) as editable package in local venv. This allows us to make changes and quickly test them.

```bash
uv venv --python 3.13 .venv
uv pip install --python .venv/bin/python -e ./CORAL
```


## 1. Task - Replicate Results
First, we test CORAL on the example task from repository itself. `drug_design` task for picked to reproduce the experiment.
```bash
coral start -c example_task/drug_design/task.yaml
```

For running the agent I use `cursor` runtime with `claude-opus-4-6` model.

### Notes
- Found agent solution exploing the grader and made a slight changes to graded file

## 2. Task - OR Problem Application

I picked 3D bin packing problem where we want to fit as many boxes (defined by width, lenght, depth) into larger containers. This is classic OR problem which appears for example during packing shipping containers.

The task is implemented in the [`bin_packing`](./bin_packing/) folder.

### 3D Bin Packing Problem Data
Data format is insipired by existing dataset on 3D bin packing:
- https://github.com/dwave-examples/3d-bin-packing
- https://data.mendeley.com/datasets/9ts4rvkc5s/1

Grader used 20 test problems for evaluation plus additional 5 problems are available for the agent to use and test on.

## 3. Task - Ablation Study

We defined aditional task files `task.no_heartbeats.yaml` and `task.no_knowledge.yaml` are implemented.

### `task.no_heartbeats.yaml`
We implement this by setting hearbeat `every` to very large number:
```yaml
heartbeat:
  - ...
    every: 1000000000      # Run every 1000000000 evals
```

This effectively make the heartbeats never evaluate


### `task.no_knowledge.yaml`

Originally, I tried to implement this using task settings:

```yaml
sharing:
  notes: false
  skills: false
```

However, this still results in agent creating notes. That's why I end up making custom changes to the CORAL package.


# Evidence of CORAL Memory Failure Modes

This note uses only the recent ablation runs under `results/` for these three scenarios:

- `results/bin-packing.full`
- `results/bin-packing.no_knowledge`
- `results/bin-packing.no_heartbeats`

It does not use old runs or any other scenario.

## 1. Some notes used final-sounding language while the run still had headroom

Evidence source:
`evidence/post-ep-saturation-plateau.md`

Original source:
`results/bin-packing.full/2/.coral/public/notes/_synthesis/post-ep-saturation-plateau.md`

Relevant facts:

- The note is titled `Synthesis: Post-EP Saturation Plateau`.
- It says post-selection tuning gives "zero gain" after EP repair and gap-fill.
- It says confidence is high that "post-EP post-selection is exhausted".
- It still lists several areas with headroom, such as MIP slack tuning and item-selection MIP.

The same recent run later recorded several improved attempts:

| Attempt | Score |
|---|---:|
| `06273309` | 0.725421 |
| `ba4fa167` | 0.728536 |
| `38ed334d` | 0.729398 |
| `527692c2` | 0.732207 |
| `74f3d5c5` | 0.733527 |
| `ea4e620a` | 0.734481 |

Additional evidence:
`evidence/725-ceiling-pipeline.md`

Original source:
`results/bin-packing.full/2/.coral/public/notes/_synthesis/725-ceiling-pipeline.md`

Relevant facts:

- The title says `0.725 Ceiling`, but the note itself records a current best of `0.733920`.
- The note also lists open branches for scores above `0.73`.

This supports the failure mode: the knowledge base sometimes kept "plateau" or "ceiling" language after the active search had already moved beyond that level.

## 2. Heartbeats added repeated memory work and note overhead

Evidence source:
`results/bin-packing.full/2/.coral/public/heartbeat/agent-1.json`

Relevant facts:

- The `reflect` heartbeat runs every 1 interval, requiring extra work.

Evidence source:
`results/bin-packing.full/2/.coral/public/heartbeat/_global.json`

Relevant facts:

- The `consolidate` and `lint_wiki` heartbeat runs every 10 intervals.

Additional evidence:
`evidence/knife-edge-timeout-cluster.md`

Original source:
`results/bin-packing.full/2/.coral/public/notes/_synthesis/knife-edge-timeout-cluster.md`

Relevant facts:

- The note reports repeated 60-second timeouts, including zero-behavior-change commits.
- This shows that part of the run budget was spent around repeated diagnosis and documentation of runtime instability.

This supports the failure mode: heartbeats created useful summaries, but they also increased the amount of context and note maintenance that later agents had to read.

## 3. Experiments were mostly stored as flat files

The recent full runs stored most experiment memory as separate files in one flat folder:

| Run | Flat files in `.coral/public/notes/experiments` |
|---|---:|
| `results/bin-packing.full/1` | 97 |
| `results/bin-packing.full/2` | 91 |
| `results/bin-packing.full/3` | 106 |

The flat layout makes it hard to see which files are parent ideas, child experiments, retries, parameter sweeps, or dead ends. A later agent has to infer the dependency graph from filenames and prose.

## 4. Fine-tuning produced many similar notes

The recent full runs contain many tuning-like, sweep-like, timeout, flat, or regression notes:

This supports the failure mode: the useful signal was often short, such as "this parameter range is flat" or "this branch times out", but the knowledge base stored many small variants as separate top-level notes.

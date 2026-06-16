---
creator: agent-1
created: 2026-06-16T19:00:00
---
# Synthesis: Knife-Edge 60s Timeout Cluster

**Summary:** e378bade (agent-2 codebase, 0.725421 @ 55s nominal) fails 60s cap repeatedly in evals 33–37, including zero-behavior-change commits. agent-1 b9560db3 (0.724558 @ 59s) is the reliable scored base.

## Evidence

| Eval | Base | Change | Result |
|------|------|--------|--------|
| e378bade | agent-2 | none | **0.725421** @ 55s |
| 33–34 | e378bade | MIP cache | Timeout |
| 35 | e378bade | dead code | Timeout |
| 36 | e378bade | repack k=4 | Timeout |
| 37 | e378bade | threshold 0.96 | Timeout |

## Implications

1. Do not iterate on e378bade until environment stabilizes or runtime cut >10s
2. agent-1 should **not** compose value-first onto b9560db3 (evals 23, 38 timeout)
3. `_MIP_SELECT_TIME_LIMIT=1.5` is score-neutral headroom (agent-2 e378bade proof); try alone on b9560db3

## Confidence

**High** — timeout cluster is codebase/environment specific, not random single failures.

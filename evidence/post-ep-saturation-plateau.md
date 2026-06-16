---
creator: agent-2
created: 2026-06-16T14:30:00
---
# Synthesis: Post-EP Saturation Plateau

**Summary:** Once a pipeline includes EP repair + EP gap-fill, post-selection tuning (dual EP, intensive EP) yields zero gain at **0.683 tier**. **Exception (0.725+):** post-best local repack on overflow instances after selection MIP still moves score (+0.0031, ba4fa167) — removes low val-density placements to unlock EP refill of omitted high-value items.

## Evidence

| Change | Score delta | Items delta | Notes |
|--------|-------------|-------------|-------|
| EMS repair + dual EP (eval 5) | 0 | 0 | Redundant with EP gap-fill |
| EP repair + grader best-of (eval 6) | **+0.0045** | **+69** | Changed pre-saturation geometry |
| Post-selection EP + repack (eval 7) | 0 | 0 | After EP saturation |
| agent-1 local repack on EMS (122b69d) | 0 | 0 | Abandoned |
| agent-1 compose MIP+EP (2c7efb9f) | -0.009 | — | Conflicting stages |

## Why post-selection fails

EP maintains extreme points from all placed boxes. After repair + gap-fill, remaining unplaced items have no feasible non-overlapping placement at any generated EP — verified by identical packed volume/value across evals 6 and 7. Local repack removes items to free space, but EP already attempted high-value unplaced items in that space during repair.

## What still has headroom (untested at 0.683+)

1. **Multi-pass EP during MIP repair** (before gap-fill saturation)
2. **MIP volume slack tuning** (0.88–0.95 range)
3. **Item-selection MIP** when total item volume exceeds bin capacity
4. **Per-instance strategy selection** (MIP vs global based on instance shape)

## Confidence

**High** that post-EP post-selection is exhausted. **Medium** that MIP-parameter and in-path multi-EP passes can reach 0.69+.

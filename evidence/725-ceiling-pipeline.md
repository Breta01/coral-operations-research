---
creator: agent-2
created: 2026-06-16T17:26:00
---
# 0.725 Ceiling — Selection + EMS + EP Pipeline

## Current best

**0.733920** (ecf83e97): large-k k∈{16..64} × multi-ranking @ 53.69s.

Prior **0.733527** (3d1f66b8): k≤48.

Prior **0.725421** (e378bade / 777c26e1): value-first gap-fill + slack swap + 6×4 packing grid + MIP select 1.5s.

## What got us here

| Delta | Score lift | Eval |
|-------|-----------|------|
| Item-selection MIP | +0.027 | 9773b5fa |
| Multi-slack + near-overflow | +0.009 | b063242c |
| Tight slacks 0.99/1.0 | +0.0013 | e760c7d4 |
| Value-first gap-fill | +0.00086 | a813b280 |
| Slack swap 0.985/0.995 | +0.0016 | 06273309 |
| Post-best local repack k=4 | +0.0031 | ba4fa167 |

## Saturated (flat or timeout)

- Selection slack extension (0.992 timeout)
- MIP select time 1.5s (flat)
- MAX_EP 96 (flat at 0.722)
- MAX_EMS 48 (timeout)
- Density MIP prune, packing grid prune, variant cap (regress −0.002 to −0.003)
- Blended selection objective (flat)

## Runtime binding constraint

`overflow_instances × selection_variants × 36 packing paths × (EMS + EP cost)`. ~55s of 60s budget used on median run; **variance to 60s+** on identical code (eval 29 reproduce timeout).

## Open branches for >0.73

1. **Repack lane saturated** at 0.729398 — independent multi-ranking k=4 (38ed334d config)
2. **Lower repack threshold** — apply repack on near-overflow (0.85) while selection stays 0.92
3. **Local search post-pack** — agent-1 large-k repack in flight
4. **Grader-proxy selection objective**

**777c26e1**: 6 sorts + 4 strategies (no waste) = **0.725421 @ 44.59s**. Production config supersedes e378bade.

## Operational fast path (eval 34)

## Do not retry

- Stacking runtime prunes with slack swap
- Adding selection slacks without removing others
- Increasing EMS/EP capacity constants
- Skip bin-MIP on selection variants (timeout eval 28; no score signal)
- Any change when reproduce of e378bade fails — restore first

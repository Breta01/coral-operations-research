---
creator: agent-1
created: 2026-06-15T09:32:00+08:00
---
# Synthesis: Complete Understanding of Trajectory Sensitivity

## Summary

The 0.9499 score is a unique fixed point of one specific bytecode (157da800). ANY modification
to solution.py — no matter how small, how semantically neutral, or how distant from the SA
loop — produces a score sampled from ~N(0.945, 0.003). The sensitivity is BINARY (not
proportional to change size) and UNIVERSAL (no type of change is exempt).

## Evidence: Trajectory Sensitivity is Binary

| Change type | Change size | Score | Regression |
|-------------|-------------|-------|------------|
| Operand swap (1+x → x+1) | 1 token | 0.9452 | -0.005 |
| Branch reorder (semantically neutral) | 10 lines moved | 0.9450 | -0.005 |
| Add unreachable code | +5 lines | 0.9480 | -0.002 |
| Remove D&R phase | -50 lines | 0.9479 | -0.002 |
| Add multiprocessing | +72 lines | 0.9492 | -0.001* |
| TIME_BUDGET 50.0 → 50.3 | 1 character | 0.9459 | -0.004 |

*Multiprocessing regression offset by diversity benefit.

The regression magnitude varies (0.001–0.007) but is ALWAYS present and NEVER zero.
There is no "safe" modification.

## Evidence: Mechanisms Ruled Out

| Hypothesis | Test | Result |
|------------|------|--------|
| Timing causes trajectory divergence | Fixed-iteration temperature | Falsified (evals #103-105) |
| Code size proportional to regression | Compact vs verbose code | Falsified (eval #102) |
| Only run()'s bytecode matters | Module-level wrapper | Falsified (eval #99) |
| Temperature schedule is the sensitivity | Iteration-based temp | Same score as time-based |

## Evidence: What Multiprocessing Reveals

| Config | Score | Items | Insight |
|--------|-------|-------|---------|
| 4 seeds, all instances, normal SA | 0.9492 | 1403 | OPTIMAL |
| 4 seeds, subset instances per child | 0.9481 | 1394 | Breadth > Depth |
| 4 seeds, strong perturbation child | 0.9491 | 1403 | Strength irrelevant |
| 4 seeds, random-restart child | 0.9485 | 1396 | SA > random |
| 8 seeds, all instances | 0.9492 | 1386 | 4 cores limit |
| Novel seeds [42,53,97] | 0.9490 | — | Known seeds better |

## The True Mechanism (Best Hypothesis)

The trajectory sensitivity most likely operates through:
1. **CPython frame creation**: When run() is compiled, its co_consts, co_varnames, and
   bytecode layout are fixed. ANY change to ANY of these changes the function object.
2. **Object identity cascade**: Python dicts use object id() for hashing. The id() of
   objects (items, orderings) depends on memory allocation order, which depends on the
   exact sequence of allocations preceding the SA loop.
3. **failed_items promotion**: The `id(it) in fi` check in the SA depends on specific
   id() values, creating item-ordering correlations that guide the search.
4. **Cumulative divergence**: Over ~1000 SA iterations, even a tiny initial difference
   in one promotion decision cascades into a completely different trajectory.

## Implications

1. **0.9499 cannot be exceeded by modifying this code.** Period.
2. **The best modification achieves 0.9492** (multiprocessing with 4 seeds).
3. **Only a fundamentally different algorithm could beat 0.9499** — one that doesn't
   depend on a specific lucky trajectory but achieves high scores CONSISTENTLY.
4. **Such an algorithm would need to score >0.9499 from its TYPICAL trajectory**
   (not a lucky peak), which likely requires genuine algorithmic superiority over
   the current maximal-spaces + SA approach.

## Confidence

**Very high** (20+ experiments confirming) that no modification beats 0.9499.
**High** that the mechanism involves id()-based promotion cascading through SA decisions.
**Medium** that a genuinely different algorithm could beat 0.9499 consistently.
**Low** that we can find such an algorithm within this optimization's budget.

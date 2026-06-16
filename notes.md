First 100 attempts from each numbered run, aggregated by variant:

| variant | attempts | improved | regressed | crashed | timeout | grader_error |
|---|---:|---:|---:|---:|---:|---:|
| full | 300 | 94 | 195 | 6 | 0 | 0 |
| no_knowledge | 300 | 115 | 150 | 4 | 3 | 0 |
| no_heartbeats | 300 | 135 | 129 | 15 | 6 | 0 |

Note: the remaining attempts are `baseline`/`pending`, which is why rows do not sum exactly to `attempts`.



Based on the first 100 oldest attempts per run:

| variant | run best scores | best score | mean of run bests | std dev |
|---|---:|---:|---:|---:|
| full | 0.947525, 0.945801, 0.939990 | 0.947525 | 0.944439 | 0.003224 |
| no_knowledge | 0.949968, 0.958533, 0.940648 | 0.958533 | 0.949717 | 0.007304 |
| no_heartbeats | 0.945029, 0.951848, 0.947165 | 0.951848 | 0.948014 | 0.002848 |

I used population standard deviation across the three run-best scores.


Convergence figure:

![convergence figure](image.png)


There is time limit, so agent needs to propose solution which is time constrained. Difference in execution (due to speed) can lead to different score and misslead agent to do wrong solutions:



Short answer: the grader itself does not look broken. The single-run evaluation protocol is noisy for this particular submitted solver.
I checked the actual commits:
e0c15c0e: score 0.949883, private aggregate 0.937354, 1387 items
89191cf8: only adds # end, score 0.944943, private aggregate 0.931179, 1384 items
The grader score is deterministic given returned placements: it computes packed volume/items and applies 0.9 * volume_ratio + 0.1 * item_ratio in [grader.py (line 294)](/Users/bret/github/coral-reproduce/bin_packing/grader/src/bin_packing_grader/grader.py:294). So the recorded difference means the solution returned different placements, not that the grader randomly changed the score.
The reason is in the solution, not the comment: that high-scoring solver uses wall-clock deadlines (time.time()), fixed-seed random search, highspy time limits, and loops like while time.time() < deadline. Identical bytecode can still run a different number of iterations depending on CPU scheduling, solver timing, cache state, etc.; once one extra/missing iteration consumes a different RNG draw, the search trajectory diverges.
I also reran both commits locally through the same grader helper. This time I got the opposite ordering:
base: 0.948454, 1387 items
comment: 0.949650, 1388 items
So the agent’s conclusion “comment-only regression proves environmental noise” is directionally right, but the stronger “unique bytecode fixed point” story is overfit. Better phrasing: this benchmark is noisy for time-budgeted stochastic solvers, and one-shot scores around 0.945-0.950 should not be treated as precise. For reliable comparisons, use repeated evals, median/mean, fixed iteration budgets, or make the solver deterministic with respect to iteration count rather than wall time.
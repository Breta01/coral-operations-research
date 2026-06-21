"""Provable upper bound on the 3D bin-packing grader score.

The grader scores each instance as

    score = 0.5 * packed_volume / volume_bound + 0.5 * packed_value / total_value

with volume_bound = min(total_item_volume, total_bin_volume) and an item's value
taken from its explicit ``value`` field, else volume ** 0.65.

Any feasible 3D packing selects a subset of items whose total volume cannot
exceed the total bin volume (boxes are axis-aligned, non-overlapping, inside the
bins) and uses no more than the available quantity of each type. Relaxing away
all geometry and keeping ONLY those two facts gives a bounded knapsack whose
optimum is a valid UPPER BOUND on the achievable grader score: for every real
packing P with item set S, score(P) <= knapsack_opt, because S is feasible for
the knapsack and the knapsack maximizes exactly the grader's score expression.

We solve the knapsack exactly with HiGHS (highspy). The bound is tight for the
volume/value-selection structure of the problem and loose only to the extent
that real geometry forbids perfectly volume-filling packings.
"""

from __future__ import annotations

import importlib.resources
import json
import os
import sys

# Make the grader package importable without setting PYTHONPATH: add
# <repo>/bin_packing/grader/src (relative to this file) to sys.path.
_GRADER_SRC = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "bin_packing", "grader", "src",
)
if _GRADER_SRC not in sys.path:
    sys.path.insert(0, _GRADER_SRC)

import highspy


def _load_instances() -> list[dict]:
    """Load the exact 5 public + 20 private instances the grader evaluates."""
    data_dir = importlib.resources.files("bin_packing_grader.data")
    public = json.loads(data_dir.joinpath("instances.json").read_text())
    private = json.loads(data_dir.joinpath("private_instances.json").read_text())
    return (
        [{**inst, "split": "public"} for inst in public]
        + [{**inst, "split": "private"} for inst in private]
    )


def _instance_economics(instance: dict) -> dict:
    """Replicate the grader's value / volume_bound / total_value computation."""
    items = instance["items"]
    vols = [float(it["length"]) * float(it["width"]) * float(it["height"]) for it in items]
    values = [
        float(it.get("value", vol ** 0.65))
        for it, vol in zip(items, vols)
    ]
    qtys = [int(it["quantity"]) for it in items]

    total_item_volume = sum(q * v for q, v in zip(qtys, vols))
    bin_volume = float(sum(b["length"] * b["width"] * b["height"] for b in instance["bins"]))
    volume_bound = min(total_item_volume, bin_volume)
    total_value = sum(q * val for q, val in zip(qtys, values))

    return {
        "vols": vols,
        "values": values,
        "qtys": qtys,
        "bin_volume": bin_volume,
        "volume_bound": volume_bound,
        "total_value": total_value,
        "total_item_volume": total_item_volume,
    }


def _upper_bound(instance: dict) -> dict:
    econ = _instance_economics(instance)
    vols, values, qtys = econ["vols"], econ["values"], econ["qtys"]
    bin_volume = econ["bin_volume"]
    volume_bound = econ["volume_bound"]
    total_value = econ["total_value"]
    n = len(vols)

    h = highspy.Highs()
    h.setOptionValue("output_flag", False)

    inf = highspy.kHighsInf
    # Integer var per item type: 0 <= x_i <= quantity_i (count of that type packed).
    for q in qtys:
        h.addVar(0.0, float(q))
    h.changeColsIntegrality(n, list(range(n)), [highspy.HighsVarType.kInteger] * n)

    # Objective: maximize 0.5 * (Σ x_i vol_i)/volume_bound + 0.5 * (Σ x_i value_i)/total_value
    obj_coeffs = [
        0.5 * vols[i] / volume_bound + 0.5 * values[i] / total_value
        for i in range(n)
    ]
    h.changeColsCost(n, list(range(n)), obj_coeffs)
    h.changeObjectiveSense(highspy.ObjSense.kMaximize)

    # Capacity: Σ x_i vol_i <= total bin volume  (the only geometric fact kept).
    h.addRow(-inf, bin_volume, n, list(range(n)), vols)

    h.run()
    sol = h.getSolution()
    counts = [int(round(sol.col_value[i])) for i in range(n)]

    packed_volume = sum(c * v for c, v in zip(counts, vols))
    packed_value = sum(c * val for c, val in zip(counts, values))
    volume_ratio = packed_volume / volume_bound if volume_bound > 0 else 0.0
    value_ratio = packed_value / total_value if total_value > 0 else 0.0
    score = max(0.0, min(1.0, 0.5 * volume_ratio + 0.5 * value_ratio))

    return {
        "id": instance["id"],
        "split": instance.get("split", "public"),
        "score": score,
        "volume_ratio": volume_ratio,
        "value_ratio": value_ratio,
        "packed_volume": packed_volume,
        "volume_bound": volume_bound,
        "packed_value": packed_value,
        "total_value": total_value,
        "packed_items": sum(counts),
        "total_items": sum(qtys),
        "oversubscription": econ["total_item_volume"] / bin_volume,
    }


def main() -> None:
    instances = _load_instances()
    rows = [_upper_bound(inst) for inst in instances]

    def mean(key, subset):
        vals = [r[key] for r in rows if r["split"] in subset]
        return sum(vals) / len(vals) if vals else 0.0

    print(f"{'instance':<14}{'split':<9}{'score':>8}{'vol_r':>8}{'val_r':>8}"
          f"{'items':>10}{'over':>7}")
    print("-" * 64)
    for r in rows:
        print(f"{r['id']:<14}{r['split']:<9}{r['score']:>8.4f}{r['volume_ratio']:>8.4f}"
              f"{r['value_ratio']:>8.4f}{r['packed_items']:>5}/{r['total_items']:<4}"
              f"{r['oversubscription']:>7.2f}")
    print("-" * 64)
    overall = mean("score", {"public", "private"})
    pub = mean("score", {"public"})
    priv = mean("score", {"private"})
    print(f"UPPER BOUND  overall={overall:.4f}  public={pub:.4f}  private={priv:.4f}")

    out = {
        "method": "volume-knapsack LP relaxation (HiGHS), geometry dropped",
        "overall_upper_bound": overall,
        "public_upper_bound": pub,
        "private_upper_bound": priv,
        "instances": rows,
    }
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.path.join(repo_root, "output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "upper_bound.json")
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()

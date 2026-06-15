"""Baseline heuristic for the 3D bin-packing task.

The grader imports this module and calls run(instances). Agents should replace
this baseline with a stronger optimizer, for example a highspy MIP model plus a
packing/repair heuristic.
"""

from __future__ import annotations

from itertools import permutations


def _rotations(item: dict) -> list[tuple[float, float, float]]:
    dims = (item["length"], item["width"], item["height"])
    return sorted(set(permutations(dims)), key=lambda d: (d[2], d[1], d[0]))


def _expanded_items(instance: dict) -> list[dict]:
    items = []
    for item in instance["items"]:
        for _ in range(item["quantity"]):
            items.append(dict(item))
    items.sort(key=lambda it: it["length"] * it["width"] * it["height"], reverse=True)
    return items


def _pack_instance(instance: dict) -> list[dict]:
    placements = []
    remaining = _expanded_items(instance)

    for bin_index, bin_spec in enumerate(instance["bins"]):
        x = y = z = 0.0
        row_width = 0.0
        layer_height = 0.0
        kept = []

        for item in remaining:
            placed = None
            for l, w, h in _rotations(item):
                candidates = [
                    (x, y, z),
                    (0.0, y + row_width, z),
                    (0.0, 0.0, z + layer_height),
                ]
                for cx, cy, cz in candidates:
                    if (
                        cx + l <= bin_spec["length"]
                        and cy + w <= bin_spec["width"]
                        and cz + h <= bin_spec["height"]
                    ):
                        placed = {
                            "bin": bin_index,
                            "item_id": item["id"],
                            "x": cx,
                            "y": cy,
                            "z": cz,
                            "l": l,
                            "w": w,
                            "h": h,
                        }
                        break
                if placed is not None:
                    break

            if placed is None:
                kept.append(item)
                continue

            placements.append(placed)
            x = placed["x"] + placed["l"]
            y = placed["y"]
            z = placed["z"]
            row_width = max(row_width, placed["w"])
            layer_height = max(layer_height, placed["h"])

        remaining = kept

    return placements


def run(instances: list[dict]) -> dict[str, list[dict]]:
    return {instance["id"]: _pack_instance(instance) for instance in instances}

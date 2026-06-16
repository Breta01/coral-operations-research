"""Deterministic private benchmark instances for the 3D bin-packing grader."""

from __future__ import annotations

import importlib.resources
import json


def make_private_instances() -> list[dict]:
    data_file = importlib.resources.files("bin_packing_grader.data").joinpath(
        "private_instances.json"
    )
    if data_file.is_file():
        return json.loads(data_file.read_text())

    return [_make_instance(*spec) for spec in _SPECS]


_SPECS = [
    ("private_01", [(42, 42, 38)], 1.65),
    ("private_02", [(60, 42, 34)], 1.85),
    ("private_03", [(72, 54, 40)], 2.10),
    ("private_04", [(90, 52, 46)], 2.40),
    ("private_05", [(110, 70, 44)], 2.70),
    ("private_06", [(64, 64, 64)], 1.90),
    ("private_07", [(96, 48, 72)], 2.30),
    ("private_08", [(120, 60, 50)], 2.80),
    ("private_09", [(150, 80, 60)], 2.55),
    ("private_10", [(180, 90, 54)], 2.95),
    ("private_11", [(48, 36, 96)], 1.75),
    ("private_12", [(75, 75, 30)], 2.05),
    ("private_13", [(100, 40, 40), (100, 40, 40)], 2.25),
    ("private_14", [(130, 65, 52)], 2.65),
    ("private_15", [(160, 70, 70)], 3.00),
    ("private_16", [(58, 58, 58)], 1.55),
    ("private_17", [(200, 100, 80)], 2.85),
    ("private_18", [(84, 42, 126)], 2.35),
    ("private_19", [(140, 56, 42), (70, 56, 84)], 2.60),
    ("private_20", [(220, 110, 66)], 2.90),
]


def _volume(dims: tuple[int, int, int]) -> int:
    length, width, height = dims
    return length * width * height


def _value(dims: tuple[int, int, int], multiplier: float) -> float:
    return round((_volume(dims) ** 0.65) * multiplier, 3)


def _add_item(
    items: list[dict],
    item_id: int,
    quantity: int,
    dims: tuple[int, int, int],
    value_multiplier: float,
    role: str,
) -> int:
    length, width, height = dims
    items.append(
        {
            "id": item_id,
            "quantity": int(quantity),
            "length": int(length),
            "width": int(width),
            "height": int(height),
            "value": _value(dims, value_multiplier),
            "role": role,
        }
    )
    return item_id + 1


def _make_instance(
    instance_id: str,
    bin_specs: list[tuple[int, int, int]],
    target_oversubscription: float,
) -> dict:
    max_length = max(b[0] for b in bin_specs)
    max_width = max(b[1] for b in bin_specs)
    max_height = max(b[2] for b in bin_specs)
    short = max(3, min(max_length, max_width, max_height) // 12)
    thin = max(2, min(max_length, max_width, max_height) // 18)
    slab = max(3, max_height // 9)
    items: list[dict] = []
    item_id = 0

    item_id = _add_item(items, item_id, 4, (max(4, max_length // 2), max(4, max_width // 2), max(3, max_height // 4)), 1.45, "complement_a")
    item_id = _add_item(items, item_id, 6, (max(4, max_length // 3), max(4, max_width // 2), max(3, max_height // 4)), 1.40, "complement_b")
    item_id = _add_item(items, item_id, 8, (max(4, max_length // 4), max(4, max_width // 2), max(3, max_height // 4)), 1.35, "complement_c")
    item_id = _add_item(items, item_id, 3, (max(5, max_length - 2), max(3, thin), max(3, thin)), 1.30, "long_rod_x")
    item_id = _add_item(items, item_id, 3, (max(3, thin), max(5, max_width - 2), max(3, thin)), 1.30, "long_rod_y")
    item_id = _add_item(items, item_id, 3, (max(3, thin), max(3, thin), max(5, max_height - 2)), 1.30, "long_rod_z")
    item_id = _add_item(items, item_id, 3, (max(5, max_length - 4), max(5, max_width // 3), max(3, slab)), 1.20, "wide_slab")
    item_id = _add_item(items, item_id, 3, (max(5, max_length // 3), max(5, max_width - 3), max(3, slab)), 1.20, "deep_slab")
    item_id = _add_item(items, item_id, 2, (max(5, max_length // 2 + 1), max(5, max_width - 1), max(3, max_height // 5)), 1.15, "near_width_blocker")
    item_id = _add_item(items, item_id, 10, (max(4, max_length // 5), max(4, max_width // 3), max(4, max_height // 3)), 1.05, "medium_brick")
    item_id = _add_item(items, item_id, 12, (max(4, max_length // 6), max(4, max_width // 4), max(4, max_height // 2)), 1.00, "upright_brick")
    item_id = _add_item(items, item_id, 26, (short, short, short), 0.18, "low_value_filler")
    _add_item(items, item_id, 18, (max(2, short // 2), short, max(2, short // 2)), 0.12, "tiny_decoy")

    bin_volume = sum(_volume(spec) for spec in bin_specs)
    item_volume = sum(
        item["quantity"] * _volume((item["length"], item["width"], item["height"]))
        for item in items
    )
    bump_order = [0, 1, 2, 6, 7, 9, 10, 11]
    cursor = 0
    while item_volume / bin_volume < target_oversubscription:
        idx = bump_order[cursor % len(bump_order)]
        items[idx]["quantity"] += 1
        item_volume += _volume((items[idx]["length"], items[idx]["width"], items[idx]["height"]))
        cursor += 1

    cursor = 0
    while item_volume / bin_volume > 3.0:
        idx = bump_order[-1 - (cursor % len(bump_order))]
        if items[idx]["quantity"] > 1:
            items[idx]["quantity"] -= 1
            item_volume -= _volume((items[idx]["length"], items[idx]["width"], items[idx]["height"]))
        cursor += 1
        if cursor > 200:
            break

    return {
        "id": instance_id,
        "bins": [
            {"id": bin_id, "length": length, "width": width, "height": height}
            for bin_id, (length, width, height) in enumerate(bin_specs)
        ],
        "items": items,
    }

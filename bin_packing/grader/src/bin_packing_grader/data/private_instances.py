"""Deterministic private benchmark instances for the 3D bin-packing grader."""

from __future__ import annotations

import importlib.resources
import json
import random


def make_private_instances() -> list[dict]:
    data_file = importlib.resources.files("bin_packing_grader.data").joinpath(
        "private_instances.json"
    )
    if data_file.is_file():
        return json.loads(data_file.read_text())

    rng = random.Random(42)
    cases: list[dict] = []
    specs = [
        ("private_01", [(40, 40, 40)], 8, (3, 8), (5, 24), True),
        ("private_02", [(60, 45, 35)], 9, (3, 7), (4, 30), True),
        ("private_03", [(80, 60, 55), (45, 45, 45)], 11, (2, 8), (6, 38), True),
        ("private_04", [(100, 70, 50), (65, 65, 65)], 12, (2, 7), (8, 48), False),
        ("private_05", [(120, 90, 75)], 14, (2, 9), (10, 55), True),
        ("private_06", [(90, 90, 90), (70, 80, 60), (50, 50, 110)], 13, (2, 8), (8, 52), True),
        ("private_07", [(150, 100, 80), (90, 90, 90)], 16, (2, 6), (8, 70), True),
        ("private_08", [(35, 35, 100), (55, 45, 65)], 10, (4, 10), (3, 32), True),
        ("private_09", [(200, 160, 120)], 18, (2, 8), (12, 90), False),
        ("private_10", [(120, 120, 120), (80, 100, 60), (140, 60, 50)], 15, (3, 7), (8, 64), True),
        ("private_11", [(30, 30, 30)], 7, (5, 14), (2, 18), True),
        ("private_12", [(48, 32, 28), (28, 48, 32)], 9, (4, 12), (2, 24), True),
        ("private_13", [(75, 75, 35), (60, 40, 80)], 12, (3, 9), (5, 42), True),
        ("private_14", [(250, 180, 140), (160, 160, 100)], 20, (2, 7), (15, 105), True),
        ("private_15", [(300, 220, 160)], 22, (2, 6), (20, 130), False),
        ("private_16", [(90, 40, 40), (40, 90, 40), (40, 40, 90)], 12, (3, 10), (4, 44), True),
        ("private_17", [(500, 320, 280), (220, 220, 220)], 24, (1, 5), (35, 190), True),
        ("private_18", [(64, 64, 64)], 14, (4, 12), (4, 36), True),
        ("private_19", [(110, 75, 95), (95, 70, 55)], 13, (3, 8), (8, 58), True),
        ("private_20", [(180, 90, 60), (100, 100, 100), (70, 130, 80)], 18, (2, 7), (8, 85), True),
    ]
    for args in specs:
        cases.append(_make_instance(rng, *args))
    return cases


def _make_instance(
    rng: random.Random,
    instance_id: str,
    bin_specs: list[tuple[int, int, int]],
    type_count: int,
    qty_range: tuple[int, int],
    dim_range: tuple[int, int],
    awkward: bool,
) -> dict:
    items = []
    for item_id in range(type_count):
        if awkward and item_id % 4 == 0:
            length = rng.randint(int(dim_range[1] * 0.55), dim_range[1])
            width = rng.randint(dim_range[0], max(dim_range[0], int(dim_range[1] * 0.20)))
            height = rng.randint(dim_range[0], max(dim_range[0], int(dim_range[1] * 0.22)))
        elif awkward and item_id % 4 == 1:
            length = rng.randint(dim_range[0], max(dim_range[0], int(dim_range[1] * 0.25)))
            width = rng.randint(int(dim_range[1] * 0.45), dim_range[1])
            height = rng.randint(dim_range[0], max(dim_range[0], int(dim_range[1] * 0.30)))
        else:
            length = rng.randint(*dim_range)
            width = rng.randint(*dim_range)
            height = rng.randint(*dim_range)

        items.append(
            {
                "id": item_id,
                "quantity": rng.randint(*qty_range),
                "length": length,
                "width": width,
                "height": height,
            }
        )

    return {
        "id": instance_id,
        "bins": [
            {"id": bin_id, "length": length, "width": width, "height": height}
            for bin_id, (length, width, height) in enumerate(bin_specs)
        ],
        "items": items,
    }

"""Achievable anchor for the 3D bin-packing grader, using py3dbp.

py3dbp produces *feasible* placements, so this is NOT an upper bound -- it is a
realistic best-achievable score (a lower bound on the true optimum) graded by
the real grader's geometric validator.

py3dbp's stock packer orders items by volume only. The grader's score is
0.5*vol_ratio + 0.5*value_ratio, and for the oversubscribed instances vol_ratio
is easy to drive near 1.0 while value_ratio is the scarce resource. So we drive
the packing order by value-density (value / volume) instead, which targets the
part of the objective py3dbp would otherwise ignore.
"""

from __future__ import annotations

from py3dbp import Packer, Bin, Item


class _ValuePacker(Packer):
    """Identical to Packer.pack but orders items by a supplied priority key."""

    def __init__(self, priority: dict):
        super().__init__()
        self._priority = priority

    def pack(self, distribute_items=True, number_of_decimals=4):  # type: ignore[override]
        for b in self.bins:
            b.format_numbers(number_of_decimals)
        for it in self.items:
            it.format_numbers(number_of_decimals)
        # Bigger bins first; items by value-density (tie-break larger volume).
        self.bins.sort(key=lambda b: b.get_volume(), reverse=True)
        self.items.sort(key=lambda it: self._priority[it.name], reverse=True)
        for b in self.bins:
            for it in self.items:
                self.pack_to_bin(b, it)
            if distribute_items:
                for it in list(b.items):
                    self.items.remove(it)


def _value_of(item: dict, vol: float) -> float:
    return float(item.get("value", vol ** 0.65))


# Ordering strategies: each maps (density, value, vol) -> sort key (desc).
_STRATEGIES = {
    "density":  lambda d, val, vol: (d, vol),       # value-per-volume, tie big first
    "volume":   lambda d, val, vol: (vol,),         # py3dbp's native bigger-first
    "value":    lambda d, val, vol: (val,),         # absolute value first
    "val_x_vol": lambda d, val, vol: (val * vol,),  # value weighted by footprint
}


def _pack(instance: dict, key_fn) -> list:
    packer = _ValuePacker.__new__(_ValuePacker)
    Packer.__init__(packer)
    priority: dict = {}
    packer._priority = priority

    # Bins: py3dbp axes (width,height,depth) <-> grader (length,width,height).
    # Name = original bin index so we can recover it after py3dbp re-sorts.
    for idx, b in enumerate(instance["bins"]):
        packer.add_bin(Bin(str(idx), b["length"], b["width"], b["height"], 1e12))

    for item in instance["items"]:
        l, w, h = item["length"], item["width"], item["height"]
        vol = float(l) * float(w) * float(h)
        val = _value_of(item, vol)
        density = val / vol if vol > 0 else 0.0
        for k in range(int(item["quantity"])):
            name = f"{item['id']}#{k}"
            priority[name] = key_fn(density, val, vol)
            packer.add_item(Item(name, l, w, h, 0))

    packer.pack(distribute_items=True, number_of_decimals=4)

    placements = []
    for b in packer.bins:
        bidx = int(b.name)
        for it in b.items:
            px, py, pz = (float(v) for v in it.position)
            dl, dw, dh = (float(v) for v in it.get_dimension())
            placements.append({
                "bin": bidx,
                "item_id": int(it.name.split("#")[0]),
                "x": px, "y": py, "z": pz,
                "l": dl, "w": dw, "h": dh,
            })
    return placements


def _grader_score(instance: dict, placements: list) -> float:
    """Replicate the grader's score for feasible placements (py3dbp guarantees
    geometric feasibility, so only volume/value totals matter here)."""
    item_vol = {int(it["id"]): float(it["length"]) * it["width"] * it["height"]
                for it in instance["items"]}
    item_val = {int(it["id"]): _value_of(it, item_vol[int(it["id"])])
                for it in instance["items"]}
    total_item_vol = sum(int(it["quantity"]) * item_vol[int(it["id"])]
                         for it in instance["items"])
    bin_vol = float(sum(b["length"] * b["width"] * b["height"] for b in instance["bins"]))
    volume_bound = min(total_item_vol, bin_vol)
    total_value = sum(int(it["quantity"]) * item_val[int(it["id"])]
                      for it in instance["items"])
    packed_vol = sum(p["l"] * p["w"] * p["h"] for p in placements)
    packed_val = sum(item_val[p["item_id"]] for p in placements)
    vr = packed_vol / volume_bound if volume_bound > 0 else 0.0
    vvr = packed_val / total_value if total_value > 0 else 0.0
    return max(0.0, min(1.0, 0.5 * vr + 0.5 * vvr))


def _solve(instance: dict) -> list:
    best, best_score = [], -1.0
    for key_fn in _STRATEGIES.values():
        placements = _pack(instance, key_fn)
        s = _grader_score(instance, placements)
        if s > best_score:
            best, best_score = placements, s
    return best


def run(instances: list) -> dict:
    return {inst["id"]: _solve(inst) for inst in instances}

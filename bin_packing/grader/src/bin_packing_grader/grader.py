"""3D bin-packing grader.

The agent program must define ``run(instances)``. ``instances`` is a list of
benchmark dictionaries. The function should return either:

* a dict mapping each instance id to a list of placements, or
* a list with one placement list per instance, in the same order.

A placement may be a dict with keys ``bin``, ``item_id``, ``x``, ``y``, ``z``,
``l``, ``w``, ``h`` or a tuple/list ``(bin, item_id, x, y, z, l, w, h)``.
Coordinates are the lower-left-back corner of an axis-aligned placed item.
Rotations are allowed: ``(l, w, h)`` must be a permutation of the selected
item type dimensions.
"""

from __future__ import annotations

import importlib.resources
import json
import math
import os
import textwrap
from typing import Any

from coral.grader import TaskGrader
from coral.types import ScoreBundle

from bin_packing_grader.data.private_instances import make_private_instances

EPS = 1e-6


class Grader(TaskGrader):
    """Evaluate 3D bin-packing submissions."""

    def evaluate(self) -> ScoreBundle:
        program_file = self.args.get("program_file", "solution.py")
        program_path = os.path.join(self.codebase_path, program_file)
        if not os.path.exists(program_path):
            return self.fail(f"Program file not found: {program_file}")

        try:
            data_dir = importlib.resources.files("bin_packing_grader.data")
            public_instances = json.loads(data_dir.joinpath("instances.json").read_text())
            private_instances = make_private_instances()
            instances = [
                {**instance, "split": "public"} for instance in public_instances
            ] + [
                {**instance, "split": "private"} for instance in private_instances
            ]
        except Exception as e:
            return self.fail(f"Grader data could not be loaded: {e}")

        try:
            result = _run_evaluation(
                program_path=program_path,
                instances=instances,
                timeout=self.timeout or 300,
                python_cmd=self.get_python_command(),
            )
        except TimeoutError:
            return self.fail(f"Evaluation timed out after {self.timeout}s")
        except Exception as e:
            return self.fail(f"Evaluation failed: {type(e).__name__}: {e}")

        if "error" in result:
            return self.fail(f"Error: {result['error']}")

        score = float(result["score"])
        summaries = result["instances"]
        public_summaries = [row for row in summaries if row.get("split") == "public"]
        private_summaries = [row for row in summaries if row.get("split") == "private"]
        public_score = _mean(row["score"] for row in public_summaries)
        private_score = _mean(row["score"] for row in private_summaries)
        explanation = (
            f"Score: {score:.6f} | "
            f"Public: {public_score:.6f} | "
            f"Private: {private_score:.6f} | "
            f"Packed volume: {result['packed_volume']:.0f}/{result['volume_bound']:.0f} | "
            f"Items: {result['packed_items']}/{result['total_items']} | "
            f"Time: {result['eval_time']:.2f}s"
        )

        feedback_lines = []
        for row in public_summaries:
            line = (
                f"{row['id']}: score={row['score']:.4f}, "
                f"volume={row['packed_volume']:.0f}/{row['volume_bound']:.0f}, "
                f"items={row['packed_items']}/{row['total_items']}"
            )
            if row.get("violations"):
                line += f", violations={'; '.join(row['violations'][:3])}"
            feedback_lines.append(line)
        feedback_lines.append(
            f"private: {len(private_summaries)} hidden instances, aggregate score={private_score:.4f}"
        )

        return self.score(
            score,
            explanation,
            feedback="\n".join(feedback_lines),
            metadata={
                "public_instances": public_summaries,
                "private": {
                    "count": len(private_summaries),
                    "score": private_score,
                    "packed_volume": sum(row["packed_volume"] for row in private_summaries),
                    "volume_bound": sum(row["volume_bound"] for row in private_summaries),
                    "packed_items": sum(row["packed_items"] for row in private_summaries),
                    "total_items": sum(row["total_items"] for row in private_summaries),
                },
            },
        )


def _run_evaluation(
    program_path: str,
    instances: list[dict[str, Any]],
    timeout: int,
    python_cmd: list[str],
) -> dict[str, Any]:
    """Run the submitted program in a subprocess and parse JSON results."""

    script = textwrap.dedent(
        f"""\
        import copy
        import importlib.util
        import json
        import math
        import os
        import sys
        import time

        EPS = {EPS!r}
        INSTANCES = {json.dumps(instances)!r}


        def load_program(path):
            module_name = os.path.splitext(os.path.basename(path))[0]
            sys.path.insert(0, os.path.dirname(path))
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec is None or spec.loader is None:
                raise RuntimeError(f"could not import {{path}}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module


        def finite_number(value, name):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{{name}} must be numeric")
            value = float(value)
            if not math.isfinite(value):
                raise ValueError(f"{{name}} must be finite")
            return value


        def same_dimensions(got, expected):
            got_sorted = sorted(float(x) for x in got)
            expected_sorted = sorted(float(x) for x in expected)
            return all(abs(a - b) <= EPS for a, b in zip(got_sorted, expected_sorted))


        def normalize_placement(raw):
            if isinstance(raw, dict):
                try:
                    return {{
                        "bin": int(raw.get("bin", raw.get("bin_index"))),
                        "item_id": int(raw.get("item_id", raw.get("id", raw.get("type")))),
                        "x": finite_number(raw["x"], "x"),
                        "y": finite_number(raw["y"], "y"),
                        "z": finite_number(raw["z"], "z"),
                        "l": finite_number(raw.get("l", raw.get("length")), "l"),
                        "w": finite_number(raw.get("w", raw.get("width")), "w"),
                        "h": finite_number(raw.get("h", raw.get("height")), "h"),
                    }}
                except KeyError as e:
                    raise ValueError(f"missing placement field {{e}}")
            if isinstance(raw, (list, tuple)) and len(raw) == 8:
                b, item_id, x, y, z, l, w, h = raw
                return {{
                    "bin": int(b),
                    "item_id": int(item_id),
                    "x": finite_number(x, "x"),
                    "y": finite_number(y, "y"),
                    "z": finite_number(z, "z"),
                    "l": finite_number(l, "l"),
                    "w": finite_number(w, "w"),
                    "h": finite_number(h, "h"),
                }}
            raise ValueError("placement must be dict or 8-tuple/list")


        def overlap(a, b):
            return (
                a["x"] < b["x"] + b["l"] - EPS and b["x"] < a["x"] + a["l"] - EPS
                and a["y"] < b["y"] + b["w"] - EPS and b["y"] < a["y"] + a["w"] - EPS
                and a["z"] < b["z"] + b["h"] - EPS and b["z"] < a["z"] + a["h"] - EPS
            )


        def get_instance_answer(answer, idx, instance_id):
            if isinstance(answer, dict):
                if instance_id in answer:
                    return answer[instance_id]
                if str(instance_id) in answer:
                    return answer[str(instance_id)]
                return []
            if isinstance(answer, (list, tuple)):
                if idx >= len(answer):
                    return []
                return answer[idx]
            raise ValueError("run() must return a dict or list")


        def evaluate_instance(instance, raw_answer):
            item_types = {{int(item["id"]): item for item in instance["items"]}}
            type_counts = {{item_id: 0 for item_id in item_types}}
            total_items = int(sum(item["quantity"] for item in instance["items"]))
            total_item_volume = float(sum(
                item["quantity"] * item["length"] * item["width"] * item["height"]
                for item in instance["items"]
            ))
            bins = instance["bins"]
            bin_volume = float(sum(b["length"] * b["width"] * b["height"] for b in bins))
            volume_bound = min(total_item_volume, bin_volume)

            violations = []
            valid = []
            if raw_answer is None:
                raw_answer = []
            if not isinstance(raw_answer, (list, tuple)):
                return {{
                    "id": instance["id"],
                    "split": instance.get("split", "public"),
                    "score": 0.0,
                    "packed_volume": 0.0,
                    "volume_bound": volume_bound,
                    "packed_items": 0,
                    "total_items": total_items,
                    "violations": ["instance answer must be a placement list"],
                }}

            for placement_index, raw in enumerate(raw_answer):
                try:
                    p = normalize_placement(raw)
                except Exception as e:
                    violations.append(f"placement {{placement_index}} malformed: {{e}}")
                    continue

                item = item_types.get(p["item_id"])
                if item is None:
                    violations.append(f"placement {{placement_index}} uses unknown item_id {{p['item_id']}}")
                    continue
                if not (0 <= p["bin"] < len(bins)):
                    violations.append(f"placement {{placement_index}} uses invalid bin {{p['bin']}}")
                    continue
                if p["l"] <= EPS or p["w"] <= EPS or p["h"] <= EPS:
                    violations.append(f"placement {{placement_index}} has nonpositive dimensions")
                    continue
                if not same_dimensions((p["l"], p["w"], p["h"]), (item["length"], item["width"], item["height"])):
                    violations.append(f"placement {{placement_index}} dimensions do not match item {{p['item_id']}}")
                    continue

                type_counts[p["item_id"]] += 1
                if type_counts[p["item_id"]] > int(item["quantity"]):
                    violations.append(f"too many placements for item_id {{p['item_id']}}")
                    type_counts[p["item_id"]] -= 1
                    continue

                b = bins[p["bin"]]
                if (
                    p["x"] < -EPS or p["y"] < -EPS or p["z"] < -EPS
                    or p["x"] + p["l"] > b["length"] + EPS
                    or p["y"] + p["w"] > b["width"] + EPS
                    or p["z"] + p["h"] > b["height"] + EPS
                ):
                    violations.append(f"placement {{placement_index}} is outside bin {{p['bin']}}")
                    type_counts[p["item_id"]] -= 1
                    continue

                collision = None
                for prev_index, q in enumerate(valid):
                    if p["bin"] == q["bin"] and overlap(p, q):
                        collision = prev_index
                        break
                if collision is not None:
                    violations.append(f"placement {{placement_index}} overlaps accepted placement {{collision}}")
                    type_counts[p["item_id"]] -= 1
                    continue

                valid.append(p)

            packed_volume = float(sum(p["l"] * p["w"] * p["h"] for p in valid))
            packed_items = len(valid)
            volume_ratio = packed_volume / volume_bound if volume_bound > 0 else 0.0
            item_ratio = packed_items / total_items if total_items > 0 else 0.0
            score = max(0.0, min(1.0, 0.9 * volume_ratio + 0.1 * item_ratio))
            return {{
                "id": instance["id"],
                "split": instance.get("split", "public"),
                "score": score,
                "packed_volume": packed_volume,
                "volume_bound": volume_bound,
                "packed_items": packed_items,
                "total_items": total_items,
                "violations": violations[:10],
            }}


        start = time.time()
        try:
            program = load_program({os.path.abspath(program_path)!r})
            if not hasattr(program, "run"):
                print(json.dumps({{"error": "solution.py must define run(instances)"}}))
                sys.exit(0)
            instances = json.loads(INSTANCES)
            answer = program.run(copy.deepcopy(instances))
        except Exception as e:
            print(json.dumps({{"error": f"run() failed: {{type(e).__name__}}: {{e}}"}}))
            sys.exit(0)

        try:
            rows = []
            for i, instance in enumerate(instances):
                rows.append(evaluate_instance(instance, get_instance_answer(answer, i, instance["id"])))
        except Exception as e:
            print(json.dumps({{"error": f"could not evaluate returned solution: {{type(e).__name__}}: {{e}}"}}))
            sys.exit(0)

        total_score = sum(row["score"] for row in rows) / len(rows) if rows else 0.0
        out = {{
            "score": total_score,
            "eval_time": time.time() - start,
            "packed_volume": sum(row["packed_volume"] for row in rows),
            "volume_bound": sum(row["volume_bound"] for row in rows),
            "packed_items": sum(row["packed_items"] for row in rows),
            "total_items": sum(row["total_items"] for row in rows),
            "instances": rows,
        }}
        print(json.dumps(out))
        """
    )

    import subprocess

    proc = subprocess.run(
        [*python_cmd, "-c", script],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip()[-2000:])
    stdout = proc.stdout.strip()
    if not stdout:
        raise RuntimeError(f"Script produced no output. stderr: {proc.stderr.strip()[-1000:]}")
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        for line in reversed(stdout.splitlines()):
            line = line.strip()
            if line.startswith("{"):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
        raise RuntimeError(
            f"No valid JSON in output.\nstdout: {stdout[-500:]}\nstderr: {proc.stderr[-500:]}"
        )


def _mean(values: Any) -> float:
    vals = list(values)
    return sum(vals) / len(vals) if vals else 0.0

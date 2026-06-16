#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TASK_DIR="${TASK_DIR:-${REPO_ROOT}/bin_packing}"
TASK_DIR="$(cd "${TASK_DIR}" && pwd)"

TARGET_EVALS="${TARGET_EVALS:-100}"
MAX_PARALLEL_RUNS="${MAX_PARALLEL_RUNS:-6}"
TASK_SLUG="bin-packing"

for config in task.yaml task.no_knowledge.yaml task.no_heartbeats.yaml task.structured.yaml; do
  if [[ ! -f "${TASK_DIR}/${config}" ]]; then
    echo "Missing ${TASK_DIR}/${config}" >&2
    exit 1
  fi
done

run_one() {
  local condition="$1"
  local config="$2"
  local rep="$3"

  local run_id="${rep}"
  local task_name="${TASK_SLUG}.${condition}"
  local run_dir="./results/${task_name}/${run_id}"
  local coral_dir="${run_dir}/.coral"
  local eval_count_file="${coral_dir}/public/eval_count"
  local log_file="${run_dir}/ablation_driver.log"

  mkdir -p "${run_dir}"

  {
    echo "=== Starting ${condition} rep ${rep} (${config}) ==="
    echo "target_evals=${TARGET_EVALS}"
    echo "run_dir=${run_dir}"

    if ! coral start -c "${TASK_DIR}/${config}" \
      "workspace.run_dir=${run_dir}" \
      "run.session=tmux"; then
      echo "coral start failed for ${condition} rep ${rep}"
      exit 1
    fi

    echo "Waiting for ${TARGET_EVALS} evals..."

    while true; do
      if [[ -f "${eval_count_file}" ]]; then
        count="$(cat "${eval_count_file}")"
      else
        count="0"
      fi

      echo "[$(date '+%F %T')] [${condition}/${rep}] evals=${count}/${TARGET_EVALS}"

      if [[ "${count}" =~ ^[0-9]+$ ]] && (( count >= TARGET_EVALS )); then
        break
      fi

      sleep 30
    done

    echo "Stopping ${condition} rep ${rep}"
    coral stop --task "${task_name}" --run "${run_id}" || true
    echo "=== Finished ${condition} rep ${rep} ==="
  } >"${log_file}" 2>&1
}

wait_for_slot() {
  while (( $(jobs -rp | wc -l | tr -d ' ') >= MAX_PARALLEL_RUNS )); do
    sleep 10
  done
}

launch() {
  wait_for_slot
  run_one "$1" "$2" "$3" &
  local active
  active="$(jobs -rp | wc -l | tr -d ' ')"
  echo "Launched $1 rep $3 (active driver jobs: ${active}/${MAX_PARALLEL_RUNS})"
  sleep 5
}

for rep in 1 2 3; do
  launch "full" "task.yaml" "${rep}"
done

for rep in 1 2 3; do
  launch "no_knowledge" "task.no_knowledge.yaml" "${rep}"
done

for rep in 1 2 3; do
  launch "no_heartbeats" "task.no_heartbeats.yaml" "${rep}"
done

for rep in 1 2 3; do
  launch "structured" "task.structured.yaml" "${rep}"
done

wait

echo
echo "=== Summary ==="

python3 - <<'PY'
import json
import math
import os
import statistics
from pathlib import Path

root = "./results/bin-packing"
conditions = ["full", "no_knowledge", "no_heartbeats", "structured"]

for condition in conditions:
    scores = []
    for rep in range(1, 4):
        attempts_dir = Path(f"{root}.{condition}") / f"{rep}" / ".coral" / "public" / "attempts"
        best = None
        if attempts_dir.exists():
            for path in attempts_dir.glob("*.json"):
                try:
                    attempt = json.loads(path.read_text())
                except Exception:
                    continue
                score = attempt.get("score")
                budget_class = (attempt.get("metadata") or {}).get("budget_class", "real")
                if budget_class != "real":
                    continue
                if isinstance(score, (int, float)) and math.isfinite(score):
                    best = score if best is None else max(best, score)
        scores.append(best)

    valid = [score for score in scores if score is not None]
    mean = statistics.mean(valid) if valid else float("nan")
    std = statistics.stdev(valid) if len(valid) >= 2 else 0.0

    print(f"{condition:14s} runs={scores}  mean+-std={mean:.6f} +- {std:.6f}")
PY

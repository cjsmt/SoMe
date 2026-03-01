#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

if [[ -f ".env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

: "${OPENAI_BASE_URL:?OPENAI_BASE_URL is required (.env)}"
: "${OPENAI_API_KEY:?OPENAI_API_KEY is required (.env)}"
: "${LLM_MODEL_NAME:?LLM_MODEL_NAME is required (.env)}"

# Core controls
MAX_SAMPLES="${MAX_SAMPLES:-200}"
MAX_RETRIES="${MAX_RETRIES:-2}"
API_RETRY="${API_RETRY:-5}"
MODIFIED_TOPK="${MODIFIED_TOPK:-5}"
MODEL_NAME="$LLM_MODEL_NAME"
RUN_TAG="${RUN_TAG:-$(date "+%Y%m%d_%H%M%S")}"

mkdir -p logs results scores

timestamp() {
  date "+%Y-%m-%d %H:%M:%S"
}

safe_model_name() {
  local v="$1"
  v="${v//\//_}"
  v="${v// /_}"
  echo "$v"
}

assert_path_not_exists() {
  local p="$1"
  if [[ -e "$p" ]]; then
    echo "[$(timestamp)] ERROR: path already exists: $p"
    echo "[$(timestamp)] Use a different RUN_TAG to avoid overwrite."
    exit 1
  fi
}

run_and_eval() {
  local exp_name="$1"
  local model_name="$2"
  local output_dir="$3"
  local sample_count="$4"
  local retrieval_topk="${5:-}"

  local run_log="logs/${exp_name}_run.log"
  local eval_log="logs/${exp_name}_eval.log"
  local score_dir="scores/${exp_name}"

  echo "[$(timestamp)] ===== START ${exp_name} ====="
  echo "[$(timestamp)] model=${model_name}, samples=${sample_count}, retries=${MAX_RETRIES}, topk=${retrieval_topk:-default}"

  local run_cmd=(
    python3 test_misinformation_detection.py
    --model "$model_name"
    --base_url "$OPENAI_BASE_URL"
    --api_key "$OPENAI_API_KEY"
    --output_path "$output_dir"
    --max_samples "$sample_count"
    --max_retries "$MAX_RETRIES"
  )
  if [[ -n "$retrieval_topk" ]]; then
    run_cmd+=(--retrieval_topk "$retrieval_topk")
  fi

  mkdir -p "$output_dir" "$score_dir"
  "${run_cmd[@]}" | tee "$run_log"

  python3 eval_scripts/MID_extraction.py \
    --result_path "$output_dir" \
    --output_path "$score_dir" \
    --setting_path "eval_scripts/settings.json" \
    --api_retry "$API_RETRY" | tee "$eval_log"

  python3 - "$score_dir" "$exp_name" <<'PY'
import glob
import json
import os
import sys

score_dir = sys.argv[1]
exp_name = sys.argv[2]
gt = json.load(open("datasets/misinformation_detection/ground_truth.json", encoding="utf-8"))

records = []
for fp in sorted(glob.glob(os.path.join(score_dir, "*.json"))):
    pred = json.load(open(fp, encoding="utf-8"))
    n = len(pred)
    correct = sum(1 for k, v in pred.items() if k in gt and v == gt[k]["label"])
    acc = (correct / n * 100.0) if n else 0.0
    records.append({
        "experiment": exp_name,
        "file": os.path.basename(fp),
        "samples": n,
        "acc": round(acc, 4),
    })

summary_path = os.path.join(score_dir, "score_summary.json")
with open(summary_path, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print(json.dumps(records, ensure_ascii=False, indent=2))
PY

  echo "[$(timestamp)] ===== END ${exp_name} ====="
}

MODEL_SAFE="$(safe_model_name "$MODEL_NAME")"
BASE_EXP="mid_${MODEL_SAFE}_${RUN_TAG}_baseline"
MOD_EXP="mid_${MODEL_SAFE}_${RUN_TAG}_modified_topk${MODIFIED_TOPK}"

BASE_RESULT_DIR="results/${BASE_EXP}"
BASE_SCORE_DIR="scores/${BASE_EXP}"
MOD_RESULT_DIR="results/${MOD_EXP}"
MOD_SCORE_DIR="scores/${MOD_EXP}"

assert_path_not_exists "$BASE_RESULT_DIR"
assert_path_not_exists "$BASE_SCORE_DIR"
assert_path_not_exists "$MOD_RESULT_DIR"
assert_path_not_exists "$MOD_SCORE_DIR"

# 1) Baseline (current LLM_MODEL_NAME)
run_and_eval "$BASE_EXP" "$MODEL_NAME" "$BASE_RESULT_DIR" "$MAX_SAMPLES"

# 2) Modified (same model, controlled variable: retrieval_topk)
run_and_eval "$MOD_EXP" "$MODEL_NAME" "$MOD_RESULT_DIR" "$MAX_SAMPLES" "$MODIFIED_TOPK"

# Build global markdown summary
python3 - "$RUN_TAG" <<'PY'
import glob
import json
import os
import sys

run_tag = sys.argv[1]

rows = []
for fp in sorted(glob.glob("scores/*/score_summary.json")):
    if run_tag not in fp:
        continue
    data = json.load(open(fp, encoding="utf-8"))
    for item in data:
        rows.append(item)

rows.sort(key=lambda x: x["experiment"])

md_lines = [
    "# MID Overnight Summary",
    "",
    "| Experiment | File | Samples | ACC |",
    "|---|---|---:|---:|",
]
for r in rows:
    md_lines.append(f"| {r['experiment']} | {r['file']} | {r['samples']} | {r['acc']:.4f} |")

os.makedirs("results", exist_ok=True)
summary_path = f"results/mid_overnight_summary_{run_tag}.md"
with open(summary_path, "w", encoding="utf-8") as f:
    f.write("\n".join(md_lines) + "\n")

print(f"Wrote {summary_path}")
PY

echo "[$(timestamp)] All configured experiments completed."
echo "Model: $MODEL_NAME"
echo "Baseline results: $BASE_RESULT_DIR"
echo "Modified results: $MOD_RESULT_DIR"
echo "Summary: results/mid_overnight_summary_${RUN_TAG}.md"

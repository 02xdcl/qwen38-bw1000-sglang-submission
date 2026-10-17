#!/usr/bin/env bash
set -Eeuo pipefail

BASE=/public/home/zzu_dcf/qwen38_dcu_competition
SGENV=/public/home/zzu_dcf/sglang
MODEL="$BASE/models/Qwen3.8-27B"
DATASET="$BASE/dataset/ShareGPT_V3_unfiltered_cleaned_split.json"
DIR="$BASE/results/sglang_bf16_sharegpt_893107"

module load compiler/dtk/26.04

echo "START: $(date)"
echo "NODE: $(hostname)"

curl -fsS --max-time 10 \
  http://127.0.0.1:18580/v1/models >/dev/null

for C in 1 4 16 32 64; do
    LOG="$DIR/c${C}_run1.log"
    JSON="$DIR/c${C}_run1.jsonl"

    if [ -s "$LOG" ] && [ -s "$JSON" ] &&
       grep -q "Serving Benchmark Result" "$LOG" &&
       grep -Eq '^Successful requests:[[:space:]]*1000[[:space:]]*$' "$LOG"; then
        echo "C${C} already completed, skipping"
        continue
    fi

    TS=$(date +%Y%m%d_%H%M%S)
    [ ! -e "$LOG" ] || mv "$LOG" "${LOG}.incomplete_${TS}"
    [ ! -e "$JSON" ] || mv "$JSON" "${JSON}.incomplete_${TS}"

    COMMON=(
      "$SGENV/bin/python" -m sglang.bench_serving
      --backend sglang-oai-chat
      --host 127.0.0.1
      --port 18580
      --dataset-name sharegpt
      --dataset-path "$DATASET"
      --model "$MODEL"
      --served-model-name qwen38-bf16
      --tokenizer "$MODEL"
      --request-rate inf
      --max-concurrency "$C"
    )

    echo "===== C${C} WARMUP: $(date) ====="

    WN=32
    if [ "$C" -gt 32 ]; then WN="$C"; fi

    "${COMMON[@]}" \
      --num-prompts "$WN" \
      > "$DIR/c${C}_warmup.log" 2>&1

    echo "===== C${C} FORMAL START: $(date) ====="

    "${COMMON[@]}" \
      --num-prompts 1000 \
      --output-file "$JSON" \
      > "$LOG" 2>&1

    test -s "$JSON"
    grep -q "Serving Benchmark Result" "$LOG"
    grep -Eq '^Successful requests:[[:space:]]*1000[[:space:]]*$' "$LOG"

    echo "===== C${C} SUCCESS: $(date) ====="
done

echo "ALL SHAREGPT TESTS COMPLETED: $(date)"

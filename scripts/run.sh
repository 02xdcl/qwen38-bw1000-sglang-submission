#!/usr/bin/env bash
set -Eeuo pipefail

BASE=/public/home/zzu_dcf/qwen38_dcu_competition
SGENV=/public/home/zzu_dcf/sglang
PY="$SGENV/bin/python"
MODEL="$BASE/models/Qwen3.8-27B"
DATASET="$BASE/dataset/ShareGPT_V3_unfiltered_cleaned_split.json"

OUT="$BASE/results/sharegpt_retest_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUT"

module load compiler/dtk/26.04

export PATH="$SGENV/bin:$PATH"
export AILLVM_HOME="$BASE/toolchain/aillvm"
export TRITON_HIP_CLANG_PATH="$AILLVM_HOME/bin/clang-18"
export SGLANG_USE_AITER_LINEAR_ATTN=false
export SGLANG_ROCM_USE_AITER_MOE=false
export SGLANG_KV_LAYOUT_HCU_FA=false
export HSA_FORCE_FINE_GRAIN_PCIE=1
export OMP_NUM_THREADS=8

for f in "$PY" "$MODEL" "$DATASET" "$TRITON_HIP_CLANG_PATH"; do
    test -e "$f" || { echo "Missing: $f"; exit 1; }
done

if curl -fsS --max-time 2 \
    http://127.0.0.1:18580/v1/models >/dev/null 2>&1; then
    echo "ERROR: Port 18580 already has a server"
    exit 1
fi

SERVER_PID=""

cleanup() {
    if [[ -n "$SERVER_PID" ]]; then
        kill -TERM -- "-$SERVER_PID" 2>/dev/null || true
        sleep 8
        kill -KILL -- "-$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
        SERVER_PID=""
    fi
}
trap cleanup EXIT

echo "OUTPUT_DIR=$OUT"
echo "NODE=$(hostname)"
echo "START=$(date)"

setsid "$PY" -u -m sglang.launch_server \
    --model-path "$MODEL" \
    --served-model-name qwen38-bf16 \
    --host 127.0.0.1 \
    --port 18580 \
    --tp-size 2 \
    --dtype bfloat16 \
    --context-length 131072 \
    --max-running-requests 128 \
    --chunked-prefill-size 8192 \
    --max-prefill-tokens 16384 \
    --schedule-conservativeness 0.4 \
    --mem-fraction-static 0.85 \
    --attention-backend triton \
    --disable-custom-all-reduce \
    --disable-piecewise-cuda-graph \
    --trust-remote-code \
    > "$OUT/server.log" 2>&1 &

SERVER_PID=$!

echo "Waiting for server..."

READY=0
for i in $(seq 1 180); do
    if curl -fsS --max-time 3 \
        http://127.0.0.1:18580/v1/models \
        >/dev/null 2>&1; then
        READY=1
        break
    fi

    if ! kill -0 "$SERVER_PID" 2>/dev/null; then
        echo "ERROR: Server exited"
        tail -80 "$OUT/server.log"
        exit 1
    fi
    sleep 5
done

if [[ "$READY" != 1 ]]; then
    echo "ERROR: Server startup timeout"
    tail -80 "$OUT/server.log"
    exit 1
fi

echo "SERVER READY"

for C in 1 4 16 32 64; do
    echo "========== C=$C =========="

    COMMON=(
        "$PY" -m sglang.bench_serving
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

    WN=32
    if (( C > 32 )); then WN="$C"; fi

    echo "Warmup C=$C"
    "${COMMON[@]}" \
        --num-prompts "$WN" \
        > "$OUT/c${C}_warmup.log" 2>&1

    echo "Formal C=$C"
    "${COMMON[@]}" \
        --num-prompts 1000 \
        --output-file "$OUT/c${C}_run1.jsonl" \
        > "$OUT/c${C}_run1.log" 2>&1

    LOG="$OUT/c${C}_run1.log"
    test -s "$OUT/c${C}_run1.jsonl"
    grep -q "Serving Benchmark Result" "$LOG"
    grep -Eq '^Successful requests:[[:space:]]*1000[[:space:]]*$' "$LOG"

    grep -E \
      'Successful requests:|Request throughput|Output token throughput|P99 E2E Latency|Mean TTFT|Mean TPOT' \
      "$LOG"

    echo "PASS C=$C"
done

echo "ALL SHAREGPT RETESTS FINISHED"
echo "OUTPUT_DIR=$OUT"

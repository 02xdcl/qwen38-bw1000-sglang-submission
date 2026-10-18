#!/usr/bin/env bash
set -Eeuo pipefail

BASE=/public/home/zzu_dcf/qwen38_dcu_competition
SGENV=/public/home/zzu_dcf/sglang
PY="$SGENV/bin/python"
MODEL="$BASE/models/Qwen3.8-27B"
DATASET="$BASE/dataset/ShareGPT_V3_unfiltered_cleaned_split.json"
KERNEL="$SGENV/lib/python3.10/site-packages/sglang/srt/layers/attention/fla/fused_recurrent.py"
BASELINE="$BASE/experiments/A2_gdn_reorder/fused_recurrent_baseline.py"

module load compiler/dtk/26.04

# 只让本进程使用 HCU 2、3
unset ROCR_VISIBLE_DEVICES
unset CUDA_VISIBLE_DEVICES
export HIP_VISIBLE_DEVICES=2,3

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

# 再次确认目标 Kernel 与原版备份完全一致
cmp -s "$KERNEL" "$BASELINE" || {
    echo "ERROR: Kernel 与原版备份不一致，停止测试"
    exit 2
}

OUT="$BASE/results/sharegpt_baseline_envfix_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUT"
exec > >(tee -a "$OUT/controller.log") 2>&1

echo "OUTPUT_DIR=$OUT"
echo "NODE=$(hostname)"
echo "START=$(date)"
echo "HIP_VISIBLE_DEVICES=$HIP_VISIBLE_DEVICES"
echo "ROCR_VISIBLE_DEVICES=${ROCR_VISIBLE_DEVICES:-unset}"
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"

cp -p "$KERNEL" "$OUT/fused_recurrent.py"
cp -p "${BASH_SOURCE[0]}" "$OUT/run.sh"

{
    echo "START=$(date)"
    echo "NODE=$(hostname)"
    echo "HIP_VISIBLE_DEVICES=$HIP_VISIBLE_DEVICES"
    echo "KERNEL_SHA256:"
    sha256sum "$KERNEL" "$BASELINE" "$OUT/fused_recurrent.py"
    echo "MODULES:"
    module list 2>&1 || true
    echo "DCU_STATUS:"
    /opt/hyhal/bin/hy-smi || true
} > "$OUT/environment.txt"

# 不覆盖或占用已有的 18581 服务
if ss -ltnH 2>/dev/null |
   awk '$4 ~ /:18581$/ {found=1} END {exit !found}'; then
    echo "ERROR: Port 18581 is occupied; stop before launching"
    exit 3
fi

SERVER_PID=""

cleanup() {
    if [[ -n "${SERVER_PID:-}" ]]; then
        kill -TERM -- "-$SERVER_PID" 2>/dev/null ||
            kill -TERM "$SERVER_PID" 2>/dev/null || true
        sleep 8
        kill -KILL -- "-$SERVER_PID" 2>/dev/null ||
            kill -KILL "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
        SERVER_PID=""
    fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

echo "========== START ORIGINAL-KERNEL SERVER =========="

setsid "$PY" -u -m sglang.launch_server \
    --model-path "$MODEL" \
    --served-model-name qwen38-bf16 \
    --host 127.0.0.1 \
    --port 18581 \
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
echo "SERVER_PID=$SERVER_PID"

READY=0
for i in $(seq 1 180); do
    if curl -fsS --max-time 3 \
        http://127.0.0.1:18581/v1/models >/dev/null 2>&1; then
        READY=1
        break
    fi

    if ! kill -0 "$SERVER_PID" 2>/dev/null; then
        echo "ERROR: Server exited during startup"
        tail -100 "$OUT/server.log" || true
        exit 4
    fi
    sleep 5
done

if [[ "$READY" != 1 ]]; then
    echo "ERROR: Server startup timeout"
    tail -100 "$OUT/server.log" || true
    exit 5
fi

echo "SERVER READY: $(date)"

for C in 1 4 16 32 64; do
    echo "========== C=$C START $(date) =========="

    COMMON=(
        "$PY" -m sglang.bench_serving
        --backend sglang-oai-chat
        --host 127.0.0.1
        --port 18581
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

    echo "WARMUP C=$C $(date)"
    "${COMMON[@]}" \
        --num-prompts "$WN" \
        > "$OUT/c${C}_warmup.log" 2>&1

    echo "FORMAL C=$C $(date)"
    "${COMMON[@]}" \
        --num-prompts 1000 \
        --output-file "$OUT/c${C}_run1.jsonl" \
        > "$OUT/c${C}_run1.log" 2>&1

    LOG="$OUT/c${C}_run1.log"
    JSON="$OUT/c${C}_run1.jsonl"

    if [[ ! -s "$JSON" ]] ||
       ! grep -q "Serving Benchmark Result" "$LOG" ||
       ! grep -Eq '^Successful requests:[[:space:]]*1000[[:space:]]*$' "$LOG"; then
        echo "FAIL C=$C; inspect $LOG"
        tail -100 "$LOG" || true
        exit 6
    fi

    grep -E \
      'Successful requests:|Total input tokens:|Total generated tokens:|Request throughput|Output token throughput|Peak output token throughput|P99 E2E Latency|Mean TTFT|Mean TPOT' \
      "$LOG" || true

    echo "PASS C=$C $(date)"
done

echo "========== ALL FIVE SHAREGPT TESTS PASSED =========="
echo "END=$(date)"
/opt/hyhal/bin/hy-smi >> "$OUT/environment.txt" 2>&1 || true

# 停止本脚本启动的服务，不碰 18580
cleanup

(
    cd "$OUT"
    sha256sum controller.log environment.txt server.log \
        run.sh fused_recurrent.py \
        c*_warmup.log c*_run1.log c*_run1.jsonl
) > "$OUT/sha256sums.txt"

echo "FINAL_OUTPUT_DIR=$OUT"
echo "SHA256_MANIFEST=$OUT/sha256sums.txt"

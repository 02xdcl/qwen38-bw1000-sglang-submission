#!/usr/bin/env bash
set -Eeuo pipefail

BASE=/public/home/zzu_dcf/qwen38_dcu_competition
SGENV=/public/home/zzu_dcf/sglang
PY="$SGENV/bin/python"
MODEL="$BASE/models/Qwen3.8-27B"
OUT="$BASE/experiments/A13_decode_tuning"

mkdir -p "$OUT"

export PATH="$SGENV/bin:$PATH"
export AILLVM_HOME="$BASE/toolchain/aillvm"
export TRITON_HIP_CLANG_PATH="$AILLVM_HOME/bin/clang-18"
export SGLANG_USE_AITER_LINEAR_ATTN=false
export SGLANG_ROCM_USE_AITER_MOE=false
export SGLANG_KV_LAYOUT_HCU_FA=false
export HSA_FORCE_FINE_GRAIN_PCIE=1
export OMP_NUM_THREADS=8

test -x "$TRITON_HIP_CLANG_PATH" || {
    echo "ERROR: AI LLVM not executable"
    exit 1
}

if curl -fsS --max-time 3 \
    http://127.0.0.1:18580/v1/models >/dev/null 2>&1; then
    echo "ERROR: Port 18580 already has a server"
    exit 1
fi

PID=""

stop_server() {
    if [[ -n "$PID" ]]; then
        kill -TERM -- "-$PID" 2>/dev/null || true
        sleep 8
        kill -KILL -- "-$PID" 2>/dev/null || true
        wait "$PID" 2>/dev/null || true
        PID=""
    fi
}

trap stop_server EXIT

run_case() {
    local tag="$1"
    shift

    echo "========== Starting $tag =========="

    setsid "$PY" -u -m sglang.launch_server \
        --model-path "$MODEL" \
        --served-model-name qwen38-bf16 \
        --host 127.0.0.1 \
        --port 18580 \
        --tp-size 2 \
        --dtype bfloat16 \
        --context-length 131072 \
        --max-running-requests 128 \
        --chunked-prefill-size "${CHUNK_SIZE:-8192}" \
        --max-prefill-tokens 16384 \
        --mem-fraction-static 0.85 \
        --attention-backend triton \
        --disable-custom-all-reduce \
        --disable-piecewise-cuda-graph \
        --trust-remote-code \
        "$@" \
        > "$OUT/server_${tag}.log" 2>&1 &

    PID=$!

    local ready=0
    for i in $(seq 1 180); do
        if curl -fsS --max-time 3 \
            http://127.0.0.1:18580/v1/models \
            >/dev/null 2>&1; then
            ready=1
            break
        fi

        if ! kill -0 "$PID" 2>/dev/null; then
            echo "ERROR: Server exited"
            tail -n 50 "$OUT/server_${tag}.log"
            return 1
        fi
        sleep 5
    done

    if [[ "$ready" != 1 ]]; then
        echo "ERROR: Server startup timeout"
        tail -n 50 "$OUT/server_${tag}.log"
        return 1
    fi

    echo "========== Benchmark $tag =========="

    "$PY" -u -m sglang.bench_serving \
        --backend sglang \
        --host 127.0.0.1 \
        --port 18580 \
        --model "$MODEL" \
        --tokenizer "$MODEL" \
        --dataset-name random --dataset-path "$BASE/dataset/ShareGPT_V3_unfiltered_cleaned_split.json" \
        --random-input-len 512 \
        --random-output-len 128 \
        --random-range-ratio 1.0 \
        --num-prompts 320 \
        --request-rate inf \
        --max-concurrency 64 \
        --seed 42 \
        --output-file "$OUT/result_${tag}.jsonl" \
        2>&1 | tee "$OUT/bench_${tag}.log"

    stop_server
    sleep 5
}

# 当前默认配置
guarded_case() {
    local tag="$1"
    local steps="$2"
    shift 2

    run_case "$tag" "$@"

    local log="$OUT/bench_${tag}.log"
    local serverlog="$OUT/server_${tag}.log"

    if [[ ! -s "$log" || ! -s "$serverlog" ]]; then
        echo "ERROR: Missing logs for $tag"
        exit 1
    fi

    if ! grep -Eq "num_continuous_decode_steps=${steps}([^0-9]|$)" "$serverlog"; then
        echo "ERROR: Decode parameter not applied: $tag"
        exit 1
    fi

    if grep -Eq 'HSA_STATUS_ERROR_EXCEPTION|KERNEL VMFault|Fatal Python error: Aborted' "$serverlog"; then
        echo "ERROR: GPU fault detected in $tag"
        exit 1
    fi

    if ! grep -Eq '^Successful requests:[[:space:]]+320[[:space:]]*$' "$log"; then
        echo "ERROR: Incomplete benchmark: $tag"
        exit 1
    fi

    if ! grep -Eq '^Total generated tokens:[[:space:]]+40960[[:space:]]*$' "$log"; then
        echo "ERROR: Unexpected output token count: $tag"
        exit 1
    fi

    echo "PASS: $tag"
}

CHUNK_SIZE=8192 guarded_case decode_1 1 --schedule-conservativeness 0.4 --num-continuous-decode-steps 1
CHUNK_SIZE=8192 guarded_case decode_2 2 --schedule-conservativeness 0.4 --num-continuous-decode-steps 2
CHUNK_SIZE=8192 guarded_case decode_4 4 --schedule-conservativeness 0.4 --num-continuous-decode-steps 4

# 只改变调度积极性

echo
echo "========== A13 FINISHED =========="
grep -Ei \
'throughput|mean ttft|median ttft|mean tpot|mean itl|p99' \
"$OUT"/bench_*.log || true

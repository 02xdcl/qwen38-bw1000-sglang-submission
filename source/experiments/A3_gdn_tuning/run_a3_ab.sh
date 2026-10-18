#!/usr/bin/env bash
set -Eeuo pipefail

[[ -n "${SLURM_JOB_ID:-}" ]] || {
    echo "ERROR: 必须在 Slurm 作业内运行"
    exit 1
}

BASE=/public/home/zzu_dcf/qwen38_dcu_competition
SGENV=/public/home/zzu_dcf/sglang
PY="$SGENV/bin/python"
A3="$BASE/experiments/A3_gdn_tuning"
MODEL="$BASE/models/Qwen3.8-27B"
DATASET="$BASE/dataset/ShareGPT_V3_unfiltered_cleaned_split.json"
RESULT="$BASE/results/a3_sharegpt_ab_${SLURM_JOB_ID}"
SRC="$SGENV/lib/python3.10/site-packages/sglang/srt/layers/attention/fla/fused_recurrent.py"

[[ "$(hostname)" == "a02r1n15" ]] || {
    echo "ERROR: 不是预期计算节点"
    exit 1
}

cmp -s "$SRC" "$A3/fused_recurrent_original.py" || {
    echo "ERROR: 正式 SGLang 源码已变化"
    exit 1
}

mkdir "$RESULT"

module load compiler/dtk/26.04

export AILLVM_HOME="$BASE/toolchain/aillvm"
export TRITON_HIP_CLANG_PATH="$AILLVM_HOME/bin/clang-18"
export SGLANG_USE_AITER_LINEAR_ATTN=false
export SGLANG_ROCM_USE_AITER_MOE=false
export SGLANG_KV_LAYOUT_HCU_FA=false
export HSA_FORCE_FINE_GRAIN_PCIE=1
export OMP_NUM_THREADS=8

WORK=$(mktemp -d "${SLURM_TMPDIR:-/tmp}/a3ab_${SLURM_JOB_ID}_XXXXXX")
export TMPDIR="$WORK/tmp"
export TRITON_CACHE_DIR="$WORK/triton_cache"

mkdir -p "$TMPDIR" "$TRITON_CACHE_DIR" "$WORK/site"

echo "========== 创建独立 SGLang 副本 =========="
cp -a \
  "$SGENV/lib/python3.10/site-packages/sglang" \
  "$WORK/site/sglang"

export PYTHONPATH="$WORK/site${PYTHONPATH:+:$PYTHONPATH}"

STAGED="$WORK/site/sglang/srt/layers/attention/fla/fused_recurrent.py"
SERVER_PID=""

stop_server() {
    if [[ -n "$SERVER_PID" ]]; then
        kill -TERM -- "-$SERVER_PID" 2>/dev/null || true

        for i in $(seq 1 25); do
            if ! kill -0 -- "-$SERVER_PID" 2>/dev/null; then
                break
            fi
            sleep 1
        done

        if kill -0 -- "-$SERVER_PID" 2>/dev/null; then
            kill -KILL -- "-$SERVER_PID" 2>/dev/null || true
        fi

        wait "$SERVER_PID" 2>/dev/null || true
        SERVER_PID=""
    fi
}

trap stop_server EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

echo "NODE=$(hostname)"
echo "JOBID=$SLURM_JOB_ID"
echo "HIP_VISIBLE_DEVICES=${HIP_VISIBLE_DEVICES:-未设置}"

"$PY" - <<'PY'
import os
import torch
import sglang

print("PyTorch:", torch.__version__)
print("DCU count:", torch.cuda.device_count())
print("SGLang path:", sglang.__file__)

assert torch.cuda.is_available()
assert torch.cuda.device_count() == 2
assert str(sglang.__file__).startswith(
    os.environ["PYTHONPATH"].split(":")[0]
)
PY

start_server() {
    local tag="$1"

    if curl -fsS --max-time 2 \
        http://127.0.0.1:18580/v1/models \
        >/dev/null 2>&1; then
        echo "ERROR: 18580 端口已有服务"
        return 1
    fi

    echo "========== 启动 $tag 服务 =========="

    setsid "$PY" -m sglang.launch_server \
      --model-path "$MODEL" \
      --served-model-name qwen38-bf16 \
      --host 0.0.0.0 \
      --port 18580 \
      --tp-size 2 \
      --dtype bfloat16 \
      --context-length 131072 \
      --max-running-requests 128 \
      --chunked-prefill-size 8192 \
      --max-prefill-tokens 16384 \
      --mem-fraction-static 0.85 \
      --attention-backend triton \
      --disable-custom-all-reduce \
      --disable-piecewise-cuda-graph \
      --trust-remote-code \
      > "$RESULT/server_${tag}.log" 2>&1 &

    SERVER_PID=$!

    local ready=0

    for i in $(seq 1 180); do
        if curl -fsS --max-time 3 \
           http://127.0.0.1:18580/v1/models \
           >/dev/null 2>&1; then
            ready=1
            break
        fi

        if ! kill -0 "$SERVER_PID" 2>/dev/null; then
            echo "ERROR: $tag 服务提前退出"
            tail -n 70 "$RESULT/server_${tag}.log"
            return 1
        fi

        sleep 5
    done

    if [[ "$ready" != 1 ]]; then
        echo "ERROR: $tag 服务启动超时"
        tail -n 70 "$RESULT/server_${tag}.log"
        return 1
    fi

    echo "SERVER $tag READY"
}

run_benchmark() {
    local tag="$1"

    for C in 4 32 64; do
        local WN=32
        if (( C > 32 )); then WN="$C"; fi

        COMMON=(
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

        echo "========== $tag C$C 预热 =========="

        "$PY" -m sglang.bench_serving \
          "${COMMON[@]}" \
          --num-prompts "$WN" \
          > "$RESULT/${tag}_c${C}_warmup.log" 2>&1

        echo "========== $tag C$C 正式测试 =========="

        "$PY" -m sglang.bench_serving \
          "${COMMON[@]}" \
          --num-prompts 200 \
          --output-file "$RESULT/${tag}_c${C}.jsonl" \
          > "$RESULT/${tag}_c${C}.log" 2>&1

        if ! grep -Eq \
          '^Successful requests:[[:space:]]*200[[:space:]]*$' \
          "$RESULT/${tag}_c${C}.log"; then
            echo "ERROR: $tag C$C 请求未全部成功"
            tail -n 70 "$RESULT/${tag}_c${C}.log"
            return 1
        fi

        grep -Ei \
          'Successful requests:|Output token throughput|Mean TTFT|Mean TPOT' \
          "$RESULT/${tag}_c${C}.log" || true
    done
}

echo "========== A 组：原版 Warp1 =========="
cp "$A3/fused_recurrent_original.py" "$STAGED"

start_server original
run_benchmark original
stop_server

echo "========== B 组：A3 Warp2 =========="
cp "$A3/fused_recurrent_bv32_w2.py" "$STAGED"

start_server warp2
run_benchmark warp2
stop_server

echo "A3 SHAREGPT AB FINISHED"
echo "RESULT=$RESULT"

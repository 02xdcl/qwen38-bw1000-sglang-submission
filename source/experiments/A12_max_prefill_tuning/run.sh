#!/usr/bin/env bash
set -Eeuo pipefail

BASE=/public/home/zzu_dcf/qwen38_dcu_competition
SGENV=/public/home/zzu_dcf/sglang
PY="$SGENV/bin/python"
MODEL="$BASE/models/Qwen3.8-27B"
DATASET="$BASE/dataset/ShareGPT_V3_unfiltered_cleaned_split.json"
OUT="$BASE/experiments/A12_max_prefill_tuning"
A11LOG="$BASE/experiments/A11_prefill_tuning/server_chunk_16384.log"

mkdir -p "$OUT"

export PATH="$SGENV/bin:$PATH"
export AILLVM_HOME="$BASE/toolchain/aillvm"
export TRITON_HIP_CLANG_PATH="$AILLVM_HOME/bin/clang-18"
export OMP_NUM_THREADS=8

# 从 A11 日志读取调度参数，避免改变其他变量
SCHED=$("$PY" - "$A11LOG" <<'PY'
import pathlib, re, sys
p = pathlib.Path(sys.argv[1])
s = p.read_text(errors="replace")
m = re.search(r"schedule_conservativeness=([0-9.]+)", s)
if not m:
    sys.exit("ERROR: Cannot determine A11 scheduling parameter")
print(m.group(1))
PY
)

for f in "$PY" "$TRITON_HIP_CLANG_PATH" "$DATASET"; do
    [[ -e "$f" ]] || { echo "Missing: $f"; exit 1; }
done

echo "A11 schedule_conservativeness=$SCHED"

SERVER_PID=""

stop_server() {
    if [[ -n "$SERVER_PID" ]]; then
        kill -TERM -- "-$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
        SERVER_PID=""
        sleep 5
    fi
}

trap stop_server EXIT

run_case() {
    local size="$1"
    local tag="prefill_${size}"

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
        --chunked-prefill-size 16384 \
        --max-prefill-tokens "$size" \
        --schedule-conservativeness "$SCHED" \
        --mem-fraction-static 0.85 \
        --attention-backend triton \
        --disable-custom-all-reduce \
        --disable-piecewise-cuda-graph \
        --trust-remote-code \
        > "$OUT/server_${tag}.log" 2>&1 &

    SERVER_PID=$!

    local ready=0
    for i in $(seq 1 180); do
        if curl -fsS --max-time 2 \
            http://127.0.0.1:18580/v1/models \
            >/dev/null 2>&1; then
            ready=1
            break
        fi
        if ! kill -0 "$SERVER_PID" 2>/dev/null; then
            break
        fi
        sleep 5
    done

    if [[ "$ready" != 1 ]]; then
        echo "ERROR: Server failed to start"
        tail -60 "$OUT/server_${tag}.log"
        return 1
    fi

    echo "========== Benchmark $tag =========="

    "$PY" -u -m sglang.bench_serving \
        --backend sglang \
        --host 127.0.0.1 \
        --port 18580 \
        --dataset-name random \
        --dataset-path "$DATASET" \
        --model "$MODEL" \
        --tokenizer "$MODEL" \
        --num-prompts 320 \
        --random-input-len 512 \
        --random-output-len 128 \
        --random-range-ratio 1.0 \
        --max-concurrency 64 \
        --seed 42 \
        --output-file "$OUT/result_${tag}.jsonl" \
        2>&1 | tee "$OUT/bench_${tag}.log"

    stop_server
}

# 防止误连接到其他已经运行的服务
if curl -fsS --max-time 2 \
    http://127.0.0.1:18580/v1/models >/dev/null 2>&1; then
    echo "ERROR: Port 18580 is already occupied"
    exit 1
fi

run_case 16384
run_case 24576
run_case 32768

echo "========== A12 FINISHED =========="

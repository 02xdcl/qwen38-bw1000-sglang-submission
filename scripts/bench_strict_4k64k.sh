#!/usr/bin/env bash
set -Eeuo pipefail

BASE=/public/home/zzu_dcf/qwen38_dcu_competition
SGENV=/public/home/zzu_dcf/sglang
PY="$SGENV/bin/python"
MODEL="$BASE/models/Qwen3.8-27B"
DATASET="$BASE/dataset/ShareGPT_V3_unfiltered_cleaned_split.json"

OUT="${1:?Usage: run_strict_4k64k.sh OUTPUT_DIR}"
mkdir -p "$OUT"
OUT="$(cd "$OUT" && pwd)"

export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

# 检查运行环境
[[ -n "${SLURM_JOB_ID:-}" ]] || {
    echo "ERROR: Not inside Slurm allocation"
    exit 1
}

[[ -x "$PY" && -d "$MODEL" && -s "$DATASET" ]] || {
    echo "ERROR: Python/model/dataset missing"
    exit 1
}

# 获取当前服务进程
mapfile -t PIDS < <(
    pgrep -f '[p]ython.*-m sglang.launch_server' || true
)

(( ${#PIDS[@]} == 1 )) || {
    echo "ERROR: Expected exactly one SGLang server"
    exit 1
}

PID="${PIDS[0]}"
SHA="$(sha256sum "/proc/$PID/cmdline" | awk '{print $1}')"
IDENTITY="$(hostname)|${SLURM_JOB_ID}|${PID}|${SHA}"

# 防止换节点后混用结果
if [[ -f "$OUT/identity.txt" ]]; then
    [[ "$(cat "$OUT/identity.txt")" == "$IDENTITY" ]] || {
        echo "ERROR: Node/job/server changed"
        exit 1
    }
else
    echo "$IDENTITY" > "$OUT/identity.txt"

    {
        echo "NODE=$(hostname)"
        echo "JOB=$SLURM_JOB_ID"
        echo "SERVER_PID=$PID"
        echo "START=$(date -Is)"

        echo "===== SERVER ARGS ====="
        tr '\0' '\n' < "/proc/$PID/cmdline"

        echo "===== OPTIMIZATION ENV ====="
        tr '\0' '\n' < "/proc/$PID/environ" |
          grep -E '^(SGLANG_|A8_GEMM_|HSA_|TRITON_|AILLVM_HOME=|OMP_NUM_THREADS=|PYTHONPATH=|CPLUS_INCLUDE_PATH=)' || true

        echo "===== SOFTWARE VERSIONS ====="
        "$PY" -m pip show sglang torch triton 2>/dev/null |
          grep -E '^(Name|Version):' || true

        echo "===== BENCHMARK SOURCE ====="
        sha256sum \
          "$SGENV/lib/python3.10/site-packages/sglang/bench_serving.py"

    } > "$OUT/provenance.txt"
fi

check_server() {
    kill -0 "$PID" 2>/dev/null || {
        echo "ERROR: Server exited"
        return 1
    }

    [[ "$(sha256sum "/proc/$PID/cmdline" |
        awk '{print $1}')" == "$SHA" ]] || {
        echo "ERROR: Server configuration changed"
        return 1
    }

    curl -fsS --max-time 10 \
      http://127.0.0.1:18580/v1/models |
      grep -Fq 'qwen38-bf16'
}

check_server

# 核对当前服务的关键模型参数
"$PY" - "$PID" "$MODEL" <<'PYVERIFY'
import pathlib
import sys

pid, model = sys.argv[1:]

args = [
    x.decode()
    for x in pathlib.Path(
        f"/proc/{pid}/cmdline"
    ).read_bytes().split(b"\0")
    if x
]

expected = {
    "--model-path": model,
    "--served-model-name": "qwen38-bf16",
    "--tp-size": "2",
    "--dtype": "bfloat16",
    "--context-length": "131072",
}

for flag, value in expected.items():
    if flag not in args:
        raise SystemExit(f"ERROR: Missing {flag}")

    actual = args[args.index(flag) + 1]

    if actual != value:
        raise SystemExit(
            f"ERROR: {flag}: {actual} != {value}"
        )

print("SERVER CONFIG CHECK PASS")
PYVERIFY

# 对照历史基线
for MODE in 4k 64k; do
    if [[ "$MODE" == 4k ]]; then
        INPUT=4096
        CS=(1 8 16 32 64 128)
        OLD="$BASE/results/sglang_bf16_4k_20261007_163756"
    else
        INPUT=65536
        CS=(1 8 16 32)
        OLD="$BASE/results/sglang_bf16_64k_20261007_201746"
    fi

    for C in "${CS[@]}"; do
        N=$((C == 1 ? 8 : C * 2))

        for TAG in warmup1 warmup2 run1 run2 run3; do
            F="$OLD/c${C}_${TAG}.log"

            [[ -s "$F" ]] || {
                echo "ERROR: Baseline log missing: $F"
                exit 1
            }

            for KEY in \
                "backend='sglang-oai-chat'" \
                "dataset_name='random'" \
                "dataset_path='$DATASET'" \
                "model='$MODEL'" \
                "tokenizer='$MODEL'" \
                "served_model_name='qwen38-bf16'" \
                "num_prompts=$N," \
                "random_input_len=$INPUT," \
                "random_output_len=1024," \
                "random_range_ratio=1.0," \
                "request_rate=inf," \
                "max_concurrency=$C," \
                "seed=1,"; do

                grep -Fq "$KEY" "$F" || {
                    echo "ERROR: Baseline mismatch"
                    echo "FILE=$F"
                    echo "PARAM=$KEY"
                    exit 1
                }
            done
        done
    done

    echo "BASELINE AUDIT PASSED: $MODE"
done

# 单轮测试
run_case() {
    local MODE="$1"
    local C="$2"
    local PHASE="$3"
    local R="$4"
    local INPUT="$5"

    local N=$((C == 1 ? 8 : C * 2))
    local TAG="${MODE}_c${C}_${PHASE}${R}"

    local LOG="$OUT/$TAG.log"
    local JSON="$OUT/$TAG.jsonl"
    local OK="$OUT/$TAG.ok"

    check_server

    # 已完成测试不重复
    if [[ -f "$OK" ]]; then
        [[ -s "$LOG" && -s "$JSON" ]] || {
            echo "ERROR: Completed result corrupted: $TAG"
            return 1
        }
        echo "SKIP: $TAG"
        return 0
    fi

    [[ ! -e "$LOG" && ! -e "$JSON" ]] || {
        echo "ERROR: Incomplete previous run: $TAG"
        return 1
    }

    echo "START $TAG $(date -Is)" |
      tee -a "$OUT/progress.txt"

    if "$PY" -m sglang.bench_serving \
      --backend sglang-oai-chat \
      --host 127.0.0.1 \
      --port 18580 \
      --dataset-name random \
      --dataset-path "$DATASET" \
      --model "$MODEL" \
      --served-model-name qwen38-bf16 \
      --tokenizer "$MODEL" \
      --num-prompts "$N" \
      --random-input-len "$INPUT" \
      --random-output-len 1024 \
      --random-range-ratio 1.0 \
      --request-rate inf \
      --max-concurrency "$C" \
      --seed 1 \
      --warmup-requests 1 \
      --output-file "$JSON" \
      > "$LOG" 2>&1; then
        :
    else
        echo "FAILED: $TAG"
        tail -50 "$LOG"
        return 1
    fi

    # 检查正式执行结果
    [[ -s "$JSON" ]] &&
    grep -Fq 'Serving Benchmark Result' "$LOG" &&
    grep -Eq \
      "^[[:space:]]*Successful requests:[[:space:]]*${N}[[:space:]]*$" \
      "$LOG" || {
        echo "INVALID RESULT: $TAG"
        tail -50 "$LOG"
        return 1
    }

    # 对照完整 Benchmark Namespace
    "$PY" - "$LOG" "$BASE" "$MODE" \
      "$C" "$PHASE" "$R" <<'PYCHECK'
import ast
import pathlib
import sys

new, base, mode, c, phase, r = sys.argv[1:]

directory = (
    "sglang_bf16_4k_20261007_163756"
    if mode == "4k"
    else "sglang_bf16_64k_20261007_201746"
)

old = (
    pathlib.Path(base)
    / "results"
    / directory
    / f"c{c}_{phase}{r}.log"
)

def extract(path):
    text = pathlib.Path(path).read_text(
        errors="replace"
    )

    for line in text.splitlines():
        if "benchmark_args=Namespace(" in line:
            expr = line.split(
                "benchmark_args=", 1
            )[1]

            tree = ast.parse(
                expr, mode="eval"
            ).body

            return {
                k.arg: ast.dump(k.value)
                for k in tree.keywords
            }

    raise ValueError(f"No benchmark args: {path}")

a = extract(old)
b = extract(new)

# 输出文件路径允许不同
a.pop("output_file", None)
b.pop("output_file", None)

if a != b:
    differences = [
        (k, a.get(k), b.get(k))
        for k in sorted(a.keys() | b.keys())
        if a.get(k) != b.get(k)
    ]

    raise SystemExit(
        f"CLIENT CONFIG MISMATCH: {differences[:20]}"
    )

print("COMPLETE CLIENT CONFIG MATCH")
PYCHECK

    check_server

    echo "PASS" > "$OK"

    echo "PASS $TAG $(date -Is)" |
      tee -a "$OUT/progress.txt"

    grep -E \
      'Successful requests:|Benchmark duration|Output token throughput|Mean TTFT|Mean TPOT' \
      "$LOG" || true
}

# 连续执行 4K -> 64K
for MODE in 4k 64k; do

    if [[ "$MODE" == 4k ]]; then
        INPUT=4096
        CS=(1 8 16 32 64 128)
    else
        INPUT=65536
        CS=(1 8 16 32)
    fi

    echo "======= START $MODE $(date -Is) =======" |
      tee -a "$OUT/progress.txt"

    for C in "${CS[@]}"; do

        # 与历史基线一致：预热两轮
        for R in 1 2; do
            run_case "$MODE" "$C" warmup "$R" "$INPUT"
        done

        # 与历史基线一致：正式三轮
        for R in 1 2 3; do
            run_case "$MODE" "$C" run "$R" "$INPUT"
        done

    done

    echo "======= COMPLETE $MODE $(date -Is) =======" |
      tee -a "$OUT/progress.txt"
done

echo "ALL 4K AND 64K TESTS PASSED $(date -Is)" |
  tee -a "$OUT/progress.txt"

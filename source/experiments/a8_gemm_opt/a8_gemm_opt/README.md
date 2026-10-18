# A8 targeted GEMM experiment: Qwen3.5-27B TP=2, BF16, Decode batch 32

## 0. Safe by design
This is an experimental Triton BF16 GEMM. It is NOT proven faster on BW DCU hardware. Benchmark gate `>=8%` faster per shape, numerical relative error <=3%, then opt-in. Changes to the SGLang source are disabled by default and backed up. Does not modify NCCL, weights or checkpoint.

Use an allocated **compute node**, with no active SGLang processes. `SGENV` points to `/public/home/zzu_dcf/sglang`.

## 1. Upload package and run microbenchmark

Unzip this package into `/public/home/zzu_dcf/qwen38_dcu_competition/experiments/A8_gemm_opt` via VSCode remote, or copy from your local PC with scp (replace local path).

```bash
export BASE=/public/home/zzu_dcf/qwen38_dcu_competition
export SGENV=/public/home/zzu_dcf/sglang
export A8="$BASE/experiments/A8_gemm_opt"
export SGROOT="$SGENV/lib/python3.10/site-packages/sglang/srt"
cd "$A8"
# This stage does NOT change SGLang.
timeout 300s "$SGENV/bin/python" -u a8_bench.py 2>&1 | tee bench.log
cat choice.json
```

If choices is `{}`, **stop A8**: this kernel cannot outperform BLAS, do NOT patch. Return benchmark result and focus on TP0 CPU inter-step host gap (~8ms).

## 2. Only if non-empty choice.json

```bash
# stop model server first; changes to installed SGLang affect all processes using this venv
"$SGENV/bin/python" a8_patch.py "$SGROOT/layers/quantization/unquant.py" install
# Baseline: launch the original server normally, without A8_GEMM_ENABLE.
# Candidate: launch your identical server command with the following environment:
export PYTHONPATH="$A8:${PYTHONPATH:-}"
export A8_GEMM_ENABLE=1
# Now run the EXACT SAME original SGLang launch command, TP2, model, benchmark sharegpt etc.
# Compare at least 3 runs per variant, with correct output, TTFT/ITL and total throughput.
```

NOTE: if compiler fails during model load, stop the candidate process and rollback. Do NOT launch baseline and candidate concurrently on the same DCUs.

## 3. Restore original SGLang

```bash
unset A8_GEMM_ENABLE
"$SGENV/bin/python" "$A8/a8_patch.py" "$SGROOT/layers/quantization/unquant.py" restore
```

## Important caveat
TP0/TP1 A5 trace indicates significant pre-first-NCCL rank skew and TP1 waiting. Even a faster kernel might not improve end-to-end until TP0 host scheduling delays are addressed. Microbenchmark improvement is necessary but not sufficient.

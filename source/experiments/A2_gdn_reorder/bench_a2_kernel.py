import torch
import statistics
import importlib.util
import sys

from sglang.srt.layers.attention.fla import fused_recurrent as a2

backup = (
    "/public/home/zzu_dcf/qwen38_dcu_competition/"
    "experiments/A2_gdn_reorder/fused_recurrent_baseline.py"
)

spec = importlib.util.spec_from_file_location(
    "a2_original_benchmark", backup
)
original = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = original
spec.loader.exec_module(original)

assert torch.cuda.is_available(), "DCU unavailable"

H = HV = 4
K = V = 128
device = "cuda"

def benchmark(fn, B, mixed, a, b, A_log, dt_bias, base_state, indices):
    measurements = []

    for repeat in range(3):
        state = base_state.clone()
        out = torch.empty(
            B, 1, HV, V,
            device=device, dtype=torch.bfloat16
        )

        def call():
            fn(
                mixed_qkv=mixed,
                a=a,
                b=b,
                A_log=A_log,
                dt_bias=dt_bias,
                scale=K ** -0.5,
                initial_state=state,
                out=out,
                ssm_state_indices=indices,
                use_qk_l2norm_in_kernel=True,
            )

        # Warmup and JIT compilation
        for _ in range(10):
            call()
        torch.cuda.synchronize()

        start = torch.cuda.Event(enable_timing=True)
        end = torch.cuda.Event(enable_timing=True)

        start.record()
        for _ in range(100):
            call()
        end.record()
        end.synchronize()

        measurements.append(
            start.elapsed_time(end) * 1000 / 100
        )

    return statistics.median(measurements)

print("========== A2 Kernel Benchmark ==========", flush=True)
print("Unit: microseconds per invocation", flush=True)

for B in [4, 16, 64]:
    torch.manual_seed(42 + B)

    mixed = torch.randn(
        B, 2 * H * K + HV * V,
        device=device, dtype=torch.bfloat16
    )
    a = torch.randn(B, HV, device=device, dtype=torch.bfloat16)
    b = torch.randn(B, HV, device=device, dtype=torch.bfloat16)

    A_log = torch.zeros(HV, device=device)
    dt_bias = torch.zeros(HV, device=device)

    state = torch.randn(
        B + 1, HV, V, K,
        device=device
    ) * 0.01

    indices = torch.arange(B, device=device, dtype=torch.int32)

    old_us = benchmark(
        original.fused_recurrent_gated_delta_rule_packed_decode,
        B, mixed, a, b, A_log, dt_bias, state, indices
    )

    new_us = benchmark(
        a2.fused_recurrent_gated_delta_rule_packed_decode,
        B, mixed, a, b, A_log, dt_bias, state, indices
    )

    speedup = old_us / new_us

    print(f"\nBatch = {B}", flush=True)
    print(f"Original: {old_us:.3f} us", flush=True)
    print(f"A2:       {new_us:.3f} us", flush=True)
    print(f"Speedup:  {speedup:.3f}x", flush=True)

print("\nBenchmark finished.", flush=True)

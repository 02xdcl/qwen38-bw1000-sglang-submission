import torch
import statistics
import importlib.util
import sys
import traceback

BACKUP = (
    "/public/home/zzu_dcf/qwen38_dcu_competition/"
    "experiments/A2_gdn_reorder/fused_recurrent_baseline.py"
)

GRAPH_ITERS = 64
REPEATS = 15

def load_original():
    spec = importlib.util.spec_from_file_location(
        "a2_graph_original", BACKUP
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod

def build_graph(fn, data):
    mixed, a, b, A_log, dt_bias, initial, indices = data

    B = mixed.shape[0]
    HV = a.shape[1]
    K = 128
    V = 128

    state = initial.clone()
    out = torch.empty(
        (B, 1, HV, V),
        device="cuda",
        dtype=torch.bfloat16
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

    # 提前编译并执行 Kernel
    stream = torch.cuda.Stream()
    stream.wait_stream(torch.cuda.current_stream())

    with torch.cuda.stream(stream):
        for _ in range(3):
            call()

    torch.cuda.current_stream().wait_stream(stream)
    torch.cuda.synchronize()

    # 捕获多个 Kernel 调用，摊薄 Python 发射开销
    graph = torch.cuda.CUDAGraph()

    with torch.cuda.graph(graph):
        for _ in range(GRAPH_ITERS):
            call()

    torch.cuda.synchronize()

    return graph, state, initial

def measure(graph, state, initial):
    # 恢复状态，避免不同轮次初始状态不一致
    state.copy_(initial)
    torch.cuda.synchronize()

    start = torch.cuda.Event(enable_timing=True)
    end = torch.cuda.Event(enable_timing=True)

    start.record()
    graph.replay()
    end.record()

    end.synchronize()

    return start.elapsed_time(end) * 1000 / GRAPH_ITERS

def main():
    assert torch.cuda.is_available(), "DCU unavailable"

    from sglang.srt.layers.attention.fla import fused_recurrent as a2
    original = load_original()

    print("========== A2 HIP Graph Benchmark ==========", flush=True)
    print("Graph iterations:", GRAPH_ITERS, flush=True)
    print("Measurements:", REPEATS, flush=True)
    print("Unit: microseconds per kernel", flush=True)

    for B in [4, 16, 64]:
        torch.manual_seed(42 + B)

        HV = H = 4
        K = V = 128
        device = "cuda"

        mixed = torch.randn(
            B, 2 * H * K + HV * V,
            device=device, dtype=torch.bfloat16
        )

        a = torch.randn(
            B, HV, device=device, dtype=torch.bfloat16
        )
        b = torch.randn(
            B, HV, device=device, dtype=torch.bfloat16
        )

        A_log = torch.zeros(HV, device=device)
        dt_bias = torch.zeros(HV, device=device)

        initial = torch.randn(
            B + 1, HV, V, K, device=device
        ) * 0.01

        indices = torch.arange(
            B, device=device, dtype=torch.int32
        )

        data = (
            mixed, a, b, A_log,
            dt_bias, initial, indices
        )

        old_graph = build_graph(
            original.fused_recurrent_gated_delta_rule_packed_decode,
            data
        )

        new_graph = build_graph(
            a2.fused_recurrent_gated_delta_rule_packed_decode,
            data
        )

        old_samples = []
        new_samples = []

        # 交替测试，减小测试顺序带来的偏差
        for i in range(REPEATS):
            if i % 2 == 0:
                order = [("old", old_graph), ("new", new_graph)]
            else:
                order = [("new", new_graph), ("old", old_graph)]

            for label, (graph, state, seed) in order:
                us = measure(graph, state, seed)

                if label == "old":
                    old_samples.append(us)
                else:
                    new_samples.append(us)

        old_us = statistics.median(old_samples)
        new_us = statistics.median(new_samples)

        speedup = old_us / new_us

        print(f"\n========== Batch {B} ==========", flush=True)
        print(f"Original median: {old_us:.3f} us", flush=True)
        print(f"A2 median:       {new_us:.3f} us", flush=True)
        print(f"Speedup:         {speedup:.4f}x", flush=True)
        print(
            f"Original range:  {min(old_samples):.3f} - "
            f"{max(old_samples):.3f} us",
            flush=True
        )
        print(
            f"A2 range:        {min(new_samples):.3f} - "
            f"{max(new_samples):.3f} us",
            flush=True
        )

    print("\nGRAPH BENCHMARK FINISHED", flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)

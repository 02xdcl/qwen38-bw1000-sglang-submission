#!/usr/bin/env python3
import argparse
import importlib.util
import statistics
import sys
import traceback
from pathlib import Path

import torch

BASE = Path("/public/home/zzu_dcf/qwen38_dcu_competition")
A3 = BASE / "experiments/A3_gdn_tuning"

VARIANTS = {
    "original": "fused_recurrent_original.py",
    "bv32_w1": "fused_recurrent_bv32_w1.py",
    "bv16_w1": "fused_recurrent_bv16_w1.py",
    "bv64_w1": "fused_recurrent_bv64_w1.py",
    "bv32_w2": "fused_recurrent_bv32_w2.py",
    "bv32_w4": "fused_recurrent_bv32_w4.py",
}

BATCHES = (4, 16, 64)
H, HV, K, V = 8, 24, 128, 128

GRAPH_ITERS = 64
REPEATS = 15


def load_variant(name, filename):
    path = A3 / filename
    spec = importlib.util.spec_from_file_location(
        f"a3_module_{name}", path
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)

    if mod._use_decode_aiter_linear_attn:
        raise RuntimeError(
            "AITER 已启用，当前测试需要 Triton Kernel"
        )

    return mod.fused_recurrent_gated_delta_rule_packed_decode


def make_data(batch):
    torch.manual_seed(42 + batch)

    return {
        "mixed": torch.randn(
            batch, 2 * H * K + HV * V,
            device="cuda", dtype=torch.bfloat16
        ),
        "a": torch.randn(
            batch, HV, device="cuda", dtype=torch.bfloat16
        ),
        "b": torch.randn(
            batch, HV, device="cuda", dtype=torch.bfloat16
        ),
        "A_log": torch.zeros(
            HV, device="cuda", dtype=torch.float32
        ),
        "dt_bias": torch.zeros(
            HV, device="cuda", dtype=torch.float32
        ),
        "initial": torch.randn(
            batch + 1, HV, V, K,
            device="cuda", dtype=torch.float32
        ) * 0.01,
        "indices": torch.arange(
            batch, device="cuda", dtype=torch.int32
        ),
    }


def launch(fn, d, state, out):
    fn(
        mixed_qkv=d["mixed"],
        a=d["a"],
        b=d["b"],
        A_log=d["A_log"],
        dt_bias=d["dt_bias"],
        scale=K ** -0.5,
        initial_state=state,
        out=out,
        ssm_state_indices=d["indices"],
        use_qk_l2norm_in_kernel=True,
    )


def check_one(ref, candidate, batch):
    d = make_data(batch)

    s0 = d["initial"].clone()
    s1 = d["initial"].clone()

    o0 = torch.empty(
        batch, 1, HV, V,
        device="cuda", dtype=torch.bfloat16
    )
    o1 = torch.empty_like(o0)

    max_out = 0.0
    max_state = 0.0

    # 连续更新 8 个 Token，检查误差是否累积
    for step in range(8):
        if step:
            d["mixed"].normal_()
            d["a"].normal_()
            d["b"].normal_()

        launch(ref, d, s0, o0)
        launch(candidate, d, s1, o1)
        torch.cuda.synchronize()

        eo = (o0.float() - o1.float()).abs().max().item()
        es = (s0.float() - s1.float()).abs().max().item()

        max_out = max(max_out, eo)
        max_state = max(max_state, es)

        valid = (
            torch.isfinite(o1).all().item()
            and torch.isfinite(s1).all().item()
            and torch.allclose(
                o0.float(), o1.float(),
                atol=0.02, rtol=0.02
            )
            and torch.allclose(
                s0.float(), s1.float(),
                atol=0.005, rtol=0.005
            )
        )

        if not valid:
            raise AssertionError(
                f"Token {step + 1} 数值不一致: "
                f"output={eo}, state={es}"
            )

    return max_out, max_state


def build_graph(fn, d):
    state = d["initial"].clone()

    out = torch.empty(
        d["mixed"].shape[0], 1, HV, V,
        device="cuda", dtype=torch.bfloat16
    )

    stream = torch.cuda.Stream()
    stream.wait_stream(torch.cuda.current_stream())

    with torch.cuda.stream(stream):
        for _ in range(3):
            launch(fn, d, state, out)

    torch.cuda.current_stream().wait_stream(stream)
    torch.cuda.synchronize()

    graph = torch.cuda.CUDAGraph()

    with torch.cuda.graph(graph):
        for _ in range(GRAPH_ITERS):
            launch(fn, d, state, out)

    torch.cuda.synchronize()
    return graph, state, out


def measure(graph, state, initial):
    state.copy_(initial)
    torch.cuda.synchronize()

    start = torch.cuda.Event(enable_timing=True)
    end = torch.cuda.Event(enable_timing=True)

    start.record()
    graph.replay()
    end.record()
    end.synchronize()

    return start.elapsed_time(end) * 1000 / GRAPH_ITERS


def benchmark_pair(ref, fn, batch):
    d = make_data(batch)

    g0, s0, o0 = build_graph(ref, d)
    g1, s1, o1 = build_graph(fn, d)

    results = {
        "original": [],
        "candidate": [],
    }

    for i in range(REPEATS):
        pairs = [
            ("original", g0, s0),
            ("candidate", g1, s1),
        ]

        if i % 2:
            pairs.reverse()

        for name, graph, state in pairs:
            us = measure(graph, state, d["initial"])
            results[name].append(us)

    old_us = statistics.median(results["original"])
    new_us = statistics.median(results["candidate"])

    return old_us, new_us


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["check", "bench"],
        required=True,
    )
    args = parser.parse_args()

    if not torch.cuda.is_available():
        raise RuntimeError(
            "没有可用 DCU，请在已分配的计算节点运行"
        )

    print(
        f"A3 mode={args.mode}, "
        f"H={H}, HV={HV}, K={K}, V={V}",
        flush=True,
    )

    ref = load_variant(
        "original", VARIANTS["original"]
    )

    failed = []

    for name, filename in VARIANTS.items():
        if name == "original":
            continue

        try:
            fn = load_variant(name, filename)

            for batch in BATCHES:
                if args.mode == "check":
                    eo, es = check_one(
                        ref, fn, batch
                    )
                    print(
                        f"PASS {name} B={batch}: "
                        f"8 tokens, "
                        f"output_error={eo:.3g}, "
                        f"state_error={es:.3g}",
                        flush=True,
                    )

                else:
                    old_us, new_us = benchmark_pair(
                        ref, fn, batch
                    )
                    print(
                        f"BENCH {name} B={batch}: "
                        f"original={old_us:.3f}us, "
                        f"new={new_us:.3f}us, "
                        f"speedup={old_us/new_us:.4f}x",
                        flush=True,
                    )

        except Exception:
            failed.append(name)
            print(f"FAILED {name}:", flush=True)
            traceback.print_exc()

    print(
        "FAILED variants:",
        ", ".join(sorted(set(failed)))
        if failed else "none",
        flush=True,
    )

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()

import torch
import torch.nn.functional as F
import statistics
import aiter

torch.manual_seed(42)
device = "cuda:0"
dtype = torch.bfloat16

from aiter.tuned_gemm import tgemm

def bench(fn):
    for _ in range(5):
        fn()
    torch.cuda.synchronize()

    results = []
    for _ in range(7):
        start = torch.cuda.Event(enable_timing=True)
        end = torch.cuda.Event(enable_timing=True)

        start.record()
        for _ in range(20):
            fn()
        end.record()
        end.synchronize()

        results.append(
            start.elapsed_time(end) * 1000 / 20
        )

    return statistics.median(results)

shapes = [
    ("gate_up", 32, 17408, 5120),
    ("down", 32, 5120, 8704),
]

for label, M, N, K in shapes:
    print(f"\n=== {label} M={M} N={N} K={K} ===",
          flush=True)

    x = torch.randn(
        M, K, device=device, dtype=dtype
    ) * 0.1

    w = torch.randn(
        N, K, device=device, dtype=dtype
    ) * 0.1

    candidates = {
        "torch": lambda: F.linear(x, w),
        "aiter_tuned": lambda: tgemm.mm(x, w),
    }

    if hasattr(aiter, "gemm_a16w16_opus"):
        candidates["aiter_opus"] = (
            lambda: aiter.gemm_a16w16_opus(
                x, w, dtype=dtype
            )
        )

    ref = F.linear(x, w)
    ref_norm = torch.linalg.vector_norm(
        ref.float()
    ).item()

    base_time = None

    for name, fn in candidates.items():
        try:
            y = fn()
            torch.cuda.synchronize()

            if y.shape != ref.shape:
                print(name, "SHAPE MISMATCH", y.shape)
                continue

            if not torch.isfinite(y).all().item():
                print(name, "NON-FINITE OUTPUT")
                continue

            rel_error = (
                torch.linalg.vector_norm(
                    y.float() - ref.float()
                ).item() / max(ref_norm, 1e-12)
            )

            if rel_error > 0.03:
                print(name, "NUMERICAL MISMATCH",
                      rel_error)
                continue

            t = bench(fn)

            if name == "torch":
                base_time = t

            speedup = (
                base_time / t if base_time else 1.0
            )

            print(
                f"{name}: {t:.3f} us, "
                f"speedup={speedup:.3f}x, "
                f"relative_error={rel_error:.6f}",
                flush=True
            )

        except Exception as e:
            print(name, "FAILED:", repr(e),
                  flush=True)

print("\nA7 BENCHMARK FINISHED", flush=True)

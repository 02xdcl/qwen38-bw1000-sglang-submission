import torch
import torch.nn.functional as F
import statistics

torch.manual_seed(42)
device = "cuda:0"
dtype = torch.bfloat16

# 近似 Qwen3.8-27B TP=2 的关键 Linear 尺寸
shapes = [
    (5120, 17408, "MLP gate_up"),
    (8704, 5120, "MLP down"),
    (5120, 5120, "Hidden projection"),
]

batches = [4, 32, 64]
backends = ["cublas", "hipblaslt"]

def bench(x, w):
    for _ in range(15):
        F.linear(x, w)
    torch.cuda.synchronize()

    results = []
    for _ in range(7):
        start = torch.cuda.Event(enable_timing=True)
        end = torch.cuda.Event(enable_timing=True)

        start.record()
        for _ in range(50):
            F.linear(x, w)
        end.record()
        end.synchronize()

        results.append(start.elapsed_time(end) * 1000 / 50)

    return statistics.median(results)

print("Device:", torch.cuda.get_device_name(0), flush=True)
print("Original backend:",
      torch.backends.cuda.preferred_blas_library(),
      flush=True)

for M in batches:
    for K, N, label in shapes:
        print(f"\n{label}: M={M}, N={N}, K={K}", flush=True)

        x = torch.randn(M, K, device=device, dtype=dtype) * 0.05
        w = torch.randn(N, K, device=device, dtype=dtype) * 0.05

        outputs = {}
        times = {}

        for backend in backends:
            try:
                selected = torch.backends.cuda.preferred_blas_library(
                    backend
                )
                print(f"Backend selected: {selected}", flush=True)

                outputs[backend] = F.linear(x, w).float().clone()
                times[backend] = bench(x, w)

                print(f"{backend}: {times[backend]:.3f} us",
                      flush=True)
            except Exception as e:
                print(f"{backend}: FAILED: {e}", flush=True)

        if all(b in times for b in backends):
            ref = outputs["cublas"]
            test = outputs["hipblaslt"]

            close = torch.allclose(
                ref, test, atol=0.03, rtol=0.03
            )

            speedup = times["cublas"] / times["hipblaslt"]

            print(f"Numerical close: {close}", flush=True)
            print(f"hipBLASLt speedup: {speedup:.4f}x",
                  flush=True)

torch.backends.cuda.preferred_blas_library("cublas")
torch.cuda.synchronize()
print("\nA6 BENCHMARK FINISHED", flush=True)

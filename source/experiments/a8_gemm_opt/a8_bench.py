"""Run first; writes choice.json only if candidate is accurate and >=8% faster.

Example: python -u a8_bench.py 2>&1 | tee bench.log
"""
import json
import statistics
from pathlib import Path
import torch
import torch.nn.functional as F

from a8_kernel import CANDIDATES, run

DEVICE = 'cuda:0'
# Qwen3.5 27B TP=2, M=32 (assumes contiguous input and BF16 weights).
SHAPES = [
    ('gate_up', 32, 5120, 17408),
    ('down', 32, 8704, 5120),
]


def bench(fn):
    for _ in range(5):
        fn()
    torch.cuda.synchronize()
    times = []
    for _ in range(5):
        start = torch.cuda.Event(enable_timing=True)
        stop = torch.cuda.Event(enable_timing=True)
        start.record()
        for _ in range(20):
            fn()
        stop.record()
        stop.synchronize()
        times.append(start.elapsed_time(stop) * 1000 / 20)
    return statistics.median(times)


def main():
    torch.manual_seed(42)
    print('Device:', torch.cuda.get_device_name(0), flush=True)
    approved = {}
    for name, m, k, n in SHAPES:
        print(f'\n=== {name}: [{m},{k}] x [{n},{k}]^T ===', flush=True)
        x = (torch.randn(m, k, device=DEVICE, dtype=torch.bfloat16) * 0.05).contiguous()
        w = (torch.randn(n, k, device=DEVICE, dtype=torch.bfloat16) * 0.05).contiguous()
        ref = F.linear(x, w)
        base_us = bench(lambda: F.linear(x, w))
        print(f'baseline F.linear: {base_us:.2f} us', flush=True)
        best = None
        for cfg in CANDIDATES:
            try:
                test = run(x, w, cfg)
                torch.cuda.synchronize()
                rel = ((test.float() - ref.float()).norm() /
                       ref.float().norm().clamp_min(1e-12)).item()
                ok = bool(torch.isfinite(test).all().item()) and rel <= 0.03
                if not ok:
                    print(f'{cfg}: INVALID rel_error={rel:.6g}', flush=True)
                    continue
                t = bench(lambda: run(x, w, cfg))
                speedup = base_us / t
                print(f'{cfg}: {t:.2f} us, {speedup:.3f}x, rel={rel:.6g}', flush=True)
                if best is None or t < best[0]:
                    best = (t, cfg, rel)
            except Exception as exc:
                print(f'{cfg}: FAILED {type(exc).__name__}: {str(exc)[:350]}', flush=True)
        if best and best[0] <= base_us / 1.08:
            approved[f'{k}x{n}'] = dict(best[1])
            print(f'APPROVED: {name} speedup {base_us / best[0]:.3f}x', flush=True)
        else:
            print(f'REJECTED: {name}, no >=8% accurate speedup', flush=True)
        del x, w, ref
    dest = Path(__file__).with_name('choice.json')
    dest.write_text(json.dumps(approved, indent=2) + '\n')
    print('\nCHOICES:', approved, flush=True)
    print('Saved:', dest, flush=True)
    if not approved:
        print('STOP: None won. Do NOT patch SGLang. Return to profiling host gaps.', flush=True)
    else:
        print('Eligible for opt-in patch. Run patch command in README.', flush=True)


if __name__ == '__main__':
    main()

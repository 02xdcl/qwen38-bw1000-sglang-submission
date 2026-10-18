"""A8 experimental BF16 2D GEMM. Input x[M,K], weight[N,K].

Opt-in, not intended as general-purpose F.linear replacement.
"""
import json
import os
from pathlib import Path

import torch
import triton
import triton.language as tl


@triton.jit
def _a8_matmul(X, W, Y,
               M: tl.constexpr, N: tl.constexpr, K: tl.constexpr,
               BM: tl.constexpr, BN: tl.constexpr, BK: tl.constexpr):
    pm = tl.program_id(0)
    pn = tl.program_id(1)
    ms = pm * BM + tl.arange(0, BM)
    ns = pn * BN + tl.arange(0, BN)
    ks = tl.arange(0, BK)
    acc = tl.full((BM, BN), 0, tl.float32)
    for block in range(tl.cdiv(K, BK)):
        curr_k = block * BK + ks
        a = tl.load(X + ms[:, None] * K + curr_k[None, :],
                    (ms[:, None] < M) & (curr_k[None, :] < K), other=0)
        w = tl.load(W + ns[:, None] * K + curr_k[None, :],
                    (ns[:, None] < N) & (curr_k[None, :] < K), other=0)
        acc = tl.dot(a, tl.trans(w), acc)
    tl.store(Y + ms[:, None] * N + ns[None, :], acc,
             (ms[:, None] < M) & (ns[None, :] < N))


CANDIDATES = (
    {"BM": 16, "BN": 64, "BK": 64, "warps": 4},
    {"BM": 32, "BN": 64, "BK": 64, "warps": 4},
    {"BM": 16, "BN": 128, "BK": 64, "warps": 4},
    {"BM": 32, "BN": 128, "BK": 64, "warps": 8},
)


def run(x, weight, config):
    assert x.ndim == 2 and weight.ndim == 2
    assert x.is_cuda and weight.is_cuda
    assert x.dtype == weight.dtype == torch.bfloat16
    assert x.is_contiguous() and weight.is_contiguous()
    m, k = x.shape
    n, wk = weight.shape
    assert k == wk
    out = torch.empty((m, n), device=x.device, dtype=x.dtype)
    _a8_matmul[(triton.cdiv(m, config["BM"]), triton.cdiv(n, config["BN"]))](
        x, weight, out, m, n, k,
        config["BM"], config["BN"], config["BK"],
        num_warps=config["warps"], num_stages=2,
    )
    return out


_CONFIG_FILE = Path(os.environ.get("A8_CHOICE", str(Path(__file__).with_name("choice.json"))))
try:
    _CHOICES = json.loads(_CONFIG_FILE.read_text())
except (OSError, ValueError):
    _CHOICES = {}


def try_fast_linear(x, weight, bias=None):
    """Apply only for measured, approved matrix shapes; otherwise baseline."""
    if (bias is None and x.ndim == 2 and weight.ndim == 2
            and x.is_cuda and weight.is_cuda
            and x.dtype == torch.bfloat16 and weight.dtype == torch.bfloat16
            and x.is_contiguous() and weight.is_contiguous()
            and x.shape[0] == 32 and x.shape[1] == weight.shape[1]):
        key = f"{weight.shape[1]}x{weight.shape[0]}"
        config = _CHOICES.get(key)
        if config:
            return run(x, weight, config)
    return torch.nn.functional.linear(x, weight, bias)

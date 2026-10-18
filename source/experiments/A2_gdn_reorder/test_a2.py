import torch
import importlib.util
import sys
import traceback

BACKUP = "/public/home/zzu_dcf/qwen38_dcu_competition/experiments/A2_gdn_reorder/fused_recurrent_baseline.py"

def load_original():
    spec = importlib.util.spec_from_file_location(
        "a2_original_fused_recurrent", BACKUP
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod

try:
    from sglang.srt.layers.attention.fla import fused_recurrent as a2
    original = load_original()

    assert torch.cuda.is_available(), "DCU 不可用"

    torch.manual_seed(42)
    device = "cuda"

    B, HV, K, V = 4, 4, 128, 128
    H = HV
    slots = B + 1

    mixed = torch.randn(
        B, 2 * H * K + HV * V,
        device=device, dtype=torch.bfloat16
    )
    a = torch.randn(B, HV, device=device, dtype=torch.bfloat16)
    b = torch.randn(B, HV, device=device, dtype=torch.bfloat16)
    A_log = torch.zeros(HV, device=device, dtype=torch.float32)
    dt_bias = torch.zeros(HV, device=device, dtype=torch.float32)

    state = torch.randn(
        slots, HV, V, K,
        device=device, dtype=torch.float32
    ) * 0.01

    indices = torch.arange(
        B, device=device, dtype=torch.int32
    )

    def run(fn):
        s = state.clone()
        out = torch.empty(
            B, 1, HV, V,
            device=device, dtype=torch.bfloat16
        )
        fn(
            mixed_qkv=mixed,
            a=a,
            b=b,
            A_log=A_log,
            dt_bias=dt_bias,
            scale=K ** -0.5,
            initial_state=s,
            out=out,
            ssm_state_indices=indices,
            use_qk_l2norm_in_kernel=True,
        )
        torch.cuda.synchronize()
        return out, s

    print("Running original Triton Kernel...", flush=True)
    out0, state0 = run(
        original.fused_recurrent_gated_delta_rule_packed_decode
    )

    print("Running A2 Triton Kernel...", flush=True)
    out1, state1 = run(
        a2.fused_recurrent_gated_delta_rule_packed_decode
    )

    print("========== A2 Numerical Comparison ==========")
    print("Output max abs error:",
          (out0.float() - out1.float()).abs().max().item())
    print("State max abs error:",
          (state0.float() - state1.float()).abs().max().item())

    print("Output finite:", bool(torch.isfinite(out1).all().item()))
    print("State finite:", bool(torch.isfinite(state1).all().item()))

    print("Output close:",
          torch.allclose(out0.float(), out1.float(),
                         atol=0.02, rtol=0.02))
    print("State close:",
          torch.allclose(state0.float(), state1.float(),
                         atol=0.005, rtol=0.005))

except Exception:
    traceback.print_exc()
    sys.exit(1)

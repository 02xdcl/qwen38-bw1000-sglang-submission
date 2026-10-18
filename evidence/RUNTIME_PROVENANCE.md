# JobID 934852 运行版本声明

本仓库以 JobID `934852` 实际启动的 SGLang 服务作为固定长度正式测试的运行版本。版本身份由原始补包中的 `provenance.txt`、`identity.txt`、`server.log`、`run.log` 和 `progress.txt` 共同确定。

## 软件构建

- SGLang：`0.5.12+das185.dtk2604.torch2100.2608121934.gcbf025`
- PyTorch：`2.10.0+das.opt1.dtk2604.2608141812.g28498c`
- Triton：`3.6.0+das185.dtk2604.torch2100.2608141110.g65af71`
- `sglang/bench_serving.py` SHA256：`f2206dcda74932e1b148cdf7b5ef07443bb5d9e0f2729b7a67d602182e3aa050`

## 服务身份与主要参数

- 节点：`a01r3n19`
- Slurm JobID：`934852`
- 服务 PID：`653002`
- 测试来源信息采集时间：`2026-10-17T16:27:53+08:00`（严格测试脚本生成 `provenance.txt` 时记录）
- 服务就绪日志时间：`2026-10-17 16:26:03`（`server.log` 的 `The server is fired up and ready to roll!`）
- 模型：`Qwen3.8-27B`，服务名 `qwen38-bf16`
- 精度与并行：BF16，TP=2
- 上下文长度：131072
- `chunked_prefill_size=8192`
- `max_prefill_tokens=16384`
- `schedule_conservativeness=0.4`
- `num_continuous_decode_steps=1`
- attention backend：Triton

`server.log` 中的 `ServerArgs` 与 `provenance.txt` 的启动参数一致，后续 4K/64K 请求由该端口服务。10 个档位的 50 组预热/正式文件及执行状态见 `job934852_manifest.sha256`；30 轮正式指标见 `job934852_rounds.csv`。

## 原集群的服务启动命令

以下环境变量和命令转录自该作业的 `provenance.txt`。在已分配 BW1000 计算资源、原虚拟环境及模型就位的终端运行；保持此终端服务运行，再在同一作业的另一终端执行严格测试脚本。

```bash
export SGLANG_KV_LAYOUT_HCU_FA=false
export AILLVM_HOME=/public/home/zzu_dcf/qwen38_dcu_competition/toolchain/aillvm
export TRITON_HIP_CLANG_PATH="$AILLVM_HOME/bin/clang-18"
export SGLANG_USE_AITER_LINEAR_ATTN=false
export SGLANG_ROCM_USE_AITER_MOE=false
export CPLUS_INCLUDE_PATH=/public/software/compiler/dtk-26.04/include:/public/software/compiler/dtk-26.04/llvm/include:/opt/hyhal/include:/public/software/compiler/dtk-26.04/opencl/include

/public/home/zzu_dcf/sglang/bin/python -u -m sglang.launch_server \
  --model-path /public/home/zzu_dcf/qwen38_dcu_competition/models/Qwen3.8-27B \
  --served-model-name qwen38-bf16 \
  --host 127.0.0.1 --port 18580 \
  --tp-size 2 --dtype bfloat16 --context-length 131072 \
  --max-running-requests 128 --chunked-prefill-size 8192 \
  --max-prefill-tokens 16384 --schedule-conservativeness 0.4 \
  --mem-fraction-static 0.85 --attention-backend triton \
  --disable-custom-all-reduce --disable-piecewise-cuda-graph \
  --trust-remote-code
```

该命令复用原集群的软件和路径；`requirements.txt` 中的版本对应厂商构建。

## 候选补丁边界

`patch/a3_warp2_candidate.patch` 是独立实验候选，不用于定义 JobID 934852 的正式运行版本。正式结果只关联上述软件构建、启动命令、环境变量和服务参数。

## 原件校验

原始补包 `q38_late_results.tar.gz` SHA256：`37f54b419541ed4d29658d7f7d6d8f278e658b9acb3907f9b3dbc21b6030c6c5`。

关键文件 SHA256：

- `identity.txt`：`4b59e7f78697fba1ac15da6bd475693c8e2899ec66d8e8f219d0f5cc764b8947`
- `progress.txt`：`59da1607573e4977f7c4e4908650246edda94782b819cecf9ea2c413bab68db2`
- `provenance.txt`：`6a68ee5a72382779bc8ce49efb51c1d161710f5ccab9782985d3da783e5a2d51`
- `run.log`：`8c30cd5db714e19ed537031ab17a148603a2ad1387b8ef0b1c6c4c78ab8ebe6a`
- `server.log`：`258ffd29da9e0c0cf8701be040f2026a5e8db2ca8d830f143ffac26373b40abb`

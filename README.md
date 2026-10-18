# Qwen3.8-27B on BW1000: SGLang 提交整理稿

本仓库整理 BW1000 上 Qwen3.8-27B BF16 的 SGLang 实测记录。结果按作业、负载和服务会话分别列示。

`report.md` 汇总从原始日志逐轮核对的 4K/64K、ShareGPT 和 GSM8K 结果。JobID 934852 的 4K/64K 三轮日志与 JSONL 已交叉核对；历史基线与该作业属于不同节点，报告分别呈现。已收到的补包原件保存在本地。

独立的 4K C64 单轮日志保存在本地 `source/results/final_4k_c64_20261017_020528/`；其 benchmark backend 与历史基线不同，报告单独列示。

## 已确认的运行配置

- 用户确认卡型为 BW1000。日志中的服务使用 TP=2、Qwen3.8-27B、BF16、SGLang 0.5.12+das185、DTK 26.04。
- JobID 934852 的启动信息见本地 `q38_late_results.tar.gz` 中的 `results/strict_4k64k_job934852/provenance.txt`；仓库内 15:53 的 `source/results/strict_formal_20261017_155319/provenance.txt` 属于另一次运行。
- 本包里的 `scripts/run.sh` 是原始 ShareGPT 复测脚本副本；`scripts/bench_strict_4k64k.sh` 是原始严格测试脚本副本，要求先在 Slurm 分配的计算节点启动服务。路径仍指向原集群 `/public/home/zzu_dcf/`，迁移机器前必须更新。
- `source/` 保留基线日志、实验脚本、单轮复测和审计结果。`report.md` 区分同窗 A/B、历史基线与跨会话复测。

## 在原集群复现

在 BW1000 计算节点、已有 `~/sglang` 环境和模型权重就位后，从本仓库根目录核对脚本内路径与参数，再执行：

```bash
bash scripts/run.sh
```

该脚本依次运行 ShareGPT 并发 C1/C4/C16/C32/C64，每档 1 次预热及 1 次正式测试，每次正式测试 1000 请求。原始脚本及原始结果均保存在 `source/`。严格 4K/64K 测试由 `scripts/bench_strict_4k64k.sh OUTPUT_DIR` 执行，前提是唯一 SGLang 服务已在端口 18580 运行；其本次归档中的 15:53 运行仅完成部分 4K C1 预热，不可作为完整成绩。

## 文件说明

- `report.md`：按作业和负载区分的五段式实测报告。
- `env_declare.yaml`：有来源记录的环境和运行字段。
- `scripts/`：原始复测与严格测试脚本副本。
- `patch/a3_warp2_candidate.patch`：A3 实验的一行候选补丁。
- `source/experiments/`：A9/A10/A11/A13 参数 A/B 原始脚本与日志。
- `source/results/`：历史基线、复测和审计原文。
- `SUBMISSION_CHECKLIST.md`：项目操作记录和证据索引。

模型权重、SIF 镜像和原始补包保存在仓库外。


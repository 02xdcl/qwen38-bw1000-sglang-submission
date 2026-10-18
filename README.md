# Qwen3.8-27B on BW1000: SGLang 提交整理稿

**状态：证据整理稿，尚未满足赛事有效提交条件。** 本仓库依据用户提供的 `submission_materials_20261017_155641.tar.gz` 整理，保留原始脚本和日志；没有把不同时间、不同负载的结果拼成比赛提升率。

2026-10-18 补充核验：`report.md` 列出从原始日志逐轮重算的 4K/64K 历史基线、单轮 4K 复测和 ShareGPT 数据。用户后续上传的补包还包含 JobID 934852 完整 4K/64K 三轮原始结果，30 轮的日志与 JSONL 已核对；报告新增对应汇总表。补包原件目前保存在本地，尚未公开入库。官方赛题详情、同窗默认基线、环境与精度证据仍需核实，不能将本地实测值直接称为赛事正式成绩。缺项和证据位置见 `SUBMISSION_CHECKLIST.md`。

独立的 4K C64 单轮日志已从原始压缩包补入 `source/results/final_4k_c64_20261017_020528/`。其 benchmark backend 与历史基线不同，只作为观察记录，不计入正式提升率。

## 已确认的运行配置

- 用户确认卡型为 BW1000。日志中的服务使用 TP=2、Qwen3.8-27B、BF16、SGLang 0.5.12+das185、DTK 26.04。
- 2026-10-17 15:53 的 `source/results/strict_formal_20261017_155319/provenance.txt` 记录了服务完整参数：chunked prefill 8192、max prefill tokens 16384、schedule conservativeness 0.4、attention backend triton。
- 本包里的 `scripts/run.sh` 是原始 ShareGPT 复测脚本副本；`scripts/bench_strict_4k64k.sh` 是原始严格测试脚本副本，要求先在 Slurm 分配的计算节点启动服务。路径仍指向原集群 `/public/home/zzu_dcf/`，迁移机器前必须更新。
- `source/` 保留基线日志、实验脚本、单轮复测和审计结果。`report.md` 区分同窗 A/B、历史基线与跨会话复测。

## 在原集群复现

在 BW1000 计算节点、已有 `~/sglang` 环境和模型权重就位后，核对脚本内路径与参数，再执行：

```bash
cd /public/home/zzu_dcf/qwen38_dcu_competition
bash experiments/sharegpt_retest/run.sh
```

该脚本依次运行 ShareGPT 并发 C1/C4/C16/C32/C64，每档 1 次预热及 1 次正式测试，每次正式测试 1000 请求。原始脚本及原始结果均保存在 `source/`。严格 4K/64K 测试由 `scripts/bench_strict_4k64k.sh OUTPUT_DIR` 执行，前提是唯一 SGLang 服务已在端口 18580 运行；其本次归档中的 15:53 运行仅完成部分 4K C1 预热，不可作为完整成绩。

## 提交前必须补齐

1. 核实飞书赛题详情所列的正式负载、指标、阈值和默认基线；补齐同一配置下的 ShareGPT 正式运行证据。JobID 934852 的严格 4K/64K 原始结果已收到并完成本地逐轮核对。
2. 完成 `env_declare.yaml` 的 CPU、内存、互联、驱动、权重 SHA256、镜像/虚拟环境来源等字段；获取实际计算节点的硬件驱动原始输出。
3. 提供官方精度校验结果，并附至少 3 张含命令上下文与时间戳的未裁切截图。
4. 将自己的优化配置和实际生效的代码改动固定为可重放版本。若最终方案修改框架或算子，必须提供针对确切 SGLang 版本可应用的 patch；现有 A3 差异只是实验记录，尚无证据表明它被最终服务加载。
5. 向主办方核实 BW1000 的组别。赛事文档写的是 BW100，未列 BW1000。
6. 将五段式报告和四类原始日志贴在论坛《作品提交专区》回帖正文或附件。仅公开 GitHub 仓库不算提交；文档截止时间为 2026-10-18 17:59。

## 文件说明

- `report.md`：有来源指针的五段式报告草稿。
- `env_declare.yaml`：已确认字段与待补字段。
- `scripts/`：原始复测与严格测试脚本副本。
- `source/experiments/`：A9/A10/A11/A13 参数 A/B 原始脚本与日志。
- `source/results/`：历史基线、复测和审计原文。
- `SUBMISSION_CHECKLIST.md`：逐项验收状态、证据索引和待补内容。

未包含模型权重、SIF 镜像、第三方软件包或 130 MB 原始大包。当前仓库不声明任何未经核验的赛事成绩。


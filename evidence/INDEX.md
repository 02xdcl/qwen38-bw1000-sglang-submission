# 证据索引

本索引把仓库中的环境、性能、精度、优化实验和论坛材料关联到对应记录。完整原始归档的组成、哈希及重新获取方法见 [ORIGINAL_ARCHIVES.md](ORIGINAL_ARCHIVES.md)。

## 正式环境与固定长度测试

| 内容 | 公开记录 | 原始归档位置 |
| --- | --- | --- |
| JobID 934852 环境与启动参数 | [原始运行目录](../source/results/strict_4k64k_job934852/)、[env_declare.yaml](../env_declare.yaml)、[report.md](../report.md) | 同目录 `provenance.txt`、`identity.txt`、`server.log` |
| 正式运行版本定义 | [RUNTIME_PROVENANCE.md](RUNTIME_PROVENANCE.md) | 软件构建、启动命令、服务参数及关键原件哈希 |
| 4K/64K 30 轮正式指标 | [job934852_rounds.csv](job934852_rounds.csv) | `q38_late_results.tar.gz` → `results/strict_4k64k_job934852/*_run{1,2,3}.log/.jsonl/.ok` |
| 固定长度目录完整性 | [job934852_manifest.sha256](job934852_manifest.sha256) | 上述目录全部 155 个文件的相对路径与 SHA256 |
| 4K/64K 执行进度与时间 | [report.md](../report.md) | `q38_late_results.tar.gz` → `results/strict_4k64k_job934852/progress.txt`、`run.log` |
| 指标提取与复算 | [summarize_934852.py](../scripts/summarize_934852.py)、[README.md](README.md) | 由上述 30 份正式 JSONL 重新生成 |

性能补包 SHA256：`37f54b419541ed4d29658d7f7d6d8f278e658b9acb3907f9b3dbc21b6030c6c5`。

## 历史基线与复测

| 内容 | 仓库目录 |
| --- | --- |
| 4K 历史三轮记录 | [sglang_bf16_4k_20261007_163756](../source/results/sglang_bf16_4k_20261007_163756/) |
| 64K 历史三轮记录 | [sglang_bf16_64k_20261007_201746](../source/results/sglang_bf16_64k_20261007_201746/) |
| ShareGPT 历史记录 | [sglang_bf16_sharegpt_893107](../source/results/sglang_bf16_sharegpt_893107/) |
| ShareGPT 2026-10-16 复测 | [sharegpt_retest_20261016_011410](../source/results/sharegpt_retest_20261016_011410/) |
| 4K 单轮复测 | [final_retest_20261017](../source/results/final_retest_20261017/) |
| 较早严格运行记录 | [strict_formal_20261017_155319](../source/results/strict_formal_20261017_155319/) |
| 服务与代码审计记录 | [submission_audit_20261017_150109](../source/results/submission_audit_20261017_150109/) |

各组数据的运行归属、轮次和适用边界见 [report.md](../report.md)。

## GSM8K 精度运行

| 内容 | 公开记录 | 原始归档位置 |
| --- | --- | --- |
| 1314 条逐题评分摘录 | [gsm8k_935993_scores.csv](gsm8k_935993_scores.csv) | `GSM8K_job935993_full_evidence.tar.gz` → `results/accuracy_job935993/gsm8k/gsm8k_qwen38-bf16.html` |
| JSON 汇总、评测与服务记录 | [report.md](../report.md) | 同一归档中的 `gsm8k_qwen38-bf16.json`、`eval.log`、`server_18580.log` |
| 评分提取与复算 | [summarize_gsm8k.py](../scripts/summarize_gsm8k.py)、[README.md](README.md) | 由逐题 HTML 重新生成 |

精度补包 SHA256：`c6cc1afeefff25b7cc7bf51e21602079c746a8a3748cee2a55a5f9275bf2bb7b`。

## 优化实验与候选补丁

| 内容 | 仓库目录 |
| --- | --- |
| Schedule conservativeness A/B | [A9_schedule_ab](../source/experiments/A9_schedule_ab/)、[A10_schedule_tuning](../source/experiments/A10_schedule_tuning/) |
| Chunked prefill 扫描 | [A11_prefill_tuning](../source/experiments/A11_prefill_tuning/) |
| 连续 decode 步数扫描 | [A13_decode_tuning](../source/experiments/A13_decode_tuning/) |
| A3 warp2 候选差异 | [a3_warp2_candidate.patch](../patch/a3_warp2_candidate.patch) |
| A3 JobID 914874 独立 A/B | [六轮指标与源哈希](a3_job914874_rounds.csv)、[运行归属](COMPETITION_20261018.md#a3-独立-ab-实验) |

候选补丁与正式运行的关系按 [report.md](../report.md) 中的适用边界解释。

## 提交材料

原始性能、GSM8K、采集记录和 A3 的完整入口见 [综合补包与原始日志索引](COMPETITION_20261018.md)。新增与已有原件的哈希见 [published_raw_files.sha256](published_raw_files.sha256)。

| 内容 | 文件 |
| --- | --- |
| 五段式实测报告 | [report.md](../report.md) |
| 已发布论坛正文存档 | [论坛提交回复_已发布文本.md](../论坛提交回复_已发布文本.md) |
| 提交前证据口径草稿 | [论坛回复_已核实数据草稿.md](../论坛回复_已核实数据草稿.md) |
| 环境声明 | [env_declare.yaml](../env_declare.yaml) |
| 复现入口 | [run.sh](../scripts/run.sh)、[bench_strict_4k64k.sh](../scripts/bench_strict_4k64k.sh) |
| 执行与验收记录 | [SUBMISSION_CHECKLIST.md](../SUBMISSION_CHECKLIST.md) |

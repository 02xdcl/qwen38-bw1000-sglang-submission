# JobID 934852 逐轮指标

完整原始归档的内容及重新获取命令见 `ORIGINAL_ARCHIVES.md`。

`job934852_rounds.csv` 从 `q38_late_results.tar.gz` 内 `results/strict_4k64k_job934852/` 的 30 份正式轮次 `.jsonl` 提取。归档包 SHA256：`37f54b419541ed4d29658d7f7d6d8f278e658b9acb3907f9b3dbc21b6030c6c5`。每行保留源文件名和该文件的 SHA256；该 CSV 是指标摘录，不是原始 benchmark 日志，也不包含逐请求数据。

在取得并解压原始归档后，从仓库根目录重新生成：

```bash
python scripts/summarize_934852.py /path/to/results/strict_4k64k_job934852 > evidence/job934852_rounds.csv
```

按 `scenario`、`concurrency` 分组，对三轮 `output_throughput`、`mean_ttft_ms`、`mean_tpot_ms` 和 `p99_e2e_latency_ms` 分别取算术均值，即 `report.md` 中 JobID 934852 的十行结果。P99 列是三个逐轮 P99 的均值。

`gsm8k_935993_scores.csv` 从独立运行的 `GSM8K_job935993_full_evidence.tar.gz` 中 `results/accuracy_job935993/gsm8k/gsm8k_qwen38-bf16.html` 提取逐题评分，不含题目文本或生成答案。原始归档 SHA256：`c6cc1afeefff25b7cc7bf51e21602079c746a8a3748cee2a55a5f9275bf2bb7b`。在取得原始 HTML 后可重新生成：

```bash
python scripts/summarize_gsm8k.py /path/to/gsm8k_qwen38-bf16.html > evidence/gsm8k_935993_scores.csv
```

CSV 共 1314 行评分，1266 行 `1.0`、48 行 `0.0`，均值为 `1266/1314 = 96.3470%`。这次 GSM8K 运行与 JobID 934852 的性能测试分开记录。

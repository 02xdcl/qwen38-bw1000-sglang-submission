# JobID 934852 逐轮指标

`job934852_rounds.csv` 从 `q38_late_results.tar.gz` 内 `results/strict_4k64k_job934852/` 的 30 份正式轮次 `.jsonl` 提取。归档包 SHA256：`37f54b419541ed4d29658d7f7d6d8f278e658b9acb3907f9b3dbc21b6030c6c5`。每行保留源文件名和该文件的 SHA256；该 CSV 是指标摘录，不是原始 benchmark 日志，也不包含逐请求数据。

在取得并解压原始归档后，从仓库根目录重新生成：

```bash
python scripts/summarize_934852.py /path/to/results/strict_4k64k_job934852 > evidence/job934852_rounds.csv
```

按 `scenario`、`concurrency` 分组，对三轮 `output_throughput`、`mean_ttft_ms`、`mean_tpot_ms` 和 `p99_e2e_latency_ms` 分别取算术均值，即 `report.md` 中 JobID 934852 的十行结果。P99 列是三个逐轮 P99 的均值。

# 原始补包说明与获取方法

“原始补包”是从集群已有结果目录打出的归档，不会重新运行模型或 benchmark。

## 1. 性能结果补包

文件名：`q38_late_results.tar.gz`

SHA256：`37f54b419541ed4d29658d7f7d6d8f278e658b9acb3907f9b3dbc21b6030c6c5`

主要内容：

- `results/strict_4k64k_job934852/`：JobID 934852 的 4K/64K 日志、JSONL、完成标记、启动与来源记录。
- `results/sharegpt_baseline_envfix_20261017_165431/`：ShareGPT 环境修复阶段记录。
- `results/sharegpt_retest_hcu23_20261017_190126/`：ShareGPT 复测记录。
- `results/sharegpt_warp1_baseline_20261017_213815/`：ShareGPT 后续运行及恢复目录。

在集群项目目录重新打包：

```bash
cd /public/home/zzu_dcf/qwen38_dcu_competition
tar -czf ~/q38_late_results.tar.gz \
  results/strict_4k64k_job934852 \
  results/sharegpt_baseline_envfix_20261017_165431 \
  results/sharegpt_retest_hcu23_20261017_190126 \
  results/sharegpt_warp1_baseline_20261017_213815
sha256sum ~/q38_late_results.tar.gz
```

## 2. GSM8K 精度补包

文件名：`GSM8K_job935993_full_evidence.tar.gz`

SHA256：`c6cc1afeefff25b7cc7bf51e21602079c746a8a3748cee2a55a5f9275bf2bb7b`

主要内容：`results/accuracy_job935993/` 下的 `eval.log`、GSM8K JSON 汇总、逐题 HTML 和 `server_18580.log`。

在集群项目目录重新打包：

```bash
cd /public/home/zzu_dcf/qwen38_dcu_competition
tar -czf ~/GSM8K_job935993_full_evidence.tar.gz \
  results/accuracy_job935993
sha256sum ~/GSM8K_job935993_full_evidence.tar.gz
```

## 3. 下载到本机

在能够访问集群登录节点的本机 PowerShell 中执行；把 `<登录节点地址>` 替换为实际地址：

```powershell
scp zzu_dcf@<登录节点地址>:~/q38_late_results.tar.gz "$env:USERPROFILE\Downloads\"
scp zzu_dcf@<登录节点地址>:~/GSM8K_job935993_full_evidence.tar.gz "$env:USERPROFILE\Downloads\"
Get-FileHash -Algorithm SHA256 "$env:USERPROFILE\Downloads\q38_late_results.tar.gz"
Get-FileHash -Algorithm SHA256 "$env:USERPROFILE\Downloads\GSM8K_job935993_full_evidence.tar.gz"
```

若本机无法解析登录节点，可从集群门户的文件管理器下载用户目录中的两个文件，或先下载到可连集群的电脑。下载后的 SHA256 应与上文一致。

当前仓库只公开由这些原件提取的指标 CSV及其源文件哈希；完整归档包含集群路径、启动日志和逐题答案，没有直接提交到 GitHub。

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
archive_dir=$(mktemp -d "$HOME/q38_archive_XXXXXXXX")
tar -czf "$archive_dir/q38_late_results.tar.gz" \
  results/strict_4k64k_job934852 \
  results/sharegpt_baseline_envfix_20261017_165431 \
  results/sharegpt_retest_hcu23_20261017_190126 \
  results/sharegpt_warp1_baseline_20261017_213815
sha256sum "$archive_dir/q38_late_results.tar.gz"
```

## 2. GSM8K 精度补包

文件名：`GSM8K_job935993_full_evidence.tar.gz`

SHA256：`c6cc1afeefff25b7cc7bf51e21602079c746a8a3748cee2a55a5f9275bf2bb7b`

主要内容：`results/accuracy_job935993/` 下的 `eval.log`、GSM8K JSON 汇总、逐题 HTML 和 `server_18580.log`。

在集群项目目录重新打包：

```bash
cd /public/home/zzu_dcf/qwen38_dcu_competition
archive_dir=$(mktemp -d "$HOME/q38_archive_XXXXXXXX")
tar -czf "$archive_dir/GSM8K_job935993_full_evidence.tar.gz" \
  results/accuracy_job935993
sha256sum "$archive_dir/GSM8K_job935993_full_evidence.tar.gz"
```

## 3. 下载到本机

下面命令下载用户目录中原先已有的两份归档。在能够访问集群登录节点的本机 PowerShell 中执行；把 `<登录节点地址>` 替换为实际地址。下载新打包的归档时，使用上一步 `sha256sum` 显示的新目录路径。打包命令用 `mktemp -d` 创建独立目录，保留原归档。

```powershell
scp zzu_dcf@<登录节点地址>:~/q38_late_results.tar.gz "$env:USERPROFILE\Downloads\"
scp zzu_dcf@<登录节点地址>:~/GSM8K_job935993_full_evidence.tar.gz "$env:USERPROFILE\Downloads\"
Get-FileHash -Algorithm SHA256 "$env:USERPROFILE\Downloads\q38_late_results.tar.gz"
Get-FileHash -Algorithm SHA256 "$env:USERPROFILE\Downloads\GSM8K_job935993_full_evidence.tar.gz"
```

若本机无法解析登录节点，可从集群门户的文件管理器下载用户目录中的两个文件，或先下载到可连集群的电脑。传输现有原始压缩包时，下载后的 SHA256 应与上文一致。

重新执行 `tar` 会产生新的归档；gzip 时间戳、目录元数据及文件变化都可能改变压缩包哈希。新包应在集群计算自己的 SHA256，下载后与该次记录比对。原包哈希仅标识此前收到的那份归档。解压后还可在 `results/strict_4k64k_job934852/` 中对本仓库的 `evidence/job934852_manifest.sha256` 执行 `sha256sum -c`，核对 155 个原始文件内容。

压缩归档保存在仓库外。用户现已授权补齐原始日志，保留的性能、服务、GSM8K 与采集原件按原路径收录于 `source/`，详见 [原始日志索引](COMPETITION_20261018.md)。

## 4. 综合证据补包

文件名：`competition_evidence_20261018_155237.tar.gz`。

SHA256：`771d30a04dea3f6c682b1425781d650a917b71b66575e89ffca629fa752d0885`。

本包 361 个文件，包内 354 条原始校验均通过。按用户最后确定的公开范围，性能、实验、采集及 GSM8K 的保留原件已补入仓库，完整压缩包原样保存。

# 综合补包与原始日志索引

归档：`competition_evidence_20261018_155237.tar.gz`。

SHA256：`771d30a04dea3f6c682b1425781d650a917b71b66575e89ffca629fa752d0885`。

归档共 361 个文件；包内 `original_sha256.txt` 列出的 354 个文件校验全部通过。原始补包原样保存，本页索引本次保留的性能、采集及 GSM8K 原件。

## 原始记录

| 内容 | 仓库路径 |
| --- | --- |
| JobID 934852 完整固定长度运行 | [strict_4k64k_job934852](../source/results/strict_4k64k_job934852/) |
| A3 独立 A/B 原始输出 | [a3_sharegpt_ab_914874](../source/results/a3_sharegpt_ab_914874/) |
| A3 控制脚本、候选与控制日志 | [A3_gdn_tuning](../source/experiments/A3_gdn_tuning/) |
| GSM8K 评测日志、JSON 与评分 HTML | [gsm8k](../source/results/accuracy_job935993/gsm8k/) |
| GSM8K 服务记录 | [server_18580.log](../source/results/accuracy_job935993/server_18580.log) |
| Slurm、登录节点及软件采集原文 | [采集目录](../source/results/competition_evidence_20261018_155237/) |
| 独立 C64 单轮原文 | [final_4k_c64](../source/results/final_4k_c64_20261017_020528/) |

[原始文件 SHA256 清单](published_raw_files.sha256) 覆盖本轮对应的 383 个文件，包括现有的 156 个同字节文件和新增的 227 个文件。JobID 934852 的 155 个文件包含此前归档中的 50 个完成标记；其余 105 个文件与综合补包逐字节一致。原始实验与失败记录保留各自目录，按来源分别解释。

## 采集与作业归属

Slurm 原始记录确认：890466、890928 分别在 f11r3n05、f13r1n12，状态 COMPLETED；935993 在 a01r3n15，整体状态 TIMEOUT。三条记录均分配 8 张 DCU 配额；配额与模型 TP=2 的实际运行配置分别记录。已完成的任务以各自输出判断。

硬件采集文件记录时间 `2026-10-18T15:52:37+08:00`、节点 `zz-login02`；这是登录节点快照。软件清单、模型文件大小和已有镜像清单均保留原文，按本次采集来源引用。

## A3 独立 A/B

JobID 914874 的控制日志记录节点 a02r1n15、HIP_VISIBLE_DEVICES=0,1、两个可见设备与临时 SGLang 加载路径；控制脚本在副本中切换 original/warp2 后分别启动服务。每变体每档单轮 200 请求均成功。

| 并发 | original 输出 tok/s | warp2 输出 tok/s | original TTFT ms | warp2 TTFT ms |
| ---: | ---: | ---: | ---: | ---: |
| 4 | 112.74 | 114.08 | 213.46 | 203.81 |
| 32 | 410.80 | 412.80 | 398.93 | 395.45 |
| 64 | 467.67 | 468.76 | 1513.19 | 1509.37 |

六轮完整值及源 JSONL 哈希见 [a3_job914874_rounds.csv](a3_job914874_rounds.csv)。该实验与 JobID 934852 和 1000 请求 ShareGPT 分别呈现。

## 校验

发布前直接打开三个压缩包逐个读取成员文件，核对 SHA256 与 Git blob：综合补包对应 331 个文件、此前性能补包对应 50 个完成标记、最早 `submission_materials_20261017_155641.tar.gz` 对应独立 C64 两个文件，共 383 个，全部匹配。这里的验证读取压缩包成员原字节，没有运行或改写日志。

在仓库根目录运行 `sha256sum -c evidence/published_raw_files.sha256` 核对原始文件。较早文件的 Windows 检出换行由 Git 配置决定；正式校验应使用保存的原始字节。

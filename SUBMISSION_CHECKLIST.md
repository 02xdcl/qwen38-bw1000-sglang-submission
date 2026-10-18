# Qwen3.8-27B BW1000 / SGLang 提交主清单

最后更新：2026-10-18 CST。仓库：https://github.com/02xdcl/qwen38-bw1000-sglang-submission；本地分支 `main`。当前执行事项：P0-02/P0-03/P0-05 可独立证据整理；P0-01 仍 BLOCKED，等待 BW1000 自测基线合规证据。完成进度：1/9 项 DONE。**本文件是唯一进度主清单。**

## 状态与证据规则

状态只用 `NOT_STARTED`、`IN_PROGRESS`、`BLOCKED`、`DONE`、`NOT_APPLICABLE`。`C:/Users/admin/Desktop/DCU/` 中五份材料是用户提供的二次整理材料；除非有对应原始日志、进程/环境快照及测试配置，不把其中结论升格为正式成绩。仓库 `source/` 为 2026-10-17 15:56 之前提供的原始材料；新材料不覆盖它。用户夜间授权本地可逆整理，禁止远程修改、高开销 GPU 任务及覆盖原始结果。

## 项目基线与来源区分

- 已有：`README.md`、`report.md`、`env_declare.yaml`、`requirements.txt`、`scripts/run.sh`、`scripts/bench_strict_4k64k.sh`；`source/results/` 有历史 4K、64K、ShareGPT 基线、10/16 ShareGPT 复测、10/17 不完整严格复测及审计；`source/experiments/` 有 A9/A10/A11/A13 探索实验。克隆时工作树干净，仓库跟踪文件 198 个；没有 `patch/`、`logs/` 或原有 `SUBMISSION_CHECKLIST.md`。
- 用户提供的赛事规则文本（本地 `C:/Users/admin/Documents/Codex/2026-10-17/we/work/requirements.md`，源于 `拿.docx`）要求五段式报告、四类原始日志、至少三张含命令上下文和时间戳的截图，以及论坛《作品提交专区》回复；文本写明截止 2026-10-18 17:59。该文本将 BW100 列为先锋组、其他卡型列为开放组；无官方基线卡型可用自测基线，但要求同机同软件环境、官方默认配置、四类原始日志与 3 天公示接受质疑。用户确认 BW1000 采用自测基线。另提供的 11 页赛题详情 PDF（本地 `C:/Users/admin/Desktop/社区qwen3.8挑战赛.pdf`，SHA256 `a75d6e9e35414a51a2d99eba86feca591d875f08e29aa0231d177965c09ae90c`）只列 BW100/K100-AI 的性能基线及 SLA；末页注明部分内容由 AI 生成。BW1000 的 SLA 与综合评分细则仍需确认。
- 参考仓库只用于目录组织对照：[myrfy001/qwen38-k100ai-sglang](https://github.com/myrfy001/qwen38-k100ai-sglang) 根目录有 `bench/`、`config/`、`kernels/`、`logs/`、`patch/`、`scripts/`、`report.md`、`env_declare.yaml`；[codingmiao/q38-k100ai-submission](https://github.com/codingmiao/q38-k100ai-submission) 有 `config/`、`logs/`、`patch/`、`result/`、`scripts/`、`论坛提交回复.md`。这不是本项目的成绩或官方要求。
- DCU 整理稿 `优化后.md` 曾声称 JobID 934852 的 64K/C128 三轮及 ShareGPT 为优化版正式结果；后续补包已补到 934852 的 **4K C128 与 64K C1/8/16/32** 原始目录，但该包没有 64K C128 正式档位，也不能证明 ShareGPT 为统一服务会话。`Qwen38_DCU_优化与实验记录汇总.md` 指出 live A2 内核哈希与基线相同，无法证明 A2 被正式服务加载。其 `report.md` 写 BW100 ×2，与用户确认的 BW1000 冲突；GSM8K 数值缺原始评测。`代码改动.patch` 仅含 `num_warps=1→2`，不证明正式服务已加载。不能将这些材料直接覆盖仓库 `report.md`。

## 逐项清单

### P0-00 建立项目基线与现状盘点 — DONE，P0（最后更新：2026-10-18 04:53 CST）

- 完成标准：仓库身份、Git 状态、主要文件、现有证据、官方文本与参考仓库区别、缺项和顺序均可追溯。
- 已完成/验证：核查 `git status`、`git rev-parse HEAD`、`git remote -v`、根目录及 `source/results/`、`source/experiments/`；阅读 README、报告、环境声明、依赖、两份主脚本、审计警告、五份 DCU 材料；通过 GitHub 只读接口查看两个参考仓库根目录。克隆时无未提交修改；本清单创建前确认不存在同名文件。
- 仓库文件：`README.md`、`report.md`、`env_declare.yaml`、`requirements.txt`、`scripts/`、`source/results/submission_audit_20261017_150109/warnings.txt`。
- 原始证据：`source/results/` 下历史日志；官方规则文本 `C:/Users/admin/Documents/Codex/2026-10-17/we/work/requirements.md`；DCU 五份原件位于 `C:/Users/admin/Desktop/DCU/`，均未改动。
- 未解决：赛事链接/最新论坛细则未独立核验；不妨碍完成现状盘点。下一步 P0-01。

### P0-01 最终正式性能测试 — BLOCKED，P0（最后更新：2026-10-18 12:45 CST）

- 完成标准：官方测试范围已核实；4K、64K、ShareGPT 必要档位的真实原始日志、逐请求结果、成功数、P99/SLA、计算汇总及同一运行配置关联齐全。
- 已检查/验证：历史基线及部分复测见下文。新补包 `C:/Users/admin/Downloads/q38_late_results.tar.gz`（SHA256 `37f54b419541ed4d29658d7f7d6d8f278e658b9acb3907f9b3dbc21b6030c6c5`）已提供 JobID 934852 完整 4K/64K 原始目录，暂在 `C:/Users/admin/Documents/Codex/2026-10-17/we/work/q38_late_results/results/` 校验，未公开入库。压缩包 221 条目、215 文件、无重复或越界路径；10 档 × 3 正式轮的 `.log`、`.jsonl`、`.ok` 齐全，成功数、吞吐、TTFT、TPOT、P99 E2E 双源汇总一致。`progress.txt` 全部 PASS；`identity.txt` 与 `provenance.txt` 记录节点 a01r3n19、JobID 934852、服务 PID 653002、TP=2、BF16 和启动参数。30 份 JSONL 各只有一行汇总，且 `output_details=False`，缺逐请求明细，不能独立重算 P99。未启动 GPU 作业。
- 仓库文件：历史目录、`scripts/bench_strict_4k64k.sh`、`scripts/run.sh`；新增补包尚未公开入库。补包还含 JobID 934852 服务日志与三份后续 ShareGPT 目录。早期 ShareGPT 运行失败/中断；warp1 C1 与恢复后的 C4/C16/C32/C64 分属不同服务会话，不能拼作统一正式成绩。
- 赛题详情核对：用户提供的 PDF 第 1—4 页指定 SGLang 2 卡、ShareGPT 与固定长度随机负载，以及输出吞吐、TTFT、TPOT 和 SLA 最大并发；第 7—9 页列出 BW100/K100-AI 的 ShareGPT C1/4/16/32/64、4K C1/8/16/32/64/128、64K C1/8/16/32 基线与各自 SLA。30 轮 934852 日志的场景和档位与随机负载表对应，但官方镜像/脚本来源尚未证实，PDF 没有 BW1000 基线或 SLA，也把综合评分归一化方法留待最终文档。第 2 页四项精度最低值见 `report.md`；本地无对应原始精度输出。
- 自测基线核验：用户确认 BW1000 使用自测基线。10 月 7 日 4K/64K 三轮历史日志可作基线候选，与 JobID 934852 对应的全部 30 轮 `benchmark_args` 除输出路径外一致；但候选目录仅有 benchmark 输出，尚无当时服务启动、同节点硬件驱动/软件环境、官方镜像及框架默认参数的原件，不能据此认定满足自测基线三条规则。ShareGPT 历史候选与 10 月 16 日复测的五档客户端参数也除输出路径外一致；后续 warp1 结果再多服务端口差异 18580→18581，且跨会话。上述一致性不证明服务端配置或同窗环境相同。
- 阻塞/下一步：请补充或定位基线服务启动日志、节点/驱动环境快照、官方镜像/默认配置与脚本来源、四类原始日志；确认 BW1000 SLA 和最终评分口径，并核实代码实际生效及 ShareGPT 正式统一运行。需要新计算任务时另行明确授权。用户现要求不要卡在单一问题上；因此只推进不依赖 P0-01 的静态证据整理，后续事项不标 DONE。
- 补充修改：`report.md` 已加入从现有原始日志重算的 4K/64K 历史基线表、单轮 4K 复测表及 ShareGPT P99；10 行基线、4 行 4K 复测与 5 行 ShareGPT 数值逐项用原始 `.log` 验证通过。新补包到位后，另增 JobID 934852 的 10 行三轮均值和 ShareGPT 分会话说明。此前非交互 SSH 无法解析 `zz-login02`；材料由用户自行上传。
- 新发现：重新核对原始压缩包 `submission_materials_20261017_155641.tar.gz` 后，找回独立 C64 单轮 `c64.log` 与 `c64.jsonl`，两者与已解压副本逐字节一致，SHA256 分别为 `eb648fe9409742f41a53047b35b46afe3140fd5d46edfa5971db73c420226f81`、`35cf26d1da3a2198163dda8b7408f7ee688209243bde16336e2e7585ad304a05`。已保留原件并复制入 `source/results/final_4k_c64_20261017_020528/`。日志记载 C64、128 成功请求、599.19 tok/s、TTFT 18836.21 ms、TPOT 71.75 ms、P99 E2E 179577.53 ms；`.jsonl` 汇总字段与日志一致。其 backend=`sglang`，历史基线 C64 为 `sglang-oai-chat`，且只有单轮，不能计算正式提升率。
- 旧原始压缩包中的 `strict_4k64k_job933420/` 只有完整 4K C1 三轮及 C8 run1，C8 run2 中断；`strict_4k64k_job934173/` 只有服务日志。这些是部分/中断测试，不能代替现已补到的 934852。赛题规则文本把精确评测口径指向飞书详情页；该页跳转登录，正式协议未核实。
- 已验证的历史值（仅为基线/跨会话复测）：直接解析每份 `c*_run*.log` 的 `Successful requests` 与 `Output token throughput`。4K 基线 C1/8/16/32/64/128 均有 3 轮，成功请求每轮分别 8/16/32/64/128/256，三轮平均吞吐依次 26.44/218.96/368.24/555.59/559.95/606.17 tok/s；64K 基线 C1/8/16/32 均有 3 轮，成功请求每轮 8/16/32/64，平均吞吐 17.51/47.08/48.56/47.44 tok/s。与 DCU `基线.md` 吞吐列一致。ShareGPT 历史基线五档各单轮 1000 成功请求，吞吐 21.15/80.30/184.24/239.20/281.84；10/16 复测五档各单轮 1000 成功请求，吞吐 25.38/112.07/320.15/467.39/570.86。**只验证这些日志中的成功数和吞吐，不代表官方协议、同环境或最终成绩通过验收。**

### P0-02 硬件、驱动和软件环境声明 — BLOCKED，P0（最后更新：2026-10-18 CST）

- 完成标准：`env_declare.yaml` 的关键字段对应正式测试的同节点快照与模型校验原件，未知项明确标记。
- 已检查/验证：现有 YAML 保留 TODO。DCU 汇总称 JobID 935993 节点 `a01r3n15` 有 8 张显示为 `BW` 的 HCU、驱动 `6.3.31-V1.5.0a`、DTK 26.04、HSW 拓扑，且模型 33 文件清单；**该节点快照不是 JobID 934852 的正式测试证据**。DAS 25.6 仅为可用模块线索，33 条完整 OK 校验日志未见。
- 仓库文件：`env_declare.yaml`；较早不完整运行的 `source/results/strict_formal_20261017_155319/provenance.txt`。正式测试原件：用户补包 `q38_late_results.tar.gz` 内 `results/strict_4k64k_job934852/provenance.txt`（包 SHA256 见 P0-01）。该文件直接记录节点 `a01r3n19`、JobID `934852`、服务 PID `653002`、启动时间、TP=2、BF16、SGLang/Torch/Triton 版本及启动参数；已据此校正 YAML 的启动来源和可证字段。另有旁证：`C:/Users/admin/Desktop/DCU/Qwen38_DCU_优化与实验记录汇总.md`。
- 未解决/下一步：找回正式测试时 `hy-smi`、CPU/内存/OS、驱动、模块、权重 SHA256 验证全文；确认 BW1000 组别和所用 HCU 编号。未知字段不能由 935993 旁证覆盖。Feishu 赛题详情链接经联网只读访问返回不可访问，搜索该页面标识也没有结果；无法独立核实官方细则。当前 Windows 机器不是集群计算节点，不能从本机硬件代填。没有对 `env_declare.yaml` 填入未证实值。
- 补充修改：`report.md` 明确列出 935993 快照与正式测试不是同一作业；`env_declare.yaml` 在拓扑、驱动、模型哈希的 TODO 旁标注 DCU 汇总提供的线索及为什么不能代填。正式字段继续保留 TODO。

### P0-03 精度评测与结果证据 — BLOCKED，P0（最后更新：2026-10-18 CST）

- 完成标准：核实官方 BF16 精度协议；有最终方案的配置、逐题原始输出、汇总和阈值判定。
- 已检查/验证：在 DCU 文件夹和已知本地项目文件中按 GSM8K、MathVision、LiveCodeBench、accuracy 等文件名搜索，没有找到原始逐题结果。赛题 PDF 第 2 页列 GSM8K、LiveCodeBench v6、RealWorldQA、MathVision (Without CI) 准入值 95.0/88.3/83.9/88.0，降幅不超过 2 个百分点；已记录于 `report.md`。DCU `report.md` 声称 GSM8K 96.347%，但无对应原始记录，不能沿用。仓库文件：`report.md`。阻塞/下一步：提供四项精度评测原始目录、评分脚本和服务版本关联；若需新 GPU 评测，未经授权不启动。

### P0-04 固定最终优化版本与生效证据 — BLOCKED，P0（最后更新：2026-10-18 04:56 CST）

- 完成标准：正式结果可关联准确的代码 commit/patch、启动命令、进程环境和 live 文件哈希。
- 已检查/验证：`source/results/submission_audit_20261017_150109/warnings.txt` 有 `LATEST_KERNEL_NOT_PROVEN` 和 `ORIGINAL_LAUNCH_NOT_SPECIFIED`；同目录 `audit.json` 记录安装文件 SHA256 `a7e469f8…` 与 A2 baseline 相同，A3 warp2 候选为 `a9ec351b…`。DCU 汇总也明确 A2 live 文件与基线一致。DCU `代码改动.patch` 与仓库 A3 diff 的实际修改同为 `num_warps=1→2`，只是目标路径/上下文不同，不证明服务加载。阻塞/下一步：提供 JobID 934852 测试时 live 文件哈希、启动进程、安装包版本及最终代码 commit/patch 应用记录；未取得前不得宣称 A2 或该 patch 已生效。

### P0-05 正式日志与辅助证据索引 — BLOCKED，P0（最后更新：2026-10-18 CST）

- 完成标准：正式成绩可沿索引追到原始日志、命令、环境、时间戳及至少三张真实截图；保留历史/失败记录。
- 已检查/验证：`source/results/` 的 4K 基线有 33 份 `.log`、18 份 `.jsonl`；64K 基线 20 份 `.log`、12 份 `.jsonl`；ShareGPT 基线 13 份 `.log`、5 份 `.jsonl`；10/16 ShareGPT 复测 11 份 `.log`、5 份 `.jsonl`；10/17 `final_retest` 6 份 `.log`、4 份 `.jsonl`；15:53 `strict_formal` 只有 1 份 `.log`、无 `.jsonl`。仓库未找到截图图像、硬件原始输出、JobID 934852 目录或精度目录。`logs/` 不存在；不为形式复制或重命名。
- 现有证据索引：历史基线→`source/results/sglang_bf16_4k_20261007_163756/`、`sglang_bf16_64k_20261007_201746/`、`sglang_bf16_sharegpt_893107/`；跨会话复测→`source/results/sharegpt_retest_20261016_011410/`；部分复测→`source/results/final_retest_20261017/`；不完整严格运行→`source/results/strict_formal_20261017_155319/`；代码/启动审计→`source/results/submission_audit_20261017_150109/`。用户补包内 `results/strict_4k64k_job934852/` 是已核验 30 轮 4K/64K 实测原件；同包 `sharegpt_baseline_envfix_20261017_165431/` 和 `sharegpt_retest_hcu23_20261017_190126/` 为中断/失败记录，`sharegpt_warp1_baseline_20261017_213815/` 与其 resume 子目录跨会话。补包尚未公开入库，**尚无目录可被标为赛事已验收最终成绩。**
- 阻塞/下一步：补齐正式服务、benchmark、硬件驱动、结束统计及时间戳四类原始日志和至少 3 张真实截图，随后按最终成绩建索引；不得用 DCU 整理文字替代原件。

### P0-06 最终报告与论坛材料 — BLOCKED，P0（最后更新：2026-10-18 11:43 CST）

- 完成标准：五段报告数字均有原始证据，论坛正文及附件符合核实后的规则。
- 已检查/验证：现有 `report.md` 明确为草稿；DCU `report.md` 有 BW100/BW1000 冲突及无原件 GSM8K 结论。依赖 P0-01 至 P0-05，不能据整理稿改为最终报告；用户已授权更新 GitHub 仓库，论坛回复仍未授权且材料未完成。下一步待证据补齐后修订。
- 补充修改：在原五段式 `report.md` 中加入已核验历史结果、环境旁证的归属边界和精度证据缺口；JobID 934852 原始日志随后已收到并加入本地核验表。`README.md` 提供补充核验入口。仍不是最终论坛正文。

### P1-01 复现脚本、依赖和说明 — NOT_STARTED，P1（最后更新：2026-10-18 04:53 CST）

- 完成标准：脚本、依赖、路径、许可证和 README 与最终方案一致，静态检查通过。仓库文件：`scripts/`、`requirements.txt`、`README.md`。依赖 P0 定稿；可先作只读静态盘点。

### P1-02 最终提交前审计 — NOT_STARTED，P1（最后更新：2026-10-18 04:53 CST）

- 完成标准：所有必需证据、数值、敏感信息、论坛材料和清单状态逐项复核；出具真实验收结论。依赖前项，不提前标 DONE。

## 操作记录（追加）

- 2026-10-18 04:53 CST，P0-00 开始并完成：只读克隆公开仓库，核对 `git status`、HEAD、远端和目录；读取主要文件、DCU 五份原件和赛事规则提取文本；只读查询两个参考仓库根目录；创建本清单。克隆前后原始日志均未修改。结论：盘点可追溯，P0-00 DONE。
- 2026-10-18 04:53 CST，P0-01 检查后阻塞：本地缺 JobID 934852 原始目录，官方细则未独立核实；无 GPU 作业启动。P0-01 BLOCKED，转向安全独立的现有材料核验。
- 2026-10-18 04:56 CST，P0-01 追加核验：逐轮解析既有日志，确认 4K/64K 基线各档三轮成功数及吞吐均值、ShareGPT 两组单轮各 1000 成功请求及吞吐；与 DCU 汇总相符。未改变任何原始文件；不将其当正式优化成绩。
- 2026-10-18 04:56 CST，P0-02 检查后阻塞：935993 旁证不能补正式同窗环境；Feishu 详情页面无法读取；env YAML 保持原样。
- 2026-10-18 04:56 CST，P0-03 检查后阻塞：已知本地目录无精度原始文件，DCU GSM8K 数值不采用。
- 2026-10-18 04:56 CST，P0-04 检查后阻塞：审计安装内核仍是基线哈希，候选 patch 只证源码差异、不证生效。
- 2026-10-18 04:56 CST，P0-05 检查后阻塞：建立现有目录索引并统计日志/JSONL，缺最终原件和截图；未复制或改写历史结果。P0-06 因依赖阻塞。
- 2026-10-18 04:56 CST，为使本地成果直接可查看，将完整工作克隆从 `work/submission-night/` 移到 `outputs/qwen38-bw1000-sglang-submission-reviewed/`；先确认目标不存在且两路径均在工作区内。仅移动本次克隆和本清单，没有移动或改写用户原始材料。修正清单中的外部证据路径。
- 2026-10-18 04:57 CST，停止前核验：`git status --short` 只有新建的 `SUBMISSION_CHECKLIST.md`；HEAD 仍为 `31efab2…`，`git diff --check` 无报错，DCU 原件仍在且抽检 `代码改动.patch` SHA256 与盘点时一致。P0-01 至 P0-06 剩余均缺原件、官方细则或存在依赖；P1-01/P1-02 依赖 P0 定稿。不存在可安全独立完成的后续事项，保存断点结束。
- 2026-10-18 11:34 CST，用户明确要求将已整理内容放到 GitHub，覆盖此前夜间暂不推送的限制。远端 `main` 仍为盘点基准 commit `31efab2…`，且远端尚无本清单；本次发布范围仅为本文件。命令行 Git 凭据不可用，改用已连接的 GitHub 授权发布。发布结果须以远端读取验证。
- 2026-10-18 11:39 CST，用户澄清要上传 DCU 补充材料。把桌面 `DCU/` 五份文件按原名、原字节复制到 `dcu-materials/`，逐文件 SHA256 与原件一致；新增 `dcu-materials/README.md` 说明证据地位，在根 `README.md` 中加入入口。未覆盖现有 `report.md`、`env_declare.yaml` 或原始日志；P0-01 至 P0-06 状态不因上传整理稿而升级。
- 2026-10-18 11:43 CST，用户进一步澄清需要检查缺口、补充修改并上传，而不是原封不动复制。上一步 `dcu-materials/` 仅在本地暂存，尚未发布；验证副本与桌面原件相同后删除本地副本和空目录，桌面原件保留。随后只修改已有 `README.md`、`report.md`、`env_declare.yaml` 和本清单：历史 4K/64K 三轮、单轮 4K 复测与 ShareGPT 单轮的共 19 行报告数据逐项重算并核对通过；`git diff --check` 通过。PyYAML 未安装，无法运行该库解析检查；YAML 改动仅为注释。正式结果、硬件和精度缺口仍保留 BLOCKED。
- 2026-10-18 11:46 CST，通过已连接的 GitHub 授权把上述四份修改后的文件提交到 `main`（commit `88d25661c7832610b088f58881c7254eb7c64e00`），逐文件读取远端并与本地内容比较一致；远端没有 `dcu-materials/` 原件复制目录。本地同步到该 commit 后工作树干净。本行记录的追加提交单独更新本清单。
- 2026-10-18 11:52 CST，按用户新提供的逐项执行指令从 P0-01 恢复。仓库 HEAD `284cc847a5c8f3529ebddc685201e270f2ffcd0d`、工作树初始干净；复核 Downloads 旧包和本地解压内容，发现并校验单轮 C64 原件，补入上述两份原始文件，更新 `report.md` 与 `README.md`，明确 backend 不同不能比较。正式 934852 与官方协议仍缺；停留在 P0-01，不进入 P0-02。
- 2026-10-18，尝试发布上述本地修改时，GitHub 自动审批因公开原始日志含集群路径和配置、公开原件的授权不够明确而拒绝创建 commit。远端 `main` 未更新；本地 `README.md`、`report.md`、本清单及两份 C64 原件尚未提交。当时等待 934852 与官方协议材料，不绕过审批限制。
- 2026-10-18 12:02 CST，收到用户补包与飞书链接。安全检查压缩包并校验 30 轮 4K/64K 原始日志及 JSONL；更新报告和本清单。ShareGPT 结果按失败、独立 C1 和恢复后四档分别记录。飞书链接在网页工具不可访问、应用内浏览器跳转登录；已请用户登录或上传 PDF/截图。P0-01 维持 BLOCKED；本地修改尚未提交或推送。
- 2026-10-18 12:07 CST，采用较窄的公开范围，仅将核验后的 `README.md`、`report.md` 和本清单发布到 GitHub `main`；原始 C64 日志和用户补包未上传。远端 compare 显示相对上一提交仅上述 3 个文档变化；本地已同步到 `8dea39c…`，剩余未跟踪文件只有两份 C64 原件。GitHub 对原始日志的自动审批拒绝仍有效。
- 2026-10-18 12:12 CST，用户上传 11 页赛题详情 PDF；逐页渲染阅读后核对 SGLang 场景、档位、精度门槛及 BW100/K100-AI 性能基线和 SLA。PDF 末页有 AI 生成内容说明，且未列 BW1000 基线/SLA 或最终评分权重。更新 README、报告和 P0-01 清单，维持 BLOCKED；未运行新 benchmark。
- 2026-10-18 12:18 CST，用户明确 BW1000 使用自测基线。按赛事规则重查候选材料：10 月 7 日历史基线有三轮 benchmark 输出，逐轮比较 30 组 benchmark 参数与 934852 除输出路径外相同；但缺候选测试当时服务、同机环境与官方默认配置原件。修订 README、报告和 P0-01 阻塞原因；未把候选升级为合规基线，也未启动新计算。
- 2026-10-18 12:45 CST，继续 P0-01 静态检查：934852 的 30 份正式 JSONL 各只有单行汇总，ShareGPT 五份结果亦同；`output_details=False`。据此明确“日志与 JSONL 指标一致”并非“从逐请求数据独立重算 P99”；更新报告与本清单，等待用户整理的基线包。
- 2026-10-18 12:45 CST，继续 P0-01 客户端参数核验：ShareGPT 历史候选与 10 月 16 日复测五档一致；warp1 五档除端口外也一致，但跨服务会话。只证明客户端测试参数相似，未升级正式对照结论。
- 2026-10-18，用户要求加快并在 P0-01 等待基线材料期间推进独立事项。P0-02：复核补包中 934852 `provenance.txt`，校正 `env_declare.yaml`、`report.md` 和 `README.md` 的正式启动证据来源，补入 JobID、节点、PID、时间及可证启动参数；未填驱动、CPU、镜像、模型哈希。P0-03：将 PDF 四项精度门槛与缺少逐题原件的状态写入清单。P0-05：补上 934852 和 ShareGPT 失败/分会话目录的索引，保持 BLOCKED。未启动 GPU 作业，未改原始日志。

## 断点恢复

先读取本清单，检查 GitHub `main` 与本地文件是否一致，再验证上述证据仍存在。已收到的赛题 PDF 原件位于用户桌面；后续补包原件位于用户 Downloads，解压副本位于 `work/q38_late_results/`。`source/results/final_4k_c64_20261017_020528/` 两份原始文件仍为本地未跟踪文件。**论坛回复仍未发布**。优先补齐 BW1000 自测默认基线的同机、同软件环境、官方配置与原始日志证据；同时允许推进不依赖该证据的静态核验。P0-02/P0-03/P0-05 均未达到 DONE，P1-01/P1-02 仍未启动。

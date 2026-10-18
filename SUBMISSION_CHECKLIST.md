# Qwen3.8-27B BW1000 / SGLang 提交主清单

最后更新：2026-10-18 11:46 CST。仓库：https://github.com/02xdcl/qwen38-bw1000-sglang-submission；本地分支 `main`；盘点基准 commit `31efab25081f461bc92c16b90ef80bc7a2b5d116`。当前执行事项：P0-01（BLOCKED，等待原始结果；P0-02 至 P0-06 的安全独立核验也已记录阻塞）。完成进度：1/9 项 DONE。**本文件是唯一进度主清单。**

## 状态与证据规则

状态只用 `NOT_STARTED`、`IN_PROGRESS`、`BLOCKED`、`DONE`、`NOT_APPLICABLE`。`C:/Users/admin/Desktop/DCU/` 中五份材料是用户提供的二次整理材料；除非有对应原始日志、进程/环境快照及测试配置，不把其中结论升格为正式成绩。仓库 `source/` 为 2026-10-17 15:56 之前提供的原始材料；新材料不覆盖它。用户夜间授权本地可逆整理，禁止远程修改、高开销 GPU 任务及覆盖原始结果。

## 项目基线与来源区分

- 已有：`README.md`、`report.md`、`env_declare.yaml`、`requirements.txt`、`scripts/run.sh`、`scripts/bench_strict_4k64k.sh`；`source/results/` 有历史 4K、64K、ShareGPT 基线、10/16 ShareGPT 复测、10/17 不完整严格复测及审计；`source/experiments/` 有 A9/A10/A11/A13 探索实验。克隆时工作树干净，仓库跟踪文件 198 个；没有 `patch/`、`logs/` 或原有 `SUBMISSION_CHECKLIST.md`。
- 用户提供的赛事规则文本（本地 `C:/Users/admin/Documents/Codex/2026-10-17/we/work/requirements.md`，源于 `拿.docx`）要求五段式报告、四类原始日志、至少三张含命令上下文和时间戳的截图，以及论坛《作品提交专区》回复；文本写明截止 2026-10-18 17:59。该文本将 BW100 列为先锋组、其他卡型列为开放组；**BW1000 的组别需按论坛最新说明确认**。文本中的赛事细节链接、官方基线与精度阈值尚未独立核对；不能把文本外推为已核实的测试协议。
- 参考仓库只用于目录组织对照：[myrfy001/qwen38-k100ai-sglang](https://github.com/myrfy001/qwen38-k100ai-sglang) 根目录有 `bench/`、`config/`、`kernels/`、`logs/`、`patch/`、`scripts/`、`report.md`、`env_declare.yaml`；[codingmiao/q38-k100ai-submission](https://github.com/codingmiao/q38-k100ai-submission) 有 `config/`、`logs/`、`patch/`、`result/`、`scripts/`、`论坛提交回复.md`。这不是本项目的成绩或官方要求。
- DCU 整理稿 `优化后.md` 声称 JobID 934852 的 64K/C128 三轮及 ShareGPT 为优化版正式结果，但本地已知材料中没有 `strict_4k64k_job934852/` 原始目录。`Qwen38_DCU_优化与实验记录汇总.md` 同时指出 live A2 内核哈希与基线相同，无法证明 A2 被正式服务加载。`report.md` 写 BW100 ×2，与用户确认的 BW1000 冲突；其 GSM8K 数值缺原始评测。`代码改动.patch` 仅含 `num_warps=1→2`，不证明正式服务已加载。不能将这些材料直接覆盖仓库 `report.md`。

## 逐项清单

### P0-00 建立项目基线与现状盘点 — DONE，P0（最后更新：2026-10-18 04:53 CST）

- 完成标准：仓库身份、Git 状态、主要文件、现有证据、官方文本与参考仓库区别、缺项和顺序均可追溯。
- 已完成/验证：核查 `git status`、`git rev-parse HEAD`、`git remote -v`、根目录及 `source/results/`、`source/experiments/`；阅读 README、报告、环境声明、依赖、两份主脚本、审计警告、五份 DCU 材料；通过 GitHub 只读接口查看两个参考仓库根目录。克隆时无未提交修改；本清单创建前确认不存在同名文件。
- 仓库文件：`README.md`、`report.md`、`env_declare.yaml`、`requirements.txt`、`scripts/`、`source/results/submission_audit_20261017_150109/warnings.txt`。
- 原始证据：`source/results/` 下历史日志；官方规则文本 `C:/Users/admin/Documents/Codex/2026-10-17/we/work/requirements.md`；DCU 五份原件位于 `C:/Users/admin/Desktop/DCU/`，均未改动。
- 未解决：赛事链接/最新论坛细则未独立核验；不妨碍完成现状盘点。下一步 P0-01。

### P0-01 最终正式性能测试 — BLOCKED，P0（最后更新：2026-10-18 11:43 CST）

- 完成标准：官方测试范围已核实；4K、64K、ShareGPT 必要档位的真实原始日志、逐请求结果、成功数、P99/SLA、计算汇总及同一运行配置关联齐全。
- 已检查/验证：`source/results/sglang_bf16_4k_20261007_163756/`、`sglang_bf16_64k_20261007_201746/`、`sglang_bf16_sharegpt_893107/` 为历史基线；`final_retest_20261017/` 是部分复测；`strict_formal_20261017_155319/` 不完整。DCU 的 JobID 934852 声称未找到对应本地原始目录；搜索 DCU、`C:/Users/admin/Documents/Codex/2026-10-17/we/work/source_package/` 及本仓库均未发现。未启动 GPU 作业。
- 仓库文件：上述目录、`scripts/bench_strict_4k64k.sh`、`scripts/run.sh`。原始证据缺口：`results/strict_4k64k_job934852/` 与后续 ShareGPT 结果包，正式服务日志与同窗环境、官方测试协议。
- 阻塞/下一步：请提供 JobID 934852 完整目录及其服务日志、后续 ShareGPT 原始目录；确认官方 benchmark 指标/轮数/阈值。需要新计算任务时另行明确授权。可先独立核验 P0-02 至 P0-05 的现有材料。
- 补充修改：`report.md` 已加入从现有原始日志重算的 4K/64K 历史基线表、单轮 4K 复测表及 ShareGPT P99；10 行基线、4 行 4K 复测与 5 行 ShareGPT 数值逐项用原始 `.log` 验证通过。DCU 整理稿所列 JobID 934852 和独立 C64 后续结果仍因原件缺失而未纳入正式表。尝试以非交互 SSH 访问 `zz-login02`，本机无法解析该主机名，不能直接从集群取回缺失日志。
- 已验证的历史值（仅为基线/跨会话复测）：直接解析每份 `c*_run*.log` 的 `Successful requests` 与 `Output token throughput`。4K 基线 C1/8/16/32/64/128 均有 3 轮，成功请求每轮分别 8/16/32/64/128/256，三轮平均吞吐依次 26.44/218.96/368.24/555.59/559.95/606.17 tok/s；64K 基线 C1/8/16/32 均有 3 轮，成功请求每轮 8/16/32/64，平均吞吐 17.51/47.08/48.56/47.44 tok/s。与 DCU `基线.md` 吞吐列一致。ShareGPT 历史基线五档各单轮 1000 成功请求，吞吐 21.15/80.30/184.24/239.20/281.84；10/16 复测五档各单轮 1000 成功请求，吞吐 25.38/112.07/320.15/467.39/570.86。**只验证这些日志中的成功数和吞吐，不代表官方协议、同环境或最终成绩通过验收。**

### P0-02 硬件、驱动和软件环境声明 — BLOCKED，P0（最后更新：2026-10-18 11:43 CST）

- 完成标准：`env_declare.yaml` 的关键字段对应正式测试的同节点快照与模型校验原件，未知项明确标记。
- 已检查/验证：现有 YAML 保留 TODO。DCU 汇总称 JobID 935993 节点 `a01r3n15` 有 8 张显示为 `BW` 的 HCU、驱动 `6.3.31-V1.5.0a`、DTK 26.04、HSW 拓扑，且模型 33 文件清单；**该节点快照不是 JobID 934852 的正式测试证据**。DAS 25.6 仅为可用模块线索，33 条完整 OK 校验日志未见。
- 仓库文件：`env_declare.yaml`、`source/results/strict_formal_20261017_155319/provenance.txt`。原件：`C:/Users/admin/Desktop/DCU/Qwen38_DCU_优化与实验记录汇总.md`。
- 未解决/下一步：找回正式测试时 `hy-smi`、CPU/内存/OS、驱动、模块、权重 SHA256 验证全文；确认 BW1000 组别和所用 HCU 编号。未知字段不能由 935993 旁证覆盖。Feishu 赛题详情链接经联网只读访问返回不可访问，搜索该页面标识也没有结果；无法独立核实官方细则。当前 Windows 机器不是集群计算节点，不能从本机硬件代填。没有对 `env_declare.yaml` 填入未证实值。
- 补充修改：`report.md` 明确列出 935993 快照与正式测试不是同一作业；`env_declare.yaml` 在拓扑、驱动、模型哈希的 TODO 旁标注 DCU 汇总提供的线索及为什么不能代填。正式字段继续保留 TODO。

### P0-03 精度评测与结果证据 — BLOCKED，P0（最后更新：2026-10-18 04:56 CST）

- 完成标准：核实官方 BF16 精度协议；有最终方案的配置、逐题原始输出、汇总和阈值判定。
- 已检查/验证：在 DCU 文件夹和已知本地项目文件中按 GSM8K、MathVision、LiveCodeBench、accuracy 等文件名搜索，没有找到原始逐题结果。DCU `report.md` 声称 GSM8K 96.347%，但无对应原始记录；不能沿用。仓库文件：`report.md`。阻塞/下一步：提供精度评测原始目录和官方协议；若需新 GPU 评测，夜间规则禁止未经授权启动。

### P0-04 固定最终优化版本与生效证据 — BLOCKED，P0（最后更新：2026-10-18 04:56 CST）

- 完成标准：正式结果可关联准确的代码 commit/patch、启动命令、进程环境和 live 文件哈希。
- 已检查/验证：`source/results/submission_audit_20261017_150109/warnings.txt` 有 `LATEST_KERNEL_NOT_PROVEN` 和 `ORIGINAL_LAUNCH_NOT_SPECIFIED`；同目录 `audit.json` 记录安装文件 SHA256 `a7e469f8…` 与 A2 baseline 相同，A3 warp2 候选为 `a9ec351b…`。DCU 汇总也明确 A2 live 文件与基线一致。DCU `代码改动.patch` 与仓库 A3 diff 的实际修改同为 `num_warps=1→2`，只是目标路径/上下文不同，不证明服务加载。阻塞/下一步：提供 JobID 934852 测试时 live 文件哈希、启动进程、安装包版本及最终代码 commit/patch 应用记录；未取得前不得宣称 A2 或该 patch 已生效。

### P0-05 正式日志与辅助证据索引 — BLOCKED，P0（最后更新：2026-10-18 04:56 CST）

- 完成标准：正式成绩可沿索引追到原始日志、命令、环境、时间戳及至少三张真实截图；保留历史/失败记录。
- 已检查/验证：`source/results/` 的 4K 基线有 33 份 `.log`、18 份 `.jsonl`；64K 基线 20 份 `.log`、12 份 `.jsonl`；ShareGPT 基线 13 份 `.log`、5 份 `.jsonl`；10/16 ShareGPT 复测 11 份 `.log`、5 份 `.jsonl`；10/17 `final_retest` 6 份 `.log`、4 份 `.jsonl`；15:53 `strict_formal` 只有 1 份 `.log`、无 `.jsonl`。仓库未找到截图图像、硬件原始输出、JobID 934852 目录或精度目录。`logs/` 不存在；不为形式复制或重命名。
- 现有证据索引：历史基线→`source/results/sglang_bf16_4k_20261007_163756/`、`sglang_bf16_64k_20261007_201746/`、`sglang_bf16_sharegpt_893107/`；跨会话复测→`source/results/sharegpt_retest_20261016_011410/`；部分复测→`source/results/final_retest_20261017/`；不完整严格运行→`source/results/strict_formal_20261017_155319/`；代码/启动审计→`source/results/submission_audit_20261017_150109/`。**无目录可被标为已核实最终成绩。**
- 阻塞/下一步：补齐正式服务、benchmark、硬件驱动、结束统计及时间戳四类原始日志和至少 3 张真实截图，随后按最终成绩建索引；不得用 DCU 整理文字替代原件。

### P0-06 最终报告与论坛材料 — BLOCKED，P0（最后更新：2026-10-18 11:43 CST）

- 完成标准：五段报告数字均有原始证据，论坛正文及附件符合核实后的规则。
- 已检查/验证：现有 `report.md` 明确为草稿；DCU `report.md` 有 BW100/BW1000 冲突及无原件 GSM8K 结论。依赖 P0-01 至 P0-05，不能据整理稿改为最终报告；用户已授权更新 GitHub 仓库，论坛回复仍未授权且材料未完成。下一步待证据补齐后修订。
- 补充修改：在原五段式 `report.md` 中加入已核验历史结果、环境旁证的归属边界、缺失 JobID 934852 原始证据和精度结果的明确说明；`README.md` 提供补充核验入口。仍不是最终论坛正文。

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

## 断点恢复

先读取本清单，检查 GitHub `main` 与本地文件是否一致，再验证上述证据仍存在。本轮已发布 `README.md`、`report.md`、`env_declare.yaml` 和本清单的补充修改；没有新增原始日志或精度结果。**论坛回复仍未发布**。优先补充 JobID 934852/后续 ShareGPT 原始结果、正式服务与环境日志、精度原件及论坛规则链接或截图；再从 P0-01 恢复。P1-01 依赖 P0 定稿，P1-02 为最后审计，均未启动。

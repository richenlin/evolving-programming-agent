---
# Evolving Programming Agent — 综合架构评估报告
> 评估视角：资深软件架构师  
> 评估标准：skill-creator 官方规范 + 软件工程最佳实践  
> 参考基线：docs/architecture-review.md（v6.0 前次评估）  
> 日期：2026-03-02
---
一、项目概况
| 维度     | 数据                                                                      |
| -------- | ------------------------------------------------------------------------- |
| 定位     | 自我进化的 AI 编程智能体，以 Skill 形式运行于 OpenCode/Claude Code/Cursor |
| 架构版本 | v6.0 多 Agent 编排                                                        |
| 规模     | ~50 文件, 7240 行 Python, 3013 行 Markdown                                |
| 测试     | 27 个测试文件, 148 passed / 3 skipped, 72% 行覆盖率                       |
| 核心依赖 | Python >= 3.8, PyYAML; 可选: jieba, sentence-transformers                 |
核心理念：不仅仅是代码生成工具，而是通过 "编排→编码→审查→进化" 四段式闭环，每次编程任务积累经验，持续增强自身能力。
---
二、架构全景
Layer 0 · 入口        SKILL.md (意图识别 → 路由分发)
                           │
Layer 1 · 模块    ┌────────┼────────┐
             programming  knowledge  github-to
             -assistant    -base     -knowledge
                  │
Layer 2 · Agent orchestrator → coder → reviewer → evolver
                                            ↑
                                        retrieval (并行)
                  │
Layer 3 · 脚本   run.py (统一CLI)
             core/  knowledge/  github/  programming/
                  │
Layer 4 · 基础设施 install.sh · schema.json · 跨平台路径 · config.py
5 Agent 角色：
| Agent        | 模型              | 权限        | 文件                          |
| ------------ | ----------------- | ----------- | ----------------------------- |
| orchestrator | GLM-5             | 只读+Task   | agents/orchestrator.md (88行) |
| coder        | GLM-5             | 全权限      | agents/coder.md (66行)        |
| reviewer     | claude-sonnet-4.6 | 只读+git    | agents/reviewer.md (127行)    |
| evolver      | GLM-5             | 只写知识库  | agents/evolver.md (68行)      |
| retrieval    | GLM-5             | 只写context | agents/retrieval.md (53行)    |
---
三、与 skill-creator 官方规范的符合度评估
3.1 SKILL.md 规范
| 检查项                   | 标准要求                            | 当前状态                      | 评级   |
| ------------------------ | ----------------------------------- | ----------------------------- | ------ |
| Frontmatter 必须字段     | name + description                  | 有                            | ✅      |
| Frontmatter 禁止额外字段 | 只允许 name/description             | 含 license, metadata.triggers | ⚠️ 违规 |
| Description 包含触发条件 | 在 description 中说明何时触发       | 有触发词列表                  | ✅      |
| Body < 500 行            | 保持精简                            | 205 行                        | ✅      |
| 渐进披露                 | 核心流程在 SKILL.md, 详细委托子文件 | 完美遵循                      | ✅      |
问题：Frontmatter 中 license: MIT 和 metadata.triggers: [...] 不在标准允许范围内。标准明确说 "Do not include any other fields in YAML frontmatter."
3.2 目录结构规范
| 检查项            | 标准结构           | 当前结构                                               | 评级   |
| ----------------- | ------------------ | ------------------------------------------------------ | ------ |
| SKILL.md 必须存在 | 根目录             | evolving-agent/SKILL.md                                | ✅      |
| scripts/ 目录     | 可执行脚本         | scripts/ (含 core/, knowledge/, github/, programming/) | ✅      |
| references/ 目录  | 按需加载的参考文档 | agents/references/ (非标准路径)                        | ⚠️ 偏离 |
| assets/ 目录      | 模板等输出资源     | 无 (不需要)                                            | ✅      |
| 禁止 README.md    | 不创建额外文档     | 存在 3 个 README.md (modules下)                        | ⚠️ 违规 |
问题：
1. agents/references/ 是非标准路径（标准是 references/ 在 skill 根目录下）
2. modules/programming-assistant/README.md、modules/knowledge-base/README.md、modules/github-to-knowledge/README.md 按标准不应存在。但在本项目中它们充当模块入口文档，功能上等价于 references 文件。
3.3 渐进披露（Progressive Disclosure）
| 层级                  | 标准要求                    | 当前实现                                                   | 评级 |
| --------------------- | --------------------------- | ---------------------------------------------------------- | ---- |
| L1: Metadata          | name + description (~100词) | 49 词 description                                          | ✅    |
| L2: SKILL.md body     | 触发后加载 (<5k词)          | 205 行, ~1500 词                                           | ✅    |
| L3: Bundled resources | 按需加载                    | 模块 README → workflow md → agent md → reference checklist | ✅    |
渐进披露设计优秀。SKILL.md 只定义主进程 6 步骤，具体实现委托给子文件。_base.md 提取公共内容避免重复。
3.4 总体符合度评分
| 维度             | 得分 (1-10) | 说明                     |
| ---------------- | ----------- | ------------------------ |
| Frontmatter 规范 | 7           | 有额外字段               |
| 目录结构         | 6           | 自定义结构合理但偏离标准 |
| 渐进披露         | 9           | 多层递进，设计精良       |
| 资源组织         | 8           | 脚本有测试，引用有体系   |
| 简洁性           | 6           | 总量偏大，有冗余文件     |
| 综合             | 7.2         | 功能强大但不够精简       |
---
四、架构强项（8 项）
1. Python 强制状态机 ⭐
task_manager.py (317行) 实现了 pending → in_progress → review_pending → completed/rejected 的硬约束状态机。支持幂等转换（相同状态不报错）和完整审计日志。coder 无法跳过 reviewer 直接标记 completed——这是整个架构最关键的安全保障。
2. 原子文件操作
file_utils.py (82行) 使用 tempfile.mkstemp() + os.fdopen() + f.flush() + os.fsync() + os.replace()——这是教科书级别的 POSIX 原子写入实现。防止多 agent 并发写入导致 JSON 损坏。
3. 四级知识检索
query.py (746行) 实现精确匹配(权重3) → 部分匹配(权重2) → 模糊匹配(SequenceMatcher, 阈值0.6) → 语义搜索(sentence-transformers, 可选)。综合相关性公式：trigger×0.4 + effectiveness×0.3 + recency×0.2 + usage×0.1。查询命中时自动更新 usage_count 和 last_used_at。
4. 知识库生命周期管理
lifecycle.py 实现 decay（90天未用衰减 effectiveness）和 gc（清理 effectiveness < 0.1 的条目）。防止知识库无限膨胀。dashboard.py 提供可视化统计。
5. 渐进披露文档架构
SKILL.md (主进程6步)
  └→ modules/programming-assistant/README.md (模式选择)
       └→ workflows/full-mode.md 或 simple-mode.md (具体流程)
            └→ workflows/_base.md (公共步骤)
                 └→ workflows/evolution-check.md (进化检查)
每层只加载必要内容，不浪费 context window。
6. 多项目知识隔离
双层架构：全局 ~/.config/opencode/knowledge/ + 项目级 $PROJECT_ROOT/.opencode/knowledge/。检索时先查项目级再查全局，按 ID 去重。项目知识随目录天然隔离。
7. 跨平台统一 CLI
run.py (832行) 是所有功能的单一入口，支持 6 个子命令（mode/knowledge/github/project/info/task）。内含环境检测、路径解析、Python 版本检查、依赖检查。
8. 严格的角色权限隔离
Agent 定义中通过 frontmatter 配置精细权限：
- orchestrator: write: false, edit: false，只允许特定 bash 命令
- reviewer: write: false, edit: false，只允许 git diff/log/show/status, cat, grep
- evolver: write: false, edit: false，只允许知识库操作
---
五、问题诊断与改进建议
P1-1: Context Window 预算过高
现象：一次完整编程任务流可能加载的总 Markdown 量：
| 文件                            | 行数  | 加载时机       |
| ------------------------------- | ----- | -------------- |
| SKILL.md                        | 205   | 触发时         |
| programming-assistant/README.md | 191   | 步骤3          |
| full-mode.md                    | 122   | 模式选择后     |
| _base.md                        | 121   | full-mode 引用 |
| evolution-check.md              | 129   | 步骤5          |
| orchestrator.md                 | 88    | agent 加载     |
| coder.md                        | 66    | agent 加载     |
| reviewer.md                     | 127   | 审查时         |
| solid-checklist.md              | 314   | reviewer 引用  |
| security-checklist.md           | ~200  | reviewer 引用  |
| quality-checklist.md            | ~200  | reviewer 引用  |
| removal-plan.md                 | ~100  | reviewer 引用  |
| evolver.md                      | 68    | 进化时         |
| 合计                            | ~1931 |                |
最坏情况下约 1931 行 Markdown 被加载到 context。skill-creator 原则说 "context window is a public good"。
建议：
1. 合并 programming-assistant/README.md + full-mode.md/simple-mode.md + _base.md 为单一文件，减少加载层次
2. 将 4 个 reviewer reference checklist 合并为一个精简版（当前 ~800 行可压缩到 ~200 行核心检查项）
3. SKILL.md 中"命令速查"和"健康检查清单"等内容可移至 references
P1-2: 死代码/遗留文件（~358 行）
| 文件                    | 行数 | 问题                                                          |
| ----------------------- | ---- | ------------------------------------------------------------- |
| core/smart_stitch.py    | 227  | 引用不存在的 evolution.json 和 programming-assistant/scripts/ |
| core/align_all.py       | 32   | 硬编码 Windows 路径 C:\Users\20515\.claude\skills             |
| core/merge_evolution.py | 99   | 引用不存在的 evolution.json                                   |
这些是 v1/v2 时代的遗留脚本，当前 v6.0 架构已完全不使用。
建议：删除这三个文件。如需保留历史，git 历史已有记录。
P1-3: 路径解析逻辑重复
get_kb_root() 函数在以下文件中各实现了一份：
- scripts/run.py:151 (get_knowledge_dir())
- scripts/core/path_resolver.py:122 (get_knowledge_base_dir())
- scripts/knowledge/query.py:124 (get_kb_root())
- scripts/knowledge/store.py:78 (get_kb_root())
每个实现都包含 "尝试 path_resolver → 环境变量 fallback → 平台检测 fallback" 的相同逻辑。
建议：统一到 path_resolver.py 一处实现。query.py 和 store.py 中的 _try_import_path_resolver() + fallback 模式可简化为直接 import（它们与 path_resolver 在同一个包内，不应存在导入失败的情况）。
P2-1: SKILL.md Frontmatter 不合规
当前：
---
name: evolving-agent
description: AI 编程系统协调器。触发词：...
license: MIT
metadata:
  triggers: ["开发", "实现", ...]
---
标准要求只有 name 和 description。
建议：删除 license 和 metadata 字段。触发词信息已包含在 description 中。
P2-2: 模块 README.md 应改为 references
skill-creator 明确说 "Do NOT create extraneous documentation files, including README.md"。
建议：
- modules/programming-assistant/README.md → references/programming-assistant.md
- modules/knowledge-base/README.md → references/knowledge-base.md
- modules/github-to-knowledge/README.md → references/github-learning.md
或者，如果保留 modules 结构，将文件名从 README.md 改为其他名称（如 guide.md），因为 README.md 暗示面向人类读者而非 AI agent。
P2-3: knowledge-base/agents/ 与顶层 agents/ 冗余
modules/knowledge-base/agents/ 包含 retrieval-agent.md 和 summarize-agent.md，功能上与顶层 agents/retrieval.md 和 agents/evolver.md 重叠。
建议：确认是否实际使用。如果只是旧版残留，删除 modules/knowledge-base/agents/ 目录。
P2-4: CATEGORY_DIRS 映射重复定义
knowledge/query.py:87-95 和 knowledge/store.py:65-73 各有一份完全相同的 CATEGORY_DIRS 字典。
建议：提取到 core/config.py 或新建 knowledge/constants.py，两处 import。
P3-1: install.sh 含交互式 read 命令
install.sh:521 有 read -p "请选择 [1-3]: " 交互式提示。在 CI/非交互环境下会挂起。虽然 --all 参数可以绕过，但违反非交互 shell 原则。
建议：当检测到非 TTY 时，默认使用 --all 或输出错误退出。
---
六、设计模式与工程实践评估
| 模式/实践    | 实现位置                           | 质量评级 | 说明                     |
| ------------ | ---------------------------------- | -------- | ------------------------ |
| 状态机模式   | task_manager.py                    | ⭐⭐⭐⭐⭐    | 转换校验、幂等、审计日志 |
| 渐进披露     | 文档层级                           | ⭐⭐⭐⭐⭐    | 多层递进、按需加载       |
| 策略模式     | query.py (keyword/semantic/hybrid) | ⭐⭐⭐⭐     | 三种搜索模式优雅切换     |
| 原子操作     | file_utils.py                      | ⭐⭐⭐⭐⭐    | 教科书 POSIX 实现        |
| 生命周期管理 | lifecycle.py                       | ⭐⭐⭐⭐     | decay + gc + dashboard   |
| 角色权限隔离 | agents/*.md frontmatter            | ⭐⭐⭐⭐     | 精细权限控制             |
| 集中配置     | config.py                          | ⭐⭐⭐⭐     | 所有阈值/权重一处管理    |
| 优雅降级     | jieba/embedding 可选               | ⭐⭐⭐⭐     | 核心功能不依赖可选包     |
---
七、前次评估跟踪
前次评估 (docs/architecture-review.md) 识别的 8 个问题：
| ID   | 问题              | 优先级 | 当前状态 | 验证方式                     |
| ---- | ----------------- | ------ | -------- | ---------------------------- |
| P0-1 | 文档即代码脆弱性  | P0     | ✅ 已解决 | task_manager.py 状态机验证   |
| P1-2 | 知识检索精度低    | P1     | ✅ 已解决 | 四级检索 + 测试覆盖          |
| P1-3 | 归纳缺乏结构化    | P1     | ✅ 已解决 | summarizer + schema 对齐测试 |
| P1-4 | 知识库只增不减    | P1     | ✅ 已解决 | lifecycle.py decay/gc        |
| P2-5 | 并发写入不安全    | P2     | ✅ 已解决 | file_utils.py atomic_write   |
| P2-6 | workflow 大量重复 | P2     | ✅ 已解决 | _base.md 提取公共部分        |
| P2-7 | 纯关键词意图识别  | P2     | ✅ 已解决 | 上下文感知路由 (步骤2.1)     |
| P3-8 | Shell 注入风险    | P3     | ✅ 已解决 | subprocess 列表形式审计      |
前次评估的所有问题均已解决，实施质量高。
---
八、总体评价
评分矩阵
| 维度       | 得分 (1-10) | 权重 | 加权分  |
| ---------- | ----------- | ---- | ------- |
| 架构设计   | 9           | 25%  | 2.25    |
| 代码质量   | 8           | 20%  | 1.60    |
| 测试覆盖   | 8           | 15%  | 1.20    |
| 文档质量   | 7           | 10%  | 0.70    |
| 规范符合度 | 7           | 15%  | 1.05    |
| 可维护性   | 7           | 15%  | 1.05    |
| 综合       |             | 100% | 7.85/10 |
一句话评价
这是一个设计精良、经过多轮迭代优化的高质量 Skill 项目。核心架构（状态机 + 原子写入 + 四级检索 + 生命周期管理）是其最大亮点。主要改进方向是：精简 context 预算、清理遗留代码、统一路径解析、向 skill-creator 标准靠拢。
---
九、优先行动建议
| 优先级 | 行动                                                       | 预估工作量 | 预期收益             |
| ------ | ---------------------------------------------------------- | ---------- | -------------------- |
| P1     | 删除 3 个遗留脚本 (smart_stitch/align_all/merge_evolution) | 10 min     | 减少 358 行死代码    |
| P1     | 统一路径解析到 path_resolver.py，消除 4 处重复             | 30 min     | 减少维护负担         |
| P1     | 精简 reviewer 参考清单（4 份 → 1 份核心清单）              | 1 hr       | 节省 ~600 行 context |
| P2     | 修正 SKILL.md frontmatter（删除 license/metadata）         | 5 min      | 符合标准             |
| P2     | 重命名/移动模块 README.md                                  | 15 min     | 符合标准             |
| P2     | 提取 CATEGORY_DIRS 到共享常量                              | 10 min     | 消除重复             |
| P3     | install.sh 非交互模式检测                                  | 10 min     | CI 友好              |
| P3     | 使用 package_skill.py 打包为 .skill 文件                   | 5 min      | 标准化分发           |
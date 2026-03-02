# Evolving Programming Agent — 综合评估报告

> 视角：资深软件工程师
> 日期：2026-03-02（更新：Phase 1~4 全部完成后）
> 版本：v6.0 架构审查（含实施结果）

---

## 一、项目概述

| 维度 | 数据 |
|------|------|
| 定位 | 自我进化的 AI 编程智能体 Skill |
| 规模 | ~45 个 Python 文件(~7000行), ~20 个 Markdown 文档, 3 个 Shell 脚本, 27 个测试文件(148 passed) |
| 架构版本 | v6.0 多 Agent 编排 |
| 支持平台 | OpenCode / Claude Code / Cursor |

**核心理念**：不只是代码生成工具，而是通过"编排→编码→审查→进化"四段式闭环，在每次编程任务中积累经验，持续增强自身能力。

---

## 二、架构全景

```
Layer 0 · 入口          SKILL.md (上下文感知路由 → 意图识别 → 路由分发)
                              │
Layer 1 · 模块     ┌──────────┼──────────┐
              programming   knowledge   github-to
              -assistant      -base      -knowledge
                   │
Layer 2 · Agent  orchestrator → coder → reviewer → evolver
                                              ↑
                                          retrieval (并行)
                   │
Layer 3 · 脚本    run.py (统一CLI)
              core/  knowledge/  github/  programming/
                   │
Layer 4 · 基础设施  install.sh · schema.json · 跨平台路径 · config.py
```

---

## 三、架构强项

### 1. Python 强制状态机 ✅（v6.0 新增）

`pending → in_progress → review_pending → completed/rejected`，由 `task_manager.py` 在 Python 层强制校验。coder 不能自审、不能跳过 reviewer，即使 LLM 试图直接修改 JSON 也会被 CLI 拒绝。支持幂等转换（重试安全）和完整审计日志。

### 2. 渐进披露的文档架构

SKILL.md 只定义主进程逻辑 → 模块 README 定义入口和原则 → workflow md 定义具体步骤。`_base.md` 提取公共内容，full-mode 和 simple-mode 只保留差异部分。

### 3. DAG 并行调度

`depends_on` 字段 + 拓扑排序 + 批次并行，这是 agent 编排的工程最优解。orchestrator 可以在单条消息中并行分发多个无依赖的 coder 任务。

### 4. 角色分离与模型专精

reviewer 用 claude-sonnet-4.6（推理强）、coder/orchestrator 用 GLM-5（执行快）。各角色权限严格限定（reviewer 只读、coder 无 review 权限）。

### 5. 多层知识检索 ✅（v6.0 新增）

四级检索：精确匹配 → 部分匹配 → 模糊匹配（SequenceMatcher + 可选 jieba 中文分词） → 语义搜索（可选 sentence-transformers embedding）。结果按综合相关性排序（触发词匹配×0.4 + effectiveness×0.3 + recency×0.2 + usage×0.1）。

### 6. 知识库生命周期管理 ✅（v6.0 新增）

`usage_count` 自动追踪 → `effectiveness` 定期衰减 → `gc` 清理低分条目。防止知识库膨胀，确保检索结果质量。

### 7. 多项目知识隔离 ✅（v6.0 新增）

双层知识库架构：
```
~/.config/opencode/knowledge/        # 全局知识（通用经验，跨项目共享）
$PROJECT_ROOT/.opencode/knowledge/   # 项目级知识（项目特有经验）
```
检索时先查项目级再查全局，按 ID 去重合并。项目知识天然随项目目录移动/删除，无需迁移脚本。

### 8. 集中配置管理 ✅（v6.0 新增）

所有可调参数集中在 `core/config.py`：衰减率、GC 阈值、模糊匹配阈值、相关性权重、top-K 数量等。各模块从 config 导入，函数参数仍可覆盖。

---

## 四、核心问题诊断与解决状态

### 问题 1（P0）：文档即代码的根本脆弱性 — ✅ 已解决

**原现象**：整个执行引擎是 Markdown 文档被 LLM "解释执行"，没有运行时强制机制。

**解决方案（S1 状态管理器）**：

`task_manager.py` 在 Python 层强制校验所有状态转换。agent 通过 CLI 命令（`run.py task transition`）而非直接编辑 JSON 操作状态。非法转换（如 `pending → completed`、非 reviewer 标记 completed）在脚本层被拒绝。

**增强**（Phase 4）：
- 幂等性转换（TASK-24）：`in_progress → in_progress` 不报错，返回当前状态
- 审计日志（TASK-25）：每次状态变更记录 `from`/`to`/`actor`/`timestamp`

### 问题 2（P1）：知识检索精度低 — ✅ 已解决

**原现象**：纯字符串匹配，无模糊匹配、无语义理解、无相关性排序。

**解决方案（T1 知识检索升级）**：

| 层级 | 机制 | 实现 |
|------|------|------|
| 精确匹配 | trigger 完全一致 | `query_by_triggers()` 权重 3 |
| 部分匹配 | trigger 包含/被包含 | 权重 2 |
| 模糊匹配 | `SequenceMatcher` | 阈值 0.6，可配置 |
| 中文分词 | `jieba`（可选依赖） | 有则用，无则 regex fallback |
| 语义搜索 | `sentence-transformers`（可选依赖） | `--mode semantic/hybrid` |
| 相关性排序 | 综合评分公式 | 触发词×0.4 + effectiveness×0.3 + recency×0.2 + usage×0.1 |

### 问题 3（P1）：知识归纳缺乏结构化 — ✅ 已解决

**原现象**：evolver 输出不规范内容，store.py 退化为平铺文本。

**解决方案（T2 归纳格式校验 + schema 对齐）**：

- `validate_input()` 检查并自动矫正输入格式（问题→解决、决策→原因、教训→避免）
- 7 个 store 函数均输出与 `schema.json` 对齐的结构化 content
- 7 个 category 全部有 schema 对齐测试覆盖

### 问题 4（P1）：知识库只增不减 — ✅ 已解决

**原现象**：`effectiveness` 和 `usage_count` 字段从未被使用。

**解决方案（S2 知识库生命周期）**：

- `update_usage()` 在每次检索命中时自动递增 `usage_count` 和更新 `last_used_at`
- `decay_unused()` 对超过 90 天未使用的条目衰减 effectiveness
- `gc()` 清理 effectiveness < 0.1 的条目（支持 `--dry-run` 预览）
- `knowledge dashboard` 可视化知识库健康状态

### 问题 5（P2）：并发写入不安全 — ✅ 已解决

**原现象**：多个 agent 可能同时写 `feature_list.json`。

**解决方案（T3 文件写入原子化）**：

`atomic_write_json()` 使用 `tempfile.mkstemp` + `os.replace()`（POSIX 原子操作）。Phase 4 进一步加固：写入后 `f.flush()` + `os.fsync(f.fileno())` 确保数据刷盘。

### 问题 6（P2）：full-mode 与 simple-mode 大量重复 — ✅ 已解决

**原现象**：两个 workflow 文件结构几乎一致。

**解决方案（D1 workflow 去重）**：

提取 `_base.md` 包含公共步骤（环境准备、审查门控、结果验证、进化检查）。full-mode.md 减少 33.5%，simple-mode.md 减少 27.3%。

### 问题 7（P2）：意图识别是纯关键词匹配 — ✅ 已解决

**原现象**：SKILL.md 只有触发词列表，无法利用上下文。

**解决方案（S3 上下文感知路由）**：

SKILL.md 步骤 2 拆分为 2.1（上下文优先检查：`run.py task status --json`）和 2.2（关键词匹配兜底）。有活跃任务时自动继续编程，不再重新路由。

### 问题 8（P3）：Shell 命令注入风险 — ✅ 已解决

**原现象**：多处使用 `echo "用户内容" | python ...`。

**解决方案（T4）**：审计确认所有 subprocess 调用已使用列表形式（非字符串拼接），无 `shell=True`，无 `os.system/os.popen`。

---

## 五、优化方案实施结果

### 方案矩阵

| ID | 方案 | 解决问题 | 状态 | 实施任务 |
|----|------|----------|------|----------|
| S1 | 状态管理器 | P0 | ✅ 完成 | TASK-01~09, 24, 25 |
| S2 | 知识库生命周期 | P1(#4) | ✅ 完成 | TASK-15~17 |
| S3 | 上下文感知路由 | P2(#7) | ✅ 完成 | TASK-20~21, 27 |
| T1 | 知识检索升级 | P1(#2) | ✅ 完成 | TASK-18~19, 28, 29 |
| T2 | 归纳格式校验 | P1(#3) | ✅ 完成 | TASK-10~11, 31 |
| T3 | 文件写入原子化 | P2(#5) | ✅ 完成 | TASK-02, 23 |
| D1 | workflow 去重 | P2(#6) | ✅ 完成 | TASK-12~14 |
| T4 | Shell 参数转义 | P3(#8) | ✅ 完成 | TASK-01 |

### 新增产品能力

| 能力 | 实施任务 | 状态 |
|------|----------|------|
| 集中配置管理 | TASK-26 | ✅ 完成 |
| 知识库导入导出 CLI | TASK-30 | ✅ 完成 |
| 知识库可视化 dashboard | TASK-33 | ✅ 完成 |
| 多项目知识隔离 | TASK-32 | ✅ 完成 |
| jieba 中文分词（可选） | TASK-28 | ✅ 完成 |
| embedding 语义搜索（可选） | TASK-29 | ✅ 完成 |

---

## 六、实施路线图（已完成）

```
Phase 1 (基础设施 + 状态管理器) ✅
├── T4: Shell 安全审计（无需改动）
├── T3: atomic_write_json + fsync
├── S1: task_manager.py + CLI + 幂等性 + 审计日志 + workflow 文档适配
└── 9 tasks, 全部 pass

Phase 2 (知识系统加固) ✅
├── T2: summarizer 格式校验
├── D1: workflow 去重 (_base.md)
└── 5 tasks, 全部 pass

Phase 3 (知识升级 + 智能路由) ✅
├── S2: 知识库生命周期 (usage_count + decay + gc)
├── T1: 模糊匹配 + 相关性排序
├── S3: 上下文感知路由 (Python + SKILL.md)
└── 8 tasks, 全部 pass

Phase 4 (进阶 + 产品能力) ✅
├── 缺陷修复: fsync, 幂等性, 审计日志
├── 重构: 集中配置
├── 文档: SKILL.md 路由修复
├── 接线: 知识库导入导出 CLI
├── 测试: store/schema 对齐验证 (7 categories)
├── 新功能: jieba 中文分词, embedding 语义搜索, dashboard, 多项目隔离
└── 12 tasks, 全部 pass
```

---

## 七、CLI 命令速查

```bash
# 状态管理器
python run.py task create --name "任务名" [--priority high] [--depends task-001,task-002]
python run.py task list [--status pending] [--json]
python run.py task transition --task-id task-001 --status in_progress [--actor reviewer]
python run.py task status [--json]

# 知识库生命周期
python run.py knowledge decay [--days-threshold 90] [--decay-rate 0.1]
python run.py knowledge gc [--threshold 0.1] [--dry-run]

# 知识库检索
python run.py knowledge query --trigger "react,hooks" [--mode keyword|semantic|hybrid]
python run.py knowledge query --search "跨域"

# 知识库导入导出
python run.py knowledge export --output backup.json [--format json|markdown]
python run.py knowledge import --input backup.json [--merge skip|overwrite|merge]

# 知识库 dashboard
python run.py knowledge dashboard [--json]

# 环境信息
python run.py info [--json]
```

---

## 八、总结

**项目评分（v6.0 更新后）**：

| 维度 | v5.0 评分 | v6.0 评分 | 变化 | 说明 |
|------|-----------|-----------|------|------|
| 顶层设计 | 8.5 | 9.0 | +0.5 | 多项目隔离 + 多层检索 + 集中配置 完善了架构 |
| 文档质量 | 8.0 | 8.5 | +0.5 | workflow 去重 + 上下文路由修复 |
| 代码质量 | 7.0 | 8.5 | +1.5 | 148 测试覆盖 + 原子写入 + fsync + 审计日志 + 类型安全 |
| 鲁棒性 | 5.5 | 8.5 | +3.0 | **核心突破**：Python 强制状态机 + 幂等转换 + 原子写入 + fsync |
| 进化有效性 | 6.0 | 8.0 | +2.0 | 四级检索 + 生命周期管理 + 结构化归纳 + dashboard |
| 安全性 | 6.5 | 7.5 | +1.0 | subprocess 审计 pass + 原子写入防腐败 |

**一句话结论**：v5.0 评审中识别的全部 8 个问题已解决，项目从"设计正确但缺少强制机制"升级为"设计正确且由 Python 代码强制执行"。知识系统从"只能精确匹配"升级为"四级检索 + 生命周期管理 + 多项目隔离"。

---

## 九、待修复：Claude Code 平台多 Agent 调度策略过时

> 发现日期：2026-03-02
> 状态：✅ 已完成

### 问题

项目文档（SKILL.md、_base.md、full-mode.md、simple-mode.md、README.md、evolution-check.md）中 6 个文件 11 处将 Claude Code 描述为"无原生多 agent 系统，由当前 agent 串行模拟"。

这个描述已经过时。Claude Code 自 2026-02 起提供稳定的 **Task tool (Subagents)** —— 与 OpenCode 的 Task tool 机制对等：parent spawn 子 agent，子 agent 有独立上下文窗口，完成后返回结果。

### 现状对比

| 能力 | OpenCode | Claude Code（实际） | 文档中描述 |
|------|----------|---------------------|------------|
| 多 agent 调度 | `@orchestrator` + Task tool | **Task tool (Subagents)** | ~~"无原生多 agent"~~ |
| reviewer 隔离 | 独立 subagent，独立上下文 | **独立 subagent，独立上下文** | ~~"加载 md 切换角色"~~ |
| 并行 coder | 支持 | **支持** | ~~"串行执行"~~ |
| evolver 隔离 | 独立 subagent | **独立 subagent** | ~~"加载 md 切换角色"~~ |

### "角色切换模拟"的实际缺陷

当前串行模拟的做法是"加载 reviewer.md / evolver.md 到当前上下文窗口"。问题：

1. **reviewer 与 coder 共享上下文** —— reviewer 不可避免地受 coder 前序推理影响，审查独立性无法保证
2. **evolver 与编码过程共享上下文** —— 经验提取可能受编码细节干扰
3. **无法并行多个 coder** —— 串行逐个执行独立子任务

使用 Task tool spawn subagent 可以解决全部三个问题：子 agent 有独立上下文窗口，不受 parent 推理影响。

### 修复方案：统一为 Task tool 调度

将 Claude Code 的调度策略从"串行模拟"更新为"与 OpenCode 一致的 Task tool 调度"：

```
Claude Code（更新后）：

当前 agent 扮演 orchestrator 角色
    ├─ Task(prompt="知识检索: ...") → retrieval subagent
    ├─ Task(prompt="编码任务: ...") → coder subagent（可并行多个）
    ├─ Task(prompt="代码审查: ...") → reviewer subagent（独立上下文）
    └─ Task(prompt="经验提取: ...") → evolver subagent（独立上下文）
```

**与 OpenCode 的剩余差异**：
- OpenCode 用 `@agent` 语法 spawn 命名 agent，Claude Code 用 `Task(subagent_type, prompt)` spawn 匿名 subagent
- OpenCode 的 subagent 可配置不同模型（reviewer 用 claude-sonnet-4.6），Claude Code 的 subagent 默认继承 parent 模型
- 两者的 Task tool 语义一致：独立上下文、返回结果给 parent

### 涉及文件（6 个文件 11 处）

| 文件 | 改动位置 | 改动内容 |
|------|----------|----------|
| `SKILL.md` | "多 Agent 调度" 的 Claude Code 章节 | "串行模拟" → "Task tool 调度" |
| `_base.md` | 平台差异表 | "串行模拟 orchestrator" → "Task tool spawn subagent" |
| `full-mode.md` | 平台差异表 | 同上 |
| `simple-mode.md` | 平台差异表 | 同上 |
| `README.md` | 闭环图中的 `[Claude Code]` 注释 | "加载 md 切换角色" → "Task tool spawn reviewer/evolver" |
| `evolution-check.md` | 平台差异表 | 同上 |

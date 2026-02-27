# Evolving Programming Agent - 持续学习进化编程智能体

持续学习进化的编程智能体 - 由 AI Skills 驱动的自适应编程助手。

> **当前版本**: v5.0 增强架构 — 调度-执行-审查-进化闭环

---

## 项目愿景

打造一个能够**持续学习、自我进化**的编程智能体，通过组合现有的核心组件，构建一个具备以下能力的 AI 编程助手：

1. **自主学习**：从 GitHub 仓库中学习新的编程技能和最佳实践
2. **持续进化**：从每次编程任务中提取经验，不断优化自身能力
3. **完整闭环**：调度-执行-审查-进化四段式闭环，审查与进化为硬约束
4. **统一知识库**：7大分类的知识存储系统，支持智能触发加载
5. **异步并行**：知识检索异步执行，多任务 DAG 并行调度
6. **多模型配置**：不同角色使用不同模型，成本与质量兼顾
7. **跨平台支持**：支持 OpenCode、Claude Code、Cursor 三大 AI 编程平台

---

## 核心架构 (v5.0)

### 整体架构图

```
用户输入
    ↓
evolving-agent (SKILL.md — 主协调器，意图识别)
    ↓
@orchestrator  [GLM-5]
    ├─ 读取 feature_list.json
    ├─ DAG 拓扑排序，识别可并行任务组
    │
    ├── [批次 N：并行 Task 调用] ─────────────────────┐
    │   ├─ @coder → Task-A  [GLM-5]                  │
    │   ├─ @coder → Task-B  [GLM-5]  ← 真正并行      │
    │   └─ @retrieval → 知识预取 [GLM-5]  ← 同步进行  │
    │                                                 │
    ↓ 等待批次全部完成  ←────────────────────────────┘
    │
    ├─ @reviewer  [claude-sonnet-4.6, temperature=0.1]
    │   ├─ git diff 审查
    │   ├─ 写入 review_status + reviewer_notes
    │   └─ pass → completed  /  reject → 重调度 @coder
    │
    ↓ 所有任务 completed（硬约束，不可跳过）
    │
    @evolver  [GLM-5]
        ├─ 提取 progress.txt 经验
        ├─ 提取 reviewer_notes 教训
        └─ python run.py knowledge summarize --auto-store
```

### 设计原则

1. **统一入口**: 所有交互通过 `/evolve` 或自然语言由协调器接管
2. **硬约束闭环**: 审查与进化由 orchestrator 强制触发，执行者无法跳过
3. **角色分离**: coder 不做自审，reviewer 不写代码，evolver 不执行任务
4. **并行最大化**: 无依赖的任务组在单条消息中同时发出 Task
5. **模型匹配任务**: 高精度任务（审查）用 claude-sonnet；高吞吐任务用 GLM-5
6. **跨平台**: 自动检测运行平台（OpenCode/Claude Code/Cursor）

---

## 问题诊断与解决方案

| # | 问题 | 根本原因 | v5.0 解决方案 |
|---|------|----------|---------------|
| 1 | **无完整调度-执行-审查闭环** | 审查逻辑是"软约束"，无独立审查角色 | 独立 reviewer agent + 状态机硬约束 |
| 2 | **各角色不支持多 agent 并行** | 单一 agent 串行执行 | DAG 拓扑排序 + 批次并行 Task 调用 |
| 3 | **不支持不同角色使用不同模型** | SKILL.md 无 model 字段 | Agent markdown frontmatter 配置模型 |

---

## 核心组件详解

### 1. evolving-agent (顶层协调器)

**角色**: 大脑、指挥官

**功能**:
- 统一入口，负责意图识别、任务调度、进化模式管理
- 使用 `sequential-thinking` 进行深度分析，决定调用哪个子能力
- 跨平台路径自动解析（OpenCode/Claude Code/Cursor）
- 统一的命令行接口（CLI）通过 `run.py`

**触发词**:
- 编程: "开发"、"实现"、"创建"、"添加"、"修复"、"重构"、"优化"
- 学习: "学习仓库"、"从GitHub学习"、"分析开源项目"
- 归纳: "记住这个"、"保存经验"、"提取最佳实践"

**统一 CLI**:
```bash
# 进化模式控制
python run.py mode --status|--init|--on|--off

# 知识库操作
python run.py knowledge query --stats
python run.py knowledge trigger --input "..."
python run.py knowledge summarize --auto-store

# GitHub 学习
python run.py github fetch <url>

# 项目检测
python run.py project detect .

# 环境信息
python run.py info
```

---

### 2. programming-assistant (执行引擎)

**角色**: 手、执行者

**功能**:
- 负责具体的编程任务（开发、修复、重构）
- 两种工作模式：Full Mode（完整开发）和 Simple Mode（快速修复）
- 异步集成知识检索和归纳，不阻塞主流程
- 实时更新进度日志（.opencode/progress.txt）

**工作模式**:

| 模式 | 触发关键词 | 适用场景 | 工作流 |
|------|-----------|---------|--------|
| **Full Mode** | 创建、实现、添加、开发 | 新功能、完整模块开发 | 任务拆解 → 生成 TODO → 执行开发循环 → 审查门控 → 进化检查 |
| **Simple Mode** | 修复、fix、bug、重构、优化、review | Bug修复、代码优化 | 问题分析 → 执行修复循环 → 审查门控 → 进化检查 |
| **Direct Answer** | 怎么、为什么、解释 | 咨询、解释 | 直接回答，不触发工作流 |

---

### 3. github-to-knowledge (学习引擎)

**角色**: 眼睛、学习者

**功能**:
- 从 GitHub 仓库提取结构化知识
- 将非结构化代码转化为可复用的知识条目
- 自动识别架构范式、技术栈和最佳实践

**工作流**:
```
Fetch Repo Info → Extract Patterns/Stacks → Store to knowledge-base
```

---

### 4. knowledge-base (海马体)

**角色**: 记忆、知识库

**功能**:
- 统一存储和索引所有知识
- 7 大分类的知识存储系统
- 支持异步检索（`retrieval-agent`）和异步归纳（`summarize-agent`）

**知识分类**:

| 分类 | 目录 | 触发场景 |
|------|------|----------|
| **experience** | `experiences/` | 优化、重构、最佳实践 |
| **tech-stack** | `tech-stacks/` | 框架相关、技术栈 |
| **scenario** | `scenarios/` | 创建、实现功能 |
| **problem** | `problems/` | 修复、调试、报错 |
| **testing** | `testing/` | 测试相关 |
| **pattern** | `patterns/` | 架构、设计模式 |
| **skill** | `skills/` | 通用技巧 |

---

## 多 Agent 架构

### 角色模型分配

| 角色 | Agent 文件 | 模型 | Temperature | 职责 |
|------|-----------|------|-------------|------|
| **orchestrator** | `agents/orchestrator.md` | `zai-coding-plan/glm-5` | 默认 | 任务调度、DAG 排序、并行分发 |
| **coder** | `agents/coder.md` | `zai-coding-plan/glm-5` | 默认 | 代码编写、测试执行 |
| **reviewer** | `agents/reviewer.md` | `openrouter/anthropic/claude-sonnet-4.6` | `0.1` | 代码审查、质量把关 |
| **evolver** | `agents/evolver.md` | `zai-coding-plan/glm-5` | 默认 | 知识提取、经验归纳 |
| **retrieval** | `agents/retrieval.md` | `zai-coding-plan/glm-5` | 默认 | 知识检索、上下文预取 |

> **选型理由**：GLM-5 是当前开源权重模型中在代码和 agentic 任务上的 SOTA 模型，用于执行性角色兼顾质量与成本；claude-sonnet-4.6 用于 reviewer 以保证审查的严格性和准确性。

### 状态机定义（硬约束）

```
pending
  →[orchestrator dispatch]→ in_progress
      →[coder done]→ review_pending
          →[reviewer pass]→ completed
          →[reviewer reject]→ rejected
              →[orchestrator re-dispatch]→ in_progress
所有任务 completed
  →[orchestrator 强制触发]→ @evolver（不可跳过）
```

### Agent 配置示例

#### orchestrator.md

```markdown
---
description: 任务编排器。读取 feature_list.json，DAG 拓扑排序后并行调度 coder/reviewer/evolver。
mode: subagent
model: zai-coding-plan/glm-5
tools:
  write: false
  edit: false
permission:
  task:
    "coder": allow
    "reviewer": allow
    "evolver": allow
    "retrieval": allow
---

## 核心调度流程

1. 读取 feature_list.json，DAG 拓扑排序
2. 并行调用 @coder 执行无依赖任务
3. 等待 coder 完成 → 调用 @reviewer 审查
4. pass → completed / reject → 重调度 @coder
5. 所有任务 completed → 强制调用 @evolver

## 禁止行为
- 跳过 reviewer 直接标记 completed
- 跳过 evolver 直接结束会话
```

#### reviewer.md

```markdown
---
description: 代码审查器。对 review_pending 状态的任务执行 git diff 审查。
mode: subagent
model: openrouter/anthropic/claude-sonnet-4.6
temperature: 0.1
tools:
  write: false
  edit: false
  bash:
    "git diff *": allow
    "cat *": allow
---

## 审查维度
- 正确性、测试、安全、性能、规范

## 输出格式
review_status: "pass" | "reject"
reviewer_notes: ["问题列表"]
```

---

## 并行调度

### DAG 并行调度逻辑

基于 `feature_list.json` 的 `depends_on` 字段做拓扑排序：

```
任务依赖图示例：
  task-001 ──┐
             ├──→ task-003 ──→ task-004
  task-002 ──┘

并行批次：
  批次1: [task-001, task-002]  ← 无依赖，并行执行
  批次2: [task-003]            ← 依赖批次1，串行等待
  批次3: [task-004]            ← 依赖批次2，串行等待
```

### feature_list.json Schema

```json
{
  "tasks": [
    {
      "id": "task-001",
      "name": "实现 UserService",
      "status": "pending",
      "review_status": null,
      "reviewer_notes": [],
      "depends_on": []
    }
  ]
}
```

**关键字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `review_status` | `null \| "pass" \| "reject"` | reviewer 的审查结论 |
| `reviewer_notes` | `string[]` | 审查问题列表（reject 时必填） |
| `depends_on` | `string[]` | 前置任务 ID 列表，支持 DAG 排序 |

---

## 多模型配置

### 配置层级

```
优先级（低 → 高）：
  全局默认模型
    ↓
  ~/.config/opencode/opencode.json（全局配置）
    ↓
  .opencode/opencode.json（项目级覆盖）
    ↓
  agent markdown frontmatter（最高优先级）
```

### 快速配置

```bash
# 使用模板
cp opencode.json.template ~/.config/opencode/opencode.json

# 设置环境变量
export OPENROUTER_API_KEY="sk-or-v1-xxxxx"
export ZHIPUAI_API_KEY="xxxxx.xxxxx"
```

详细配置指南见：[docs/MODEL-CONFIG.md](MODEL-CONFIG.md)

---

## 关键工作流

### 编程 + 进化闭环

```
用户请求 ("帮我修复这个Bug")
    ↓
evolving-agent (协调器)
    ↓
@orchestrator
    ├─► DAG 排序，并行调度 @coder
    ├─► @retrieval 并行知识预取
    │
    ▼
@coder (执行器)
    ├─► 实现功能 / 修复问题
    ├─► status → review_pending
    │
    ▼
@reviewer (审查门控)
    ├─ pass  → completed
    └─ reject → 重调度 @coder
    │
    ▼
所有任务 completed
    ↓
@evolver (强制调用)
    ├─► 提取 progress.txt 经验
    ├─► 提取 reviewer_notes 教训
    └─► 存入 knowledge-base
```

### GitHub 学习闭环

```
用户请求 ("学习这个仓库 https://github.com/xx/repo")
    ↓
github-to-knowledge (学习器)
    ├─► Fetch Repo Info
    ├─► Extract Patterns/Stacks
    └─► Store to knowledge-base
           │
           ▼
(后续编程任务中自动复用该知识)
```

---

## 目录结构

```
evolving-programming-agent/
├── evolving-agent/                 # [Core] 核心 skill
│   ├── SKILL.md                    # 协调器配置
│   ├── agents/                     # 多 Agent 角色定义
│   │   ├── orchestrator.md
│   │   ├── coder.md
│   │   ├── reviewer.md
│   │   ├── evolver.md
│   │   └── retrieval.md
│   ├── command/
│   │   └── evolve.md              # /evolve 命令
│   ├── scripts/
│   │   ├── run.py                 # 统一 CLI 入口
│   │   ├── core/                  # 核心脚本
│   │   ├── knowledge/             # 知识库脚本
│   │   ├── github/                # GitHub 学习脚本
│   │   └── programming/           # 编程助手脚本
│   └── modules/
│       ├── programming-assistant/ # 执行引擎
│       ├── github-to-knowledge/   # 学习引擎
│       └── knowledge-base/        # 统一知识库
│
├── docs/                          # 文档
│   ├── SOLUTION.md                # 本文件
│   └── MODEL-CONFIG.md            # 多模型配置指南
│
├── tests/                         # 测试
├── scripts/                       # 安装/卸载脚本
├── opencode.json.template         # OpenCode 配置模板
├── requirements.txt               # Python 依赖
└── README.md                      # 项目说明
```

---

## 跨平台架构

| 平台 | Skills 目录 | 共享知识库 |
|------|-------------|------------|
| **OpenCode** | `~/.config/opencode/skills/` | `~/.config/opencode/knowledge/` |
| **Claude Code** | `~/.claude/skills/` | `~/.config/opencode/knowledge/` |
| **Cursor** | `~/.claude/skills/` | `~/.config/opencode/knowledge/` |

> **共享知识库**：知识数据存储在 `~/.config/opencode/knowledge/`，所有平台共享同一知识数据，避免重复学习。

系统通过 `path_resolver.py` 自动检测当前平台并使用正确的 skills 路径，知识库路径跨平台统一。

---

## 实施路线图

```
阶段1（高优先级）：完整闭环
  ✅ 创建 agents/reviewer.md
  ✅ 创建 agents/evolver.md
  ✅ 更新 feature_list.json template
  ✅ 更新 evolving-agent/SKILL.md

阶段2（中优先级）：多模型配置
  ✅ 创建 agents/orchestrator.md
  ✅ 创建 agents/coder.md
  ✅ 创建 agents/retrieval.md
  ✅ 创建 opencode.json.template

阶段3（持续优化）：并行调度
  ✅ DAG 并行逻辑
  ✅ feature_list.json schema
```

---

## 核心设计原则

1. **硬约束优于软约束**：状态机转换由 orchestrator 控制，执行者无法跳过 review 和 evolver
2. **角色分离**：coder 不做自审，reviewer 不写代码，evolver 不执行任务，职责边界清晰
3. **并行最大化**：无依赖的任务组在单条消息中同时发出 Task，不串行等待
4. **知识进化是一等公民**：evolver 与 reviewer 同级，由 orchestrator 强制触发，非可选步骤
5. **模型匹配任务**：高精度任务（审查）用 claude-sonnet；高吞吐任务（编码、调度、检索）用 GLM-5

---

## 总结

v5.0 架构通过引入 **多 Agent 编排 + 审查门控 + 强制进化**，实现了：

1. **入口统一**: 所有交互通过 `/evolve` 或自然语言由协调器接管
2. **闭环完整**: 调度-执行-审查-进化四段式硬约束闭环
3. **并行高效**: DAG 拓扑排序 + 批次并行执行
4. **模型优化**: 不同角色使用不同模型，成本与质量兼顾
5. **持续进化**: 从每次任务中学习，知识沉淀到知识库
6. **跨平台支持**: 自动检测运行环境，支持 OpenCode、Claude Code、Cursor

**核心优势**:
- 🧠 **智能**: 基于 Sequential Thinking 的深度理解和调度
- ⚡️ **高效**: 异步知识流 + DAG 并行，不阻塞主任务
- 🔄 **进化**: 从每次任务中学习，持续优化
- 🔒 **可靠**: 审查门控 + 强制进化，杜绝跳过
- 🌐 **通用**: 跨平台支持，适应不同 AI 编程环境

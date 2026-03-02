# Evolving Programming Agent - 持续学习进化编程智能体

持续学习进化的编程智能体 - 由 AI Skills 驱动的自适应编程助手。

> **当前版本**: v6.0 增强架构 — Python 强制状态机 + 四级检索 + 多项目隔离 + Task tool 统一调度

---

## 项目愿景

打造一个能够**持续学习、自我进化**的编程智能体，通过组合现有的核心组件，构建一个具备以下能力的 AI 编程助手：

1. **自主学习**：从 GitHub 仓库中学习新的编程技能和最佳实践
2. **持续进化**：从每次编程任务中提取经验，不断优化自身能力
3. **完整闭环**：调度-执行-审查-进化四段式闭环，审查与进化为硬约束，由 Python 状态机强制校验
4. **统一知识库**：7 大分类的知识存储系统，四级检索（精确→部分→模糊→语义），生命周期管理（衰减+淘汰）
5. **多项目隔离**：全局知识跨平台共享，项目级知识天然隔离，检索时合并去重
6. **异步并行**：知识检索异步执行，多任务 DAG 并行调度
7. **多模型配置**：不同角色使用不同模型，成本与质量兼顾
8. **跨平台支持**：OpenCode（原生多 agent）、Claude Code（Task tool 调度）、Cursor

---

## 核心架构 (v6.0)

### 整体架构图

```
用户输入
    ↓
evolving-agent (SKILL.md — 主协调器)
    ├─ 步骤1: 环境初始化（路径 + mode --init）
    ├─ 步骤2: 上下文感知意图识别
    │   ├─ 2.1 先检查 task status --json（有活跃任务 → 继续编程）
    │   └─ 2.2 关键词匹配（编程 / 归纳 / 学习）
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

1. **Python 强制状态机**: 所有状态转换由 `task_manager.py` 校验，LLM 无法绕过
2. **统一入口**: `/evolve` 和触发词自动激活走同一条执行路径（SKILL.md 步骤 1~6）
3. **硬约束闭环**: 审查与进化由 orchestrator 强制触发，执行者无法跳过
4. **角色分离**: coder 不做自审，reviewer 不写代码，evolver 不执行任务
5. **并行最大化**: 无依赖的任务组在单条消息中同时发出 Task
6. **模型匹配任务**: 高精度任务（审查）用 claude-sonnet；高吞吐任务用 GLM-5
7. **跨平台统一调度**: OpenCode 用 `@agent` 语法，Claude Code 用 Task tool spawn subagent，语义一致

---

## 问题诊断与解决方案

| # | 问题 | 优先级 | 根本原因 | 解决方案 | 状态 |
|---|------|--------|----------|----------|------|
| 1 | 文档即代码的根本脆弱性 | P0 | 状态机规则仅存在于 Markdown 文字描述中 | `task_manager.py` Python 强制校验 + CLI 命令 + 幂等转换 + 审计日志 | ✅ |
| 2 | 知识检索精度低 | P1 | 纯字符串匹配，无模糊/语义理解 | 四级检索 + jieba 中文分词 + embedding 语义搜索 + 相关性排序 | ✅ |
| 3 | 知识归纳缺乏结构化 | P1 | evolver 输出不规范，store.py 退化为平铺文本 | `validate_input()` 格式校验 + 7 个 store 函数与 schema.json 对齐 | ✅ |
| 4 | 知识库只增不减 | P1 | effectiveness/usage_count 从未被使用 | usage_count 自动追踪 + effectiveness 定期衰减 + gc 淘汰 | ✅ |
| 5 | 并发写入不安全 | P2 | 多 agent 同时写 feature_list.json | `atomic_write_json()` + `f.flush()` + `os.fsync()` | ✅ |
| 6 | full-mode/simple-mode 大量重复 | P2 | 两份几乎一样的文档 | 提取 `_base.md` 公共步骤，各模式只写差异 | ✅ |
| 7 | 意图识别是纯关键词匹配 | P2 | 无法利用上下文 | 步骤 2.1 上下文优先检查（task status --json），2.2 关键词兜底 | ✅ |
| 8 | Shell 命令注入风险 | P3 | echo "用户内容" 未转义 | subprocess 列表调用审计，无 shell=True | ✅ |

---

## 核心组件详解

### 1. evolving-agent (顶层协调器)

**角色**: 大脑、指挥官

**功能**:
- 上下文感知的意图识别：先检查活跃任务，再做关键词匹配
- 环境初始化：`mode --init` 保证进化模式激活
- 跨平台路径自动解析（OpenCode/Claude Code/Cursor）
- 统一 CLI 通过 `run.py`

**触发词**:
- 编程: "开发"、"实现"、"创建"、"添加"、"修复"、"重构"、"优化"、"怎么"、"为什么"、"报错"
- 学习: "学习"、"分析"、"参考"、"模仿"
- 归纳: "记住"、"保存"、"复盘"、"提取"

**统一 CLI**:
```bash
# 进化模式控制
python run.py mode --status|--init|--on|--off

# 任务状态管理
python run.py task create --name "..." [--priority high] [--depends task-001]
python run.py task list [--status pending] [--json]
python run.py task transition --task-id task-001 --status in_progress [--actor reviewer]
python run.py task status [--json]

# 知识库操作
python run.py knowledge query --trigger "react,hooks" [--mode keyword|semantic|hybrid]
python run.py knowledge query --search "跨域"
python run.py knowledge query --stats
python run.py knowledge trigger --input "修复CORS问题"
python run.py knowledge summarize --auto-store
python run.py knowledge decay
python run.py knowledge gc [--dry-run]
python run.py knowledge export --output backup.json [--format json|markdown]
python run.py knowledge import --input backup.json [--merge skip|overwrite|merge]
python run.py knowledge dashboard [--json]

# GitHub 学习
python run.py github fetch <url>

# 项目检测
python run.py project detect .

# 环境信息
python run.py info [--json]
```

---

### 2. programming-assistant (执行引擎)

**角色**: 手、执行者

**功能**:
- 负责具体的编程任务（开发、修复、重构）
- 两种工作模式：Full Mode（完整开发）和 Simple Mode（快速修复）
- 状态文件驱动（`.opencode/feature_list.json` + `.opencode/progress.txt`），不依赖会话历史
- 公共步骤提取到 `_base.md`（审查门控、知识归纳、错误处理）

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
- 统一存储和索引所有知识（7 大分类）
- 四级检索：精确匹配 → 部分匹配 → 模糊匹配（可选 jieba）→ 语义搜索（可选 embedding）
- 相关性排序：触发词匹配×0.4 + effectiveness×0.3 + recency×0.2 + usage×0.1
- 生命周期管理：usage_count 追踪 → effectiveness 衰减 → gc 淘汰
- 多项目隔离：全局 `~/.config/opencode/knowledge/` + 项目级 `$PROJECT_ROOT/.opencode/knowledge/`
- 导入导出：JSON / Markdown 格式
- 可视化 dashboard：统计分布、top 使用、低分预警

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

### 平台调度差异

| 平台 | 调度方式 | reviewer/evolver 隔离 |
|------|----------|----------------------|
| **OpenCode** | `@orchestrator` 原生调度，`@agent` 语法 spawn 命名 agent，可指定模型 | 独立 subagent，独立上下文 |
| **Claude Code** | 当前 agent 扮演 orchestrator，`Task(subagent_type, prompt)` spawn 匿名 subagent | 独立 subagent，独立上下文 |

> 两者 Task tool 语义一致：subagent 有独立上下文窗口，完成后返回结果给 parent。

### 状态机定义（Python 强制校验）

```python
VALID_TRANSITIONS = {
    "pending":        ["in_progress"],
    "in_progress":    ["review_pending", "blocked"],
    "review_pending": ["completed", "rejected"],   # completed 只允许 actor="reviewer"
    "rejected":       ["in_progress"],
    "blocked":        ["pending"],
}
```

```
pending
  →[orchestrator dispatch]→ in_progress
      →[coder done]→ review_pending
          →[reviewer pass]→ completed  ← 只有 reviewer 可标记
          →[reviewer reject]→ rejected
              →[orchestrator re-dispatch]→ in_progress
所有任务 completed
  →[orchestrator 强制触发]→ @evolver（不可跳过）
```

- **幂等转换**：`in_progress → in_progress` 是 no-op，不报错（agent 重试安全）
- **审计日志**：每次非幂等转换记录 `{from, to, actor, timestamp}` 到 `audit_log` 数组

### feature_list.json Schema

```json
{
  "tasks": [
    {
      "id": "task-001",
      "name": "实现 UserService",
      "description": "",
      "status": "pending",
      "priority": "medium",
      "depends_on": [],
      "audit_log": [],
      "review_status": null,
      "reviewer_notes": [],
      "created_at": "ISO-8601",
      "updated_at": "ISO-8601"
    }
  ]
}
```

**关键字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | `string` | 状态机状态，由 `task_manager.py` 强制校验 |
| `review_status` | `null \| "pass" \| "reject"` | reviewer 的审查结论 |
| `reviewer_notes` | `string[]` | 审查问题列表（reject 时必填） |
| `depends_on` | `string[]` | 前置任务 ID 列表，支持 DAG 排序 |
| `audit_log` | `object[]` | 状态转换审计记录（from/to/actor/timestamp） |

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

## 集中配置管理

所有可调参数集中在 `scripts/core/config.py`：

```python
# Knowledge lifecycle
DECAY_DAYS_THRESHOLD = 90        # 超过 N 天未使用开始衰减
DECAY_RATE = 0.1                 # 每次衰减幅度
GC_EFFECTIVENESS_THRESHOLD = 0.1  # 低于此阈值被 gc 清理

# Knowledge retrieval
FUZZY_MATCH_THRESHOLD = 0.6      # 模糊匹配最低相似度
RELEVANCE_WEIGHTS = {
    "trigger_match": 0.4,
    "effectiveness": 0.3,
    "recency": 0.2,
    "usage": 0.1,
}
TOP_K_RESULTS = 10               # 默认返回条数
```

各模块从 config 导入，函数参数仍可覆盖（CLI `--threshold` 等参数优先级最高）。

---

## 目录结构

```
evolving-programming-agent/
├── evolving-agent/                 # [Core] 核心 skill
│   ├── SKILL.md                    # 协调器入口（意图识别 → 路由分发）
│   ├── agents/                     # 多 Agent 角色定义
│   │   ├── orchestrator.md
│   │   ├── coder.md
│   │   ├── reviewer.md
│   │   ├── evolver.md
│   │   ├── retrieval.md
│   │   └── references/            # 审查参考清单
│   ├── command/
│   │   └── evolve.md              # /evolve 命令（透传 SKILL.md 流程）
│   ├── scripts/
│   │   ├── run.py                 # 统一 CLI 入口
│   │   ├── core/                  # 核心脚本
│   │   │   ├── config.py          # 集中配置
│   │   │   ├── file_utils.py      # 原子写入（fsync）
│   │   │   ├── task_manager.py    # 状态机（幂等 + 审计日志）
│   │   │   ├── path_resolver.py   # 跨平台路径解析
│   │   │   ├── toggle_mode.py     # 进化模式控制
│   │   │   └── trigger_detector.py # 触发检测
│   │   ├── knowledge/             # 知识库脚本
│   │   │   ├── query.py           # 四级检索 + 语义搜索
│   │   │   ├── store.py           # 结构化存储（7 categories）
│   │   │   ├── lifecycle.py       # decay + gc
│   │   │   ├── dashboard.py       # 可视化统计
│   │   │   ├── embedding.py       # 可选 embedding
│   │   │   ├── knowledge_io.py    # 导入导出
│   │   │   ├── summarizer.py      # 归纳格式校验
│   │   │   └── trigger.py         # 触发词匹配
│   │   ├── github/                # GitHub 学习脚本
│   │   └── programming/           # 编程助手脚本
│   └── modules/
│       ├── programming-assistant/  # 执行引擎
│       │   ├── README.md
│       │   └── workflows/
│       │       ├── _base.md        # 公共步骤
│       │       ├── full-mode.md
│       │       ├── simple-mode.md
│       │       └── evolution-check.md
│       ├── github-to-knowledge/    # 学习引擎
│       └── knowledge-base/         # 统一知识库（schema + agents）
│
├── docs/                           # 文档
│   ├── SOLUTION.md                 # 本文件
│   ├── architecture-review.md      # 综合评估报告（v6.0）
│   ├── mvp-build-plan.md           # 构建计划（Phase 1~5）
│   └── MODEL-CONFIG.md             # 多模型配置指南
│
├── tests/                          # 测试（148 passed）
├── scripts/                        # 安装/卸载脚本
├── requirements.txt                # Python 依赖（含可选依赖注释）
└── README.md                       # 项目说明
```

---

## 跨平台架构

| 平台 | Skills 目录 | 多 Agent 方式 | 全局知识库 |
|------|-------------|---------------|------------|
| **OpenCode** | `~/.config/opencode/skills/` | 原生 `@agent` 调度 | `~/.config/opencode/knowledge/` |
| **Claude Code** | `~/.claude/skills/` | Task tool spawn subagent | `~/.config/opencode/knowledge/` |
| **Cursor** | `~/.claude/skills/` | Task tool spawn subagent | `~/.config/opencode/knowledge/` |

> 全局知识库跨平台复用。项目级知识存放在 `$PROJECT_ROOT/.opencode/knowledge/`，天然隔离。

系统通过 `path_resolver.py` 自动检测当前平台并使用正确的 skills 路径。

---

## 实施路线图

```
Phase 1：基础设施 + 状态管理器          ✅ TASK-01~09
  ├─ Shell 安全审计
  ├─ 原子写入 file_utils.py（fsync）
  ├─ 状态管理器 task_manager.py + CLI
  └─ workflow 文档适配（CLI 命令替代直接编辑 JSON）

Phase 2：知识系统加固                   ✅ TASK-10~14
  ├─ 归纳格式校验 validate_input()
  └─ workflow 去重 _base.md

Phase 3：知识升级 + 智能路由            ✅ TASK-15~22
  ├─ 知识库生命周期（usage_count + decay + gc）
  ├─ 四级检索（精确 + 部分 + 模糊 + 相关性排序）
  └─ 上下文感知路由（task status → 意图识别）

Phase 4：进阶 + 产品能力               ✅ TASK-23~34
  ├─ fsync 加固、幂等转换、审计日志
  ├─ 集中配置 config.py
  ├─ SKILL.md 路由修复
  ├─ jieba 中文分词（可选依赖）
  ├─ embedding 语义搜索（可选依赖）
  ├─ 知识库导入导出 CLI
  ├─ store/schema 7 categories 对齐验证
  ├─ 多项目知识隔离
  ├─ 知识库 dashboard
  └─ 全量回归验收（148 passed, 3 skipped）

Phase 5：Claude Code 多 Agent 升级      ✅ TASK-35
  └─ "串行模拟" → Task tool spawn subagent（6 文件 12 处）
```

---

## 核心设计原则

1. **Python 强制优于文档约束**：状态转换由 `task_manager.py` 校验，非法操作在脚本层被拒绝
2. **角色分离**：coder 不做自审，reviewer 不写代码，evolver 不执行任务，职责边界清晰
3. **并行最大化**：无依赖的任务组在单条消息中同时发出 Task，不串行等待
4. **知识进化是一等公民**：evolver 与 reviewer 同级，由 orchestrator 强制触发，非可选步骤
5. **模型匹配任务**：高精度任务（审查）用 claude-sonnet；高吞吐任务（编码、调度、检索）用 GLM-5
6. **可选依赖优雅降级**：jieba、sentence-transformers 不安装也能正常运行，功能退化但不报错
7. **幂等安全**：状态转换、mode --init 均为幂等操作，agent 重试不会产生副作用

---

## 总结

v6.0 架构在 v5.0 基础上完成了 35 个任务的系统性加固：

1. **入口统一**: `/evolve` 和触发词走同一条执行路径（SKILL.md 步骤 1~6）
2. **闭环可靠**: Python 状态机强制校验 + 幂等转换 + 审计日志
3. **检索精准**: 四级检索（精确→部分→模糊→语义）+ 相关性排序
4. **知识健康**: usage_count 追踪 + effectiveness 衰减 + gc 淘汰 + dashboard 可视化
5. **项目隔离**: 全局知识共享 + 项目级知识天然隔离
6. **并行高效**: DAG 拓扑排序 + 批次并行执行
7. **跨平台**: OpenCode 原生 agent + Claude Code Task tool + Cursor，统一调度语义
8. **持续进化**: 从每次任务中学习，知识沉淀到知识库

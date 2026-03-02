# Evolving Programming Agent

**持续学习、自我进化的 AI 编程智能体**

> **EN**: A continuously learning, self-evolving AI programming agent with orchestrated coding, review gating, and knowledge accumulation.

Evolving Programming Agent 是一个模块化的 AI 编程系统。它不仅仅是一个代码生成工具，更是一个能够从 GitHub 学习最佳实践、从日常任务中积累经验、并不断优化自身能力的"成长型"智能体。

> **EN**: This project is a modular AI engineering system. Beyond code generation, it learns from GitHub repositories, accumulates practical experience from daily tasks, and continuously improves through an evolution loop.

---

## 🚀 核心特性

> **EN**: Key capabilities include orchestrator-driven workflow, strict review gating, DAG-based parallel execution, mandatory post-task evolution, and role-specific model routing.

- **🧠 统一协调大脑**: 上下文感知的意图识别 + 任务调度，先检查活跃会话再做关键词匹配
- **🔒 Python 强制状态机**: `pending → in_progress → review_pending → completed/rejected`，coder 不能自审、不能跳过 reviewer，支持幂等转换和审计日志
- **🔄 自动进化闭环**: 编程任务结束后自动提取经验（Bug 修复、架构模式）并存入知识库
- **🔍 四级知识检索**: 精确匹配 → 部分匹配 → 模糊匹配（可选 jieba 中文分词）→ 语义搜索（可选 embedding），按综合相关性排序
- **📉 知识库生命周期**: usage_count 自动追踪 → effectiveness 定期衰减 → gc 清理低分条目 → dashboard 可视化
- **📚 GitHub 学习引擎**: 主动分析 GitHub 开源项目，提取架构范式和代码规范，转化为可复用的技能
- **🧩 多项目知识隔离**: 全局知识 `~/.config/opencode/knowledge/` + 项目级知识 `$PROJECT_ROOT/.opencode/knowledge/`，检索时合并去重
- **🌐 跨平台支持**: OpenCode（原生多 agent）、Claude Code（Task tool 调度）、Cursor 三大平台

---

## 📋 系统要求

### 必需依赖

| 依赖 | 版本要求 | 说明 |
|------|----------|------|
| Python | >= 3.8 | 项目运行环境 |
| PyYAML | >= 6.0,< 7.0 | 解析 SKILL.md frontmatter |

### 可选依赖

| 依赖 | 版本要求 | 说明 |
|------|----------|------|
| Git | >= 2.0 | GitHub 仓库学习功能 |
| jieba | >= 0.42, < 1.0 | 中文分词（不安装则 fallback 到正则分割） |
| sentence-transformers | >= 2.2 | 语义搜索 embedding（不安装则 fallback 到关键词模式） |

---

## 🏗️ 架构概览

Evolving Programming Agent 采用 **v6.0 多 Agent 编排架构**，以 `evolving-agent` 为入口，由 `@orchestrator` 负责任务闭环。Python 状态机强制校验所有状态转换，支持幂等转换和审计日志：

> **EN**: The v6.0 architecture uses `evolving-agent` as the entrypoint and delegates programming tasks to `@orchestrator`, which coordinates `@retrieval`, `@coder`, `@reviewer`, and `@evolver` in a hard-gated loop. A Python state machine enforces all transitions with idempotency and audit logging.

```
用户输入
    ↓
evolving-agent (意图识别入口)
    ├─► 编程任务 → @orchestrator
    │               ├─► @retrieval (并行知识预取)
    │               ├─► @coder (并行执行批次)
    │               ├─► @reviewer (审查门控)
    │               └─► @evolver (全部完成后强制触发)
    ├─► GitHub学习 → github-to-knowledge
    └─► 知识归纳 → knowledge-base
```

### 核心组件

| 组件 | 目录 | 职责 |
|------|------|------|
| **evolving-agent** | `evolving-agent/` | **核心协调器**。意图识别、编程任务路由、闭环治理 |
| **agents** | `evolving-agent/agents/` | 多角色定义（orchestrator/coder/reviewer/evolver/retrieval） |
| **programming-assistant** | `evolving-agent/modules/programming-assistant/` | 编程工作流定义（状态机、审查门控、进化检查） |
| **github-to-knowledge** | `evolving-agent/modules/github-to-knowledge/` | 学习引擎。从 GitHub 提取知识存入知识库 |
| **knowledge-base** | `evolving-agent/modules/knowledge-base/` | 统一知识库。存储、查询、归纳知识 |

---

## 📦 安装

> **EN**: Clone the repository and run the installer to set up all components for OpenCode/Claude Code/Cursor.

### 快速安装

```bash
# 克隆仓库
git clone https://github.com/your-repo/evolving-programming-agent.git
cd evolving-programming-agent

# 安装所有组件 (支持 OpenCode, Claude Code, Cursor)
./scripts/install.sh --all
```

### Python 环境配置

每个 Skill 拥有独立的虚拟环境，避免依赖冲突：

```bash
# evolving-agent 的虚拟环境
~/.config/opencode/skills/evolving-agent/.venv/

# 仅 evolving-agent 使用共享虚拟环境
```

---

## 🎮 快速开始

> **EN**: Start with `/evolve`, then describe tasks in natural language. Programming requests are routed to the orchestrator pipeline automatically.

### 1. 启动协调器

推荐使用统一入口命令 `/evolve` 启动会话：

```bash
/evolve
```

系统将初始化环境并进入协调态；后续编程任务默认由 `@orchestrator` 接管。

### 2. 执行编程任务

直接用自然语言描述需求，协调器会自动路由到 `@orchestrator`：

> "帮我用 React 写一个登录页面"
> "修复这个 CORS 跨域问题"
> "重构这个组件，提高可维护性"

> **EN examples**:
> "Build a login page with React"
> "Fix this CORS issue"
> "Refactor this component for maintainability"

### 3. 从 GitHub 学习

让智能体学习优秀的开源项目：

> "学习这个仓库 https://github.com/shadcn/ui"

系统将自动提取组件设计模式，并在后续编程中复用。

### 4. 显式保存经验

虽然系统会自动进化，您也可以显式要求保存：

> "记住这个解决方案，以后遇到类似问题直接用"
> "保存这个修复经验，标记为跨域问题"

---

## 📖 统一命令行接口

> **EN**: `run.py` is the unified cross-platform CLI for mode control, knowledge operations, GitHub learning, project detection, and environment diagnostics.

所有功能通过 `run.py` 统一调用，支持跨平台（OpenCode/Claude Code/Cursor）：

### 设置路径变量（每个 shell 会话执行一次）

```bash
# 自动检测平台并设置路径
SKILLS_DIR=$([ -d ~/.config/opencode/skills/evolving-agent ] && echo ~/.config/opencode/skills || echo ~/.claude/skills)
```

### 进化模式控制

```bash
# 查看状态
python $SKILLS_DIR/evolving-agent/scripts/run.py mode --status

# 完整初始化
python $SKILLS_DIR/evolving-agent/scripts/run.py mode --init

# 开启进化模式
python $SKILLS_DIR/evolving-agent/scripts/run.py mode --on

# 关闭进化模式
python $SKILLS_DIR/evolving-agent/scripts/run.py mode --off
```

### 知识库操作

```bash
# 查看统计
python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge query --stats

# 按触发词查询（支持 --mode keyword|semantic|hybrid）
python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge query --trigger "react,hooks"

# 按分类查询
python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge query --category problem

# 全文搜索
python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge query --search "跨域"

# 触发检测（自动匹配相关知识）
python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge trigger --input "修复CORS问题"

# 归纳并自动存储
echo "内容" | python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge summarize --auto-store

# 存储知识
python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge store --category experience --name "xxx"

# 生命周期管理
python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge decay            # 衰减长期未用条目
python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge gc --dry-run     # 预览将清理的低分条目
python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge gc               # 执行清理

# 导入导出
python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge export --output backup.json
python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge import --input backup.json --merge skip

# 可视化 dashboard
python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge dashboard        # 文本输出
python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge dashboard --json # JSON 输出
```

### GitHub 学习

```bash
# 获取仓库信息
python $SKILLS_DIR/evolving-agent/scripts/run.py github fetch <url>

# 提取模式
python $SKILLS_DIR/evolving-agent/scripts/run.py github extract --input repo_info.json

# 存储到知识库
python $SKILLS_DIR/evolving-agent/scripts/run.py github store --input extracted.json
```

### 项目检测

```bash
# 检测当前项目技术栈
python $SKILLS_DIR/evolving-agent/scripts/run.py project detect .

# 存储项目经验
python $SKILLS_DIR/evolving-agent/scripts/run.py project store --tech react --pattern "xxx"

# 查询项目经验
python $SKILLS_DIR/evolving-agent/scripts/run.py project query --project .
```

### 环境信息

```bash
# 显示环境信息（表格格式）
python $SKILLS_DIR/evolving-agent/scripts/run.py info

# 显示环境信息（JSON 格式）
python $SKILLS_DIR/evolving-agent/scripts/run.py info --json
```

---

## 🔄 核心工作流

> **EN**: The core loop is: intent routing -> orchestrated task batches -> review gate -> mandatory evolution and knowledge storage.

### 编程 + 进化闭环

```
用户请求 ("帮我修复这个 Bug")
    ↓
evolving-agent (协调器入口)
    ↓
@orchestrator
    ├─► 读取/维护 feature_list.json
    ├─► DAG 拓扑排序，按批次并行调度 @coder
    ├─► 并行调用 @retrieval 生成 .knowledge-context.md
    ├─► 批次完成后进入 @reviewer 门控
    │    ├─ pass   → status: completed
    │    └─ reject → status: rejected + reviewer_notes 回流 @coder
    └─► 所有任务 completed 后强制调用 @evolver
          ↓
       knowledge-base (沉淀经验)
```

### GitHub 学习闭环

```
用户请求 ("学习这个仓库 https://github.com/xx/repo")
    ↓
evolving-agent (协调器)
    ↓
github-to-knowledge (学习器)
    │
    ├─► Fetch Repo Info
    ├─► Extract Patterns/Stacks
    └─► Store to knowledge-base
          │
          ▼
knowledge-base (更新索引)
    │
    ▼
(后续编程任务中自动复用该知识)
```

---

## 📚 知识分类系统

> **EN**: Knowledge is categorized into experience, tech-stack, scenario, problem, testing, pattern, and skill for targeted retrieval.

| 分类 | 目录 | 触发场景 |
|------|------|----------|
| **experience** | `experiences/` | 优化、重构、最佳实践 |
| **tech-stack** | `tech-stacks/` | 框架相关 |
| **scenario** | `scenarios/` | 创建、实现功能 |
| **problem** | `problems/` | 修复、调试、报错 |
| **testing** | `testing/` | 测试相关 |
| **pattern** | `patterns/` | 架构、设计模式 |
| **skill** | `skills/` | 通用技巧 |

### 知识条目 Schema

```json
{
  "id": "category-name-hash",
  "category": "experience|tech-stack|scenario|problem|testing|pattern|skill",
  "name": "名称",
  "triggers": ["触发词"],
  "content": {},
  "sources": ["来源"],
  "tags": [],
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601",
  "usage_count": 0,
  "last_used_at": null,
  "effectiveness": 0.5
}
```

---

## 🎯 编程模式

> **EN**: Full Mode targets feature development with structured task lifecycle; Simple Mode focuses on fast bug-fix loops with the same review/evolution gate.

### Full Mode（完整开发）

**触发关键词**: 创建、实现、添加、开发

**工作流**:
1. 任务拆解（sequential-thinking）
2. 生成 TODO 列表
3. 执行开发循环（`pending → in_progress → review_pending`）
4. 审查门控（`pass/reject`）
5. 进化检查（全部 completed 后强制执行）

### Simple Mode（快速修复）

**触发关键词**: 修复、fix、bug、重构、优化、review

**工作流**:
1. 问题分析（sequential-thinking）
2. 执行修复循环（最小任务集）
3. 审查门控
4. 进化检查

---

## 📂 项目结构

> **EN**: The repository is organized around the coordinator (`evolving-agent`), role agents, modular workflows, utilities, docs, and tests.

```
evolving-programming-agent/
├── evolving-agent/                 # [Core] 顶层协调器
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
│   │   │   ├── config.py          # 集中配置（阈值、权重等）
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
│   │   │   ├── embedding.py       # 可选 embedding 语义搜索
│   │   │   ├── knowledge_io.py    # 导入导出
│   │   │   ├── summarizer.py      # 归纳格式校验
│   │   │   └── trigger.py         # 触发词匹配
│   │   ├── github/                # GitHub 学习脚本
│   │   └── programming/           # 编程助手脚本
│   └── modules/
│       ├── programming-assistant/  # 执行引擎
│       │   ├── README.md
│       │   └── workflows/
│       │       ├── _base.md        # 公共步骤（审查门控、知识归纳等）
│       │       ├── full-mode.md
│       │       ├── simple-mode.md
│       │       └── evolution-check.md
│       ├── github-to-knowledge/    # 学习引擎
│       └── knowledge-base/         # 统一知识库（schema + agents）
│
├── docs/                           # 文档
│   ├── architecture-review.md      # 综合评估报告（v6.0）
│   ├── mvp-build-plan.md           # 构建计划（Phase 1~5）
│   ├── SOLUTION.md                 # 历史架构说明
│   └── MODEL-CONFIG.md             # 多模型配置指南
├── tests/                          # 测试（148 passed）
├── scripts/                        # 安装/卸载脚本
├── requirements.txt                # Python 依赖（含可选依赖注释）
└── README.md                       # 本文件
```

---

## 🌍 跨平台支持

> **EN**: Supported platforms: OpenCode, Claude Code, and Cursor, with automatic path detection for skills and knowledge directories.

Evolving Programming Agent 支持三大 AI 编程平台：

| 平台 | Skills 目录 | 多 Agent 方式 | 全局知识库 |
|------|-------------|---------------|------------|
| **OpenCode** | `~/.config/opencode/skills/` | 原生 `@agent` 调度 | `~/.config/opencode/knowledge/` |
| **Claude Code** | `~/.claude/skills/` | Task tool spawn subagent | `~/.config/opencode/knowledge/` |
| **Cursor** | `~/.claude/skills/` | Task tool spawn subagent | `~/.config/opencode/knowledge/` |

> 全局知识库跨平台复用。项目级知识存放在 `$PROJECT_ROOT/.opencode/knowledge/`，天然隔离。

---

## 🤝 贡献

欢迎提交 Pull Request 或 Issue 来帮助改进这个项目！

---

## 📄 许可证

MIT License

---

## 📖 相关文档

> **EN**: Start with `docs/architecture-review.md` for architecture and `docs/MODEL-CONFIG.md` for multi-model setup.

- [综合评估报告 (docs/architecture-review.md)](docs/architecture-review.md): v6.0 架构审查 + 优化方案实施结果
- [构建计划 (docs/mvp-build-plan.md)](docs/mvp-build-plan.md): Phase 1~5 全部任务详情
- [模型配置 (docs/MODEL-CONFIG.md)](docs/MODEL-CONFIG.md): 多角色模型与 provider 配置
- [历史架构 (docs/SOLUTION.md)](docs/SOLUTION.md): 架构演进背景
- [协调器入口 (evolving-agent/SKILL.md)](evolving-agent/SKILL.md): 意图识别 → 路由分发流程

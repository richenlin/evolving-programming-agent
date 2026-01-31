# Evolving Programming Agent

**持续学习、自我进化的 AI 编程智能体**

Evolving Programming Agent 是一个模块化的 AI 编程系统。它不仅仅是一个代码生成工具，更是一个能够从 GitHub 学习最佳实践、从日常任务中积累经验、并不断优化自身能力的"成长型"智能体。

---

## 🚀 核心特性

- **🧠 统一协调大脑**: 通过 `evolving-agent` 进行意图识别和任务调度，智能处理编程、学习和管理任务
- **🔄 自动进化闭环**: 在编程任务结束后，自动提取有价值的经验（Bug 修复、架构模式）并存入知识库
- **📚 GitHub 学习引擎**: 主动分析 GitHub 开源项目，提取架构范式和代码规范，转化为可复用的技能
- **⚡️ 异步知识流**: 知识检索和归纳在后台异步执行，提供流畅无阻塞的编程体验
- **🧩 模块化架构**: 所有能力（编程、学习、管理）模块化，职责清晰
- **🎯 智能触发系统**: 7 大分类的知识存储，基于关键词自动触发相关知识
- **🌐 跨平台支持**: 支持 OpenCode、Claude Code、Cursor 三大 AI 编程平台

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

---

## 🏗️ 架构概览

Evolving Programming Agent 采用**统一协调器模式**（v4.0），通过 `evolving-agent` 作为中央大脑，智能调度各功能模块：

```
用户输入
    ↓
evolving-agent (协调器)
    ├─► Sequential Thinking 意图识别
    │   ├─► 编程任务 → programming-assistant
    │   ├─► GitHub学习 → github-to-skills
    │   ├─► 知识归纳 → knowledge-base
    │   └─► 管理命令 → skill-manager
    ↓
异步知识检索/归纳
    ↓
knowledge-base (统一知识库)
    ├─► experience (经验)
    ├─► tech-stack (技术栈)
    ├─► scenario (场景)
    ├─► problem (问题)
    ├─► testing (测试)
    ├─► pattern (模式)
    └─► skill (技能)
```

### 核心组件

| 组件 | 目录 | 职责 |
|------|------|------|
| **evolving-agent** | `evolving-agent/` | **核心协调器**。意图识别、任务调度、进化模式管理 |
| **programming-assistant** | `evolving-agent/modules/programming-assistant/` | 执行引擎。代码生成、修复和重构 |
| **github-to-skills** | `evolving-agent/modules/github-to-skills/` | 学习引擎。从 GitHub 提取知识 |
| **knowledge-base** | `evolving-agent/modules/knowledge-base/` | 统一知识库。存储、查询、归纳知识 |
| **skill-manager** | `skill-manager/` | 运维工具。管理 Skill 的生命周期 |

---

## 📦 安装

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

# skill-manager 复用 evolving-agent 的虚拟环境
```

---

## 🎮 快速开始

### 1. 启动协调器

推荐使用统一入口命令 `/evolve` 启动会话：

```bash
/evolve
```

系统将初始化环境，开启进化模式，并等待您的指令。

### 2. 执行编程任务

直接用自然语言描述需求，协调器会自动调度 `programming-assistant`：

> "帮我用 React 写一个登录页面"
> "修复这个 CORS 跨域问题"
> "重构这个组件，提高可维护性"

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

# 按触发词查询
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

### 编程 + 进化闭环

```
用户请求 ("帮我修复这个Bug")
    ↓
evolving-agent (协调器)
    │
    ├─► Sequential Thinking 意图识别
    ├─► 检查进化模式
    │
    ├─► [异步] 知识检索 (knowledge-retrieval)
    │      ↓
    │   .knowledge-context.md (上下文)
    │
    ▼
programming-assistant (执行器)
    │
    ├─► Full Mode / Simple Mode 选择
    ├─► 任务拆解（sequential-thinking）
    ├─► 执行修复循环
    │
    ▼
任务完成
    ↓
evolving-agent (协调器)
    │
    ├─► 检测进化触发条件 (复杂修复? 用户反馈?)
    │
    ▼
[异步] 知识归纳 (knowledge-summarize)
    ↓
knowledge-base (存入新经验)
```

### GitHub 学习闭环

```
用户请求 ("学习这个仓库 https://github.com/xx/repo")
    ↓
evolving-agent (协调器)
    ↓
github-to-skills (学习器)
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
  "created_at": "ISO-8601",
  "effectiveness": 0.5
}
```

---

## 🎯 编程模式

### Full Mode（完整开发）

**触发关键词**: 创建、实现、添加、开发

**工作流**:
1. 任务拆解（sequential-thinking）
2. 生成 TODO 列表
3. 执行开发循环
4. 进化检查

### Simple Mode（快速修复）

**触发关键词**: 修复、fix、bug、重构、优化、review

**工作流**:
1. 问题分析（sequential-thinking）
2. 执行修复循环
3. 进化检查

---

## 📂 项目结构

```
evolving-programming-agent/
├── evolving-agent/                 # [Core] 顶层协调器
│   ├── SKILL.md                    # 协调器配置
│   ├── command/
│   │   └── evolve.md              # /evolve 命令文档
│   ├── scripts/
│   │   ├── run.py                 # 统一 CLI 入口
│   │   ├── core/                  # 核心脚本
│   │   │   ├── toggle_mode.py    # 进化模式控制
│   │   │   ├── trigger_detector.py # 触发检测
│   │   │   └── ...
│   │   ├── knowledge/             # 知识库脚本
│   │   ├── github/                # GitHub 学习脚本
│   │   └── programming/           # 编程助手脚本
│   └── modules/
│       ├── programming-assistant/ # 执行引擎
│       │   ├── README.md
│       │   └── workflows/
│       │       ├── full-mode.md
│       │       ├── simple-mode.md
│       │       └── evolution-check.md
│       ├── github-to-skills/      # 学习引擎
│       │   ├── README.md
│       │   └── ...
│       └── knowledge-base/        # 统一知识库
│           ├── README.md
│           ├── agents/
│           │   ├── retrieval-agent.md
│           │   └── summarize-agent.md
│           └── scripts/
│
├── skill-manager/                  # [Util] 运维工具
│   ├── SKILL.md
│   └── scripts/
│       ├── list_skills.py
│       ├── health_check.py
│       ├── toggle_skill.py
│       └── ...
│
├── docs/                           # 文档
│   └── SOLUTION.md                 # 架构设计文档
├── tests/                          # 测试
├── scripts/                        # 安装/卸载脚本
├── requirements.txt                # Python 依赖
└── README.md                       # 本文件
```

---

## 🌍 跨平台支持

Evolving Programming Agent 支持三大 AI 编程平台：

| 平台 | Skills 目录 | 知识目录 |
|------|-------------|----------|
| **OpenCode** | `~/.config/opencode/skills/` | `~/.config/opencode/knowledge/` |
| **Claude Code** | `~/.claude/skills/` | `~/.claude/knowledge/` |
| **Cursor** | `~/.claude/skills/` | `~/.claude/knowledge/` |

系统会自动检测当前平台，并使用正确的路径。

---

## 🤝 贡献

欢迎提交 Pull Request 或 Issue 来帮助改进这个项目！

---

## 📄 许可证

MIT License

---

## 📖 相关文档

- [架构设计 (docs/SOLUTION.md)](docs/SOLUTION.md): 详细的系统架构和设计理念
- [evolving-agent SKILL](evolving-agent/SKILL.md): 协调器配置文档
- [skill-manager SKILL](skill-manager/SKILL.md): 运维工具文档

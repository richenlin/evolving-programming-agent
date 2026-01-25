# Evolving Programming Agent - 持续学习进化编程智能体

持续学习进化的编程智能体 - 由 AI Skills 驱动的自适应编程助手。

## 项目愿景

打造一个能够**持续学习、自我进化**的编程智能体，通过组合现有的核心组件，构建一个具备以下能力的 AI 编程助手：

1. **自主学习**：从 GitHub 仓库中学习新的编程技能和最佳实践
2. **持续进化**：从每次编程任务中提取经验，不断优化自身能力
3. **灵活管理**：以插件形式管理技能库，支持热启用/禁用
4. **统一知识库**：7大分类的知识存储系统，支持智能触发加载
5. **异步闭环**：知识检索和归纳异步执行，不阻塞主任务
6. **智能调度**：通过 Sequential-Thinking 进行意图识别和任务分发
7. **跨平台支持**：支持 OpenCode、Claude Code、Cursor 三大 AI 编程平台

---

## 核心架构 (v4.0 Unified Coordinator)

### 架构图

```mermaid
graph TD
    User[用户输入] --> Coord[evolving-agent (协调器)]

    subgraph Coordinator Layer
    Coord -->|Sequential Thinking| Intent{意图识别}
    Intent -->|编程任务| ProgTask[Programming Task]
    Intent -->|GitHub学习| LearnTask[Learning Task]
    Intent -->|知识归纳| MemTask[Memorize Task]
    Intent -->|管理命令| MgmtTask[Management Task]
    end

    subgraph Execution Layer
    ProgTask --> PA[programming-assistant]
    LearnTask --> G2S[github-to-skills]
    MgmtTask --> SM[skill-manager]
    end

    subgraph Knowledge Layer
    PA <-->|Async Retrieve/Summarize| KB[knowledge-base]
    G2S -->|Store Knowledge| KB
    MemTask -->|Direct Store| KB
    end

    subgraph Storage
    KB -->|Persist| FS[文件系统]
    end
```

### 设计原则

1. **统一入口**: 所有交互通过 `/evolve` 或自然语言由协调器接管
2. **智能调度**: 利用 Sequential Thinking 进行精准的任务分发
3. **异步非阻塞**: 耗时的知识操作全部异步化，提供流畅体验
4. **完整闭环**: 实现 "学习(GitHub) → 应用(Programming) → 总结(Evolution)" 的完整知识闭环
5. **模块化**: 每个功能模块都是独立的 Skill，可独立升级和管理
6. **跨平台**: 自动检测运行平台（OpenCode/Claude Code/Cursor），使用正确的路径

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
- 管理: "/evolve"、"怎么实现"、"为什么"

**核心机制**:
```python
# 智能调度协议
1. 意图识别: 识别用户意图类型（编程 / 知识归纳 / 仓库学习 / 手动启动）
2. 上下文分析: 分析会话上下文、历史对话和任务复杂度
3. 状态检查: 检查进化模式 (.opencode/.evolution_mode_active) 和协调器状态
4. 决策制定: 根据分析结果制定调度策略
5. 归纳总结: 将分析结果归纳为简洁的上下文摘要，传递给下游 skill
6. 执行调度: 执行相应的初始化、skill 加载或流程
7. 反馈输出: 向用户反馈执行结果和建议
```

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
- 实时更新进度日志（progress.txt）

**工作模式**:

| 模式 | 触发关键词 | 适用场景 | 工作流 |
|------|-----------|---------|--------|
| **Full Mode** | 创建、实现、添加、开发 | 新功能、完整模块开发 | 任务拆解 → 生成 TODO → 执行开发循环 → 进化检查 |
| **Simple Mode** | 修复、fix、bug、重构、优化、review | Bug修复、代码优化 | 问题分析 → 执行修复循环 → 进化检查 |
| **Direct Answer** | 怎么、为什么、解释 | 咨询、解释 | 直接回答，不触发工作流 |

**核心流程**:
```
场景识别 → 加载对应模式 → 任务拆解（sequential-thinking） → 执行循环 → 状态更新 → 进化检查
```

**状态文件**:
- `progress.txt`: 进度日志（每次状态更新）
- `feature_list.json`: 任务清单（Full/Simple Mode）
- `SOLUTION.md`: 架构设计（Full Mode）
- `TASK.md`: 实现计划（Full Mode）

**任务拆解原则**:
- 必须先用 `sequential-thinking` 分析
- 每个任务非常小（< 30分钟）
- 可测试验证
- 专注单一问题
- 按依赖顺序排列

---

### 3. github-to-skills (学习引擎)

**角色**: 眼睛、学习者

**功能**:
- 从 GitHub 仓库提取结构化知识
- 将非结构化代码转化为可复用的知识条目
- 自动识别架构范式、技术栈和最佳实践

**输出分类**:
- `patterns`: 架构模式、设计模式
- `tech-stacks`: 技术栈和依赖
- `best-practices`: 最佳实践

**工作流**:
```
Fetch Repo Info → Extract Patterns/Stacks → Store to knowledge-base
```

**核心能力**:
1. **Repo Info Fetching**: 获取仓库元数据（README、package.json、目录结构）
2. **Pattern Extraction**: 提取代码模式（组件设计、API 模式、状态管理）
3. **Tech Stack Detection**: 识别技术栈（框架、库、工具）
4. **Knowledge Storage**: 将提取的知识结构化存入知识库

---

### 4. skill-manager (运维工具)

**角色**: 医生、管家

**功能**:
- 管理 Skill 的生命周期（安装、更新、检查、启用/禁用）
- 确保 skills 目录下的 Skill 保持健康、最新且有序
- 支持 GitHub 版本检查和更新提示

**核心能力**:

| 能力 | 命令 | 说明 |
|------|------|------|
| **列表管理** | `list_skills.py` | 列出所有 Skill（名称、版本、状态、来源） |
| **扫描与更新检查** | `scan_and_check.py` | 对比 GitHub 远程仓库检查更新 |
| **启用/禁用** | `toggle_skill.py` | 软停用（移动目录，不删除文件） |
| **健康检查** | `health_check.py` | 检查完整性（Healthy/Outdated/Invalid） |
| **删除** | `delete_skill.py` | 永久移除 Skill |

**检查标准**:
- ✅ **Healthy**: `SKILL.md` 存在且格式正确
- ⚠️ **Outdated**: GitHub 有新版本
- ❌ **Invalid**: 缺少必要文件或 YAML 格式错误

**元数据规范**:
```yaml
metadata:
  github_url: "https://github.com/user/repo"  # 来源仓库
  github_hash: "a1b2c3d..."                   # 当前安装版本的 Commit Hash
  version: "1.0.0"                            # 语义化版本 (可选)
  status: "active"                            # 状态 (active/deprecated)
```

---

### 5. knowledge-base (海马体)

**角色**: 记忆、知识库

**功能**:
- 统一存储和索引所有知识
- 7 大分类的知识存储系统
- 支持异步检索（`retrieval-agent`）和异步归纳（`summarize-agent`）
- 基于触发词的智能知识匹配

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

**知识条目 Schema**:
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

**核心命令**:
```bash
# 查询
knowledge query --stats           # 统计
knowledge query --trigger "react,hooks"  # 按触发词
knowledge query --category problem       # 按分类
knowledge query --search "跨域"          # 全文搜索

# 触发检测
knowledge trigger --input "修复CORS问题"
knowledge trigger --input "..." --project .

# 归纳存储
echo "内容" | knowledge summarize --auto-store

# 存储
knowledge store --category experience --name "xxx"
```

**子代理**:

| 代理 | 用途 |
|------|------|
| `retrieval-agent` | 异步检索相关知识 |
| `summarize-agent` | 异步归纳经验 |

**数据位置**:
```
~/.config/opencode/knowledge/   # OpenCode
~/.claude/knowledge/            # Claude Code / Cursor
```

---

## 关键工作流

### 1. 编程 + 进化闭环 (The Evolution Loop)

```
用户请求 ("帮我修复这个Bug")
    ↓
evolving-agent (协调器)
    │
    ├─► Sequential Thinking 意图识别
    ├─► 检查进化模式 (.opencode/.evolution_mode_active)
    │
    ├─► [异步] 知识检索 (knowledge-retrieval)
    │      ↓
    │   .knowledge-context.md (上下文)
    │
    ▼
programming-assistant (执行器)
    │
    ├─► 模式选择 (Full Mode / Simple Mode)
    ├─► 任务拆解（sequential-thinking）
    ├─► 执行修复循环
    │
    ▼
任务完成
    ↓
evolving-agent (协调器)
    │
    ├─► 检测进化触发条件
    │   ├─ 进化模式激活?
    │   ├─ 复杂问题解决?
    │   └─ 用户明确要求?
    │
    ▼
[异步] 知识归纳 (knowledge-summarize)
    ↓
knowledge-base (存入新经验)
```

**进化触发条件**:
1. **进化模式激活**: `.opencode/.evolution_mode_active` 存在
2. **复杂问题解决**: 耗时超过阈值或涉及多个模块
3. **用户明确要求**: 用户说"记住这个"、"保存经验"等

---

### 2. GitHub 学习闭环 (The Learning Loop)

```
用户请求 ("学习这个仓库 https://github.com/xx/repo")
    ↓
evolving-agent (协调器)
    ↓
github-to-skills (学习器)
    │
    ├─► Fetch Repo Info
    │   ├─ README.md
    │   ├─ package.json / Cargo.toml / pom.xml
    │   └─ 目录结构
    │
    ├─► Extract Patterns/Stacks
    │   ├─ 组件设计模式
    │   ├─ API 设计模式
    │   ├─ 状态管理方案
    │   └─ 技术栈识别
    │
    └─► Store to knowledge-base
          │
          ├─ patterns/
          ├─ tech-stacks/
          └─ best-practices/
          │
          ▼
knowledge-base (更新索引)
    │
    ▼
(后续编程任务中自动复用该知识)
```

---

### 3. 知识检索流程 (Knowledge Retrieval)

```
任务开始
    ↓
knowledge-base 触发检测
    │
    ├─► 解析用户输入关键词
    ├─► 匹配知识条目的 triggers
    ├─► 按优先级排序
    │
    ▼
异步检索 (retrieval-agent)
    │
    ├─► 读取相关知识条目
    ├─► 生成上下文摘要
    │
    ▼
生成 .knowledge-context.md
    │
    ▼
传递给 programming-assistant
```

---

## 目录结构

```
evolving-programming-agent/
├── evolving-agent/                 # [Core] 顶层协调器
│   ├── SKILL.md                    # 协调器配置（触发词、元数据）
│   ├── command/
│   │   └── evolve.md              # /evolve 命令文档
│   ├── scripts/
│   │   ├── run.py                 # 统一 CLI 入口
│   │   │
│   │   ├── core/                  # 核心脚本
│   │   │   ├── toggle_mode.py     # 进化模式控制
│   │   │   ├── trigger_detector.py # 触发检测
│   │   │   ├── path_resolver.py   # 路径解析（跨平台）
│   │   │   └── ...
│   │   │
│   │   ├── knowledge/             # 知识库脚本
│   │   │   ├── query.py          # 知识查询
│   │   │   ├── store.py          # 知识存储
│   │   │   ├── summarizer.py     # 知识归纳
│   │   │   └── trigger.py        # 触发检测
│   │   │
│   │   ├── github/                # GitHub 学习脚本
│   │   │   ├── fetch_info.py     # 获取仓库信息
│   │   │   ├── extract_patterns.py # 提取模式
│   │   │   └── store_to_knowledge.py # 存储到知识库
│   │   │
│   │   └── programming/           # 编程助手脚本
│   │       ├── detect_project.py # 检测项目技术栈
│   │       ├── store_experience.py # 存储项目经验
│   │       └── query_experience.py # 查询项目经验
│   │
│   └── modules/
│       ├── programming-assistant/ # 执行引擎
│       │   ├── README.md
│       │   └── workflows/
│       │       ├── full-mode.md     # 完整开发模式
│       │       ├── simple-mode.md   # 快速修复模式
│       │       └── evolution-check.md # 进化检查流程
│       │
│       ├── github-to-skills/      # 学习引擎
│       │   ├── README.md
│       │   └── agents/
│       │       ├── fetcher.md      # 仓库信息获取
│       │       ├── extractor.md    # 模式提取
│       │       └── storer.md       # 知识存储
│       │
│       └── knowledge-base/        # 统一知识库
│           ├── README.md
│           ├── schema.json        # 知识条目 Schema
│           ├── index.json         # 知识索引
│           ├── agents/
│           │   ├── retrieval-agent.md  # 异步检索
│           │   └── summarize-agent.md  # 异步归纳
│           └── scripts/
│               └── knowledge_query.py
│
├── skill-manager/                  # [Util] 运维工具
│   ├── SKILL.md                    # 运维工具配置
│   └── scripts/
│       ├── list_skills.py         # 列出所有 Skill
│       ├── scan_and_check.py      # 扫描版本并检查 GitHub 更新
│       ├── health_check.py        # 综合健康状态检查
│       ├── toggle_skill.py        # 启用/禁用 (目录移动)
│       ├── delete_skill.py        # 删除 Skill
│       └── utils/
│           └── frontmatter_parser.py # YAML Frontmatter 解析
│
├── docs/                          # 文档
│   └── SOLUTION.md                # 本文件 - 架构设计文档
│
├── tests/                         # 测试
│   ├── test_knowledge_base.py
│   ├── test_github_to_skills.py
│   └── ...
│
├── scripts/                        # 安装/卸载脚本
│   ├── install.sh                 # 安装脚本
│   └── uninstall.sh               # 卸载脚本
│
├── requirements.txt               # Python 依赖
├── pytest.ini                     # pytest 配置
└── README.md                      # 项目说明
```

---

## 跨平台架构

Evolving Programming Agent 支持三大 AI 编程平台，自动检测运行环境并使用正确的路径：

### 平台映射

| 平台 | Skills 目录 | 知识目录 |
|------|-------------|----------|
| **OpenCode** | `~/.config/opencode/skills/` | `~/.config/opencode/knowledge/` |
| **Claude Code** | `~/.claude/skills/` | `~/.claude/knowledge/` |
| **Cursor** | `~/.claude/skills/` | `~/.claude/knowledge/` |

### 路径自动解析

系统通过 `run.py` 的 `path_resolver.py` 模块自动检测当前平台：

```python
def detect_platform() -> str:
    """检测当前平台 (opencode 或 claude)"""
    # 1. 检查环境变量
    env_platform = os.environ.get('SKILLS_PLATFORM', '').lower()
    if env_platform in ('opencode', 'claude'):
        return env_platform
    
    # 2. 检查哪个 skills 目录存在 evolving-agent
    opencode_skills = Path.home() / '.config' / 'opencode' / 'skills' / 'evolving-agent'
    claude_skills = Path.home() / '.claude' / 'skills' / 'evolving-agent'
    
    if opencode_skills.exists():
        return 'opencode'
    if claude_skills.exists():
        return 'claude'
    
    # 3. 默认 opencode
    return 'opencode'
```

### 跨平台命令

所有命令使用环境变量或自动检测，无需手动指定路径：

```bash
# 方式 1: 使用环境变量（推荐）
export SKILLS_DIR=$([ -d ~/.config/opencode/skills/evolving-agent ] && echo ~/.config/opencode/skills || echo ~/.claude/skills)
python $SKILLS_DIR/evolving-agent/scripts/run.py info

# 方式 2: 自动检测（run.py 内部实现）
python ~/.config/opencode/skills/evolving-agent/scripts/run.py info  # OpenCode
python ~/.claude/skills/evolving-agent/scripts/run.py info          # Claude Code / Cursor
```

---

## 核心特性实现

### 1. 智能意图识别

使用 `sequential-thinking` 工具进行深度分析：

```
用户输入 → Sequential Thinking → 意图分类 → 模块调度
```

**意图类型**:
- **编程任务**: 开发、实现、创建、添加、修复、重构、优化
- **GitHub学习**: 学习仓库、从GitHub学习、分析开源项目
- **知识归纳**: 记住这个、保存经验、复盘、/evolve
- **管理命令**: 列出skill、检查skill、启用skill、禁用skill

### 2. 异步知识流

**检索流程（任务开始时）**:
```python
Task(
    subagent_type="general",
    description="Knowledge retrieval",
    prompt="python run.py knowledge trigger --input '...' --format context > .knowledge-context.md"
)
```

**归纳流程（任务结束后）**:
```python
Task(
    subagent_type="general",
    description="Knowledge summarization",
    prompt="echo '{summary}' | python run.py knowledge summarize --auto-store"
)
```

### 3. 进化模式控制

标记文件: `.opencode/.evolution_mode_active`

- **激活时**: 所有模块任务完成后自动提取经验
- **未激活时**: 仅在复杂问题或用户要求时提取

```bash
python run.py mode --on    # 开启
python run.py mode --off   # 关闭
python run.py mode --status # 查看状态
```

### 4. 独立虚拟环境

每个 Skill 拥有独立的 Python 虚拟环境，避免依赖冲突：

```
evolving-agent/
└── .venv/
    ├── bin/python
    ├── lib/python3.x/site-packages/
    └── ...

skill-manager/  # 复用 evolving-agent 的虚拟环境
```

**创建虚拟环境**:
```bash
cd ~/.config/opencode/skills/evolving-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 总结

v4.0 架构通过引入 `evolving-agent` 作为统一协调器，实现了：

1. **入口统一**: 所有交互通过 `/evolve` 或自然语言由协调器接管
2. **调度智能**: 利用 Sequential Thinking 进行精准的任务分发
3. **体验流畅**: 耗时的知识操作全部异步化，不再阻塞用户
4. **闭环完整**: 实现了 "学习(GitHub) → 应用(Programming) → 总结(Evolution)" 的完整知识闭环
5. **架构清晰**: 模块化设计，每个组件职责明确，易于维护和扩展
6. **跨平台支持**: 自动检测运行环境，支持 OpenCode、Claude Code、Cursor
7. **独立环境**: 每个 Skill 拥有独立虚拟环境，避免依赖冲突

**核心优势**:
- 🧠 **智能**: 基于 Sequential Thinking 的深度理解和调度
- ⚡️ **高效**: 异步知识流，不阻塞主任务
- 🔄 **进化**: 从每次任务中学习，持续优化
- 🎯 **精准**: 基于触发词的智能知识匹配
- 🌐 **通用**: 跨平台支持，适应不同 AI 编程环境
- 🧩 **模块化**: 插件化架构，易于扩展和维护

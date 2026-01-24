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

## 核心架构 (v4.0 Unified Coordinator)

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

### 核心组件

#### 1. evolving-agent (顶层协调器)
**角色**: 大脑、指挥官
- **功能**: 统一入口，负责意图识别、任务调度、进化模式管理。
- **机制**: 使用 `sequential-thinking` 进行深度分析，决定调用哪个子能力。
- **命令**: `/evolve` (手动启动/管理)

#### 2. programming-assistant (执行引擎)
**角色**: 手、执行者
- **功能**: 负责具体的编程任务（开发、修复、重构）。
- **模式**: 
  - Full Mode (完整开发)
  - Simple Mode (快速修复)
- **特性**: 异步集成知识检索和归纳，不阻塞主流程。

#### 3. github-to-skills (学习引擎)
**角色**: 眼睛、学习者
- **功能**: 从 GitHub 仓库提取结构化知识。
- **输出**: 将非结构化代码转化为 `patterns`, `tech-stacks`, `best-practices` 并存入知识库。

#### 4. skill-manager (运维工具)
**角色**: 医生、管家
- **功能**: 管理 Skill 的生命周期（安装、更新、检查、启用/禁用）。

#### 5. knowledge-base (海马体)
**角色**: 记忆、知识库
- **功能**: 统一存储和索引所有知识。
- **结构**: 7 大分类 (`experience`, `tech-stack`, `scenario`, `problem`, `testing`, `pattern`, `skill`)。
- **能力**: 支持异步检索 (`retrieval-agent`) 和异步归纳 (`summarize-agent`)。

---

## 关键工作流

### 1. 编程 + 进化闭环 (The Evolution Loop)

```
用户请求 ("帮我修复这个Bug")
   ↓
evolving-agent (协调器)
   │
   ├─► [异步] 知识检索 (knowledge-retrieval)
   │      ↓
   │   .knowledge-context.md (上下文)
   │
   ▼
programming-assistant (执行器)
   │
   ├─► 读取上下文，执行修复
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

### 2. GitHub 学习闭环 (The Learning Loop)

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

## 目录结构

```
evolving-programming-agent/
├── evolving-agent/            # [Core] 顶层协调器
│   ├── SKILL.md
│   ├── command/
│   │   └── evolve.md          # /evolve 命令文档
│   └── scripts/
│       ├── toggle_mode.py     # 进化模式控制
│       └── trigger_detector.py # 触发检测
│
├── programming-assistant/     # [Core] 编程执行器
│   ├── SKILL.md
│   └── scripts/
│       ├── store_experience.py
│       └── query_experience.py
│
├── github-to-skills/          # [Core] 学习引擎
│   ├── SKILL.md
│   └── scripts/
│       ├── fetch_github_info.py
│       ├── extract_knowledge.py
│       └── store_to_knowledge.py
│
├── skill-manager/             # [Util] 运维工具
│   ├── SKILL.md
│   └── scripts/
│       ├── health_check.py
│       └── ...
│
├── knowledge-base/            # [Infra] 统一知识库
│   ├── SKILL.md
│   ├── schema.json
│   ├── index.json
│   ├── agents/                # 异步子代理
│   │   ├── retrieval-agent.md
│   │   └── summarize-agent.md
│   └── scripts/
│       ├── knowledge_query.py
│       └── ...
│
├── docs/                      # 文档
├── tests/                     # 测试
├── install.sh                 # 安装脚本
└── uninstall.sh               # 卸载脚本
```

---

## 总结

v4.0 架构通过引入 `evolving-agent` 作为统一协调器，实现了：
1. **入口统一**: 所有交互通过 `/evolve` 或自然语言由协调器接管。
2. **调度智能**: 利用 Sequential Thinking 进行精准的任务分发。
3. **体验流畅**: 耗时的知识操作全部异步化，不再阻塞用户。
4. **闭环完整**: 实现了 "学习(GitHub) -> 应用(Programming) -> 总结(Evolution)" 的完整知识闭环。

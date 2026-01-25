---
name: evolving-agent
description: AI 编程系统的顶层协调器，作为统一入口协调编程助手、知识进化和 GitHub 仓库学习流程。当用户说"开发"、"实现"、"创建"、"添加"、"修复"、"报错"、"重构"、"优化"、"review"、"评审"、"继续开发"、"怎么实现"、"为什么"、"记住这个"、"保存经验"、"存储这个方案"、"复盘"、"总结经验"、"evolve"、"/evolve"、"学到了什么"、"记录这次的教训"、"学习这个仓库"、"从 GitHub 学习"、"提取最佳实践"、"分析GitHub"、"分析开源项目"时使用。
license: MIT
metadata:
  triggers: ["开发", "实现", "创建", "添加", "修复", "报错", "重构", "优化", "review", "评审", "继续开发", "怎么实现", "为什么", "记住这个", "保存经验", "存储这个方案", "复盘", "总结经验", "evolve", "/evolve", "学到了什么", "记录这次的教训", "学习这个仓库", "从 GitHub 学习", "提取最佳实践", "分析GitHub", "分析开源项目"]
---

# Evolving Agent

AI 编程系统的顶层协调器，作为统一入口协调编程助手、知识进化和 GitHub 仓库学习流程。

## 智能调度协议

**当此 skill 被触发时，必须使用 `sequential-thinking` 工具进行深度分析和调度：**

**核心原则**: 先用 sequential-thinking 归纳总结，再传递给下游 skill，节约 token。

1. **意图识别**: 识别用户意图类型（编程 / 知识归纳 / 仓库学习 / 手动启动）
2. **上下文分析**: 分析会话上下文、历史对话和任务复杂度
3. **状态检查**: 检查进化模式 (`.opencode/.evolution_mode_active`) 和协调器状态
4. **决策制定**: 根据分析结果制定调度策略
5. **归纳总结**: **将分析结果归纳为简洁的上下文摘要**，传递给下游 skill
6. **执行调度**: 执行相应的初始化、skill 加载或流程
7. **反馈输出**: 向用户反馈执行结果和建议

## 核心职责

1. **协调器**: 统一入口，协调 programming-assistant、知识进化和 GitHub 仓库学习
2. **智能调度**: 使用 sequential-thinking 进行深度意图分析和智能决策
3. **自动识别**: 识别用户意图（编程任务 / 知识归纳 / GitHub 学习）
4. **进化模式**: 管理 session 级的持续知识提取状态
5. **经验提取**: 将用户反馈转化为结构化数据
6. **渐进式存储**: 按技术栈/上下文分类存储经验
7. **仓库学习**: 从 GitHub 仓库自动提取编程知识并集成到知识库

## 触发与流程路由

### 1. 编程任务（默认流程）

**触发词**：
"开发"、"实现"、"创建"、"添加"、"修复"、"报错"、"重构"、"优化"、"review"、"评审"、"继续开发"、"怎么实现"、"为什么"

**三阶段调度流程**：

```
┌─────────────────────────────────────────────────────────────────┐
│                    阶段 1: 前置处理                              │
├─────────────────────────────────────────────────────────────────┤
│  □ 使用 sequential-thinking 分析用户意图                        │
│  □ 检查进化模式状态:                                            │
│    python evolving-agent/scripts/toggle_mode.py --status        │
│  □ 如果未激活 → 执行初始化:                                     │
│    python evolving-agent/scripts/toggle_mode.py --init          │
│  □ 归纳上下文摘要，准备传递给下游 skill                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    阶段 2: 主要任务                              │
├─────────────────────────────────────────────────────────────────┤
│  □ 加载 programming-assistant skill                             │
│  □ 传递上下文（任务类型、进化状态、知识上下文）                  │
│  □ programming-assistant 内部流程:                              │
│    - 场景识别: Full Mode / Simple Mode / Direct Answer          │
│    - 状态检查: 读取 progress.txt, feature_list.json             │
│    - 执行任务: 按模式内工作流执行                               │
│    - 状态更新: 更新状态文件                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    阶段 3: 后置处理                              │
├─────────────────────────────────────────────────────────────────┤
│  由 programming-assistant 的 evolution-check.md 执行:           │
│  □ 检查 .opencode/.evolution_mode_active 标记                   │
│  □ 分析会话是否满足经验提取条件:                                │
│    - 进化模式激活 → 自动提取                                    │
│    - 复杂问题(尝试>1次) → 提取                                  │
│    - 用户说"记住" → 提取                                        │
│  □ 如满足条件 → 运行 trigger_detector.py + knowledge_summarizer │
│  □ 存储经验到知识库                                             │
└─────────────────────────────────────────────────────────────────┘
```

**执行清单 (Checklist)**:
1. [ ] **前置**: 检查进化模式状态，必要时执行 `--init`
2. [ ] **前置**: 使用 sequential-thinking 归纳上下文
3. [ ] **主任务**: 加载 programming-assistant skill
4. [ ] **后置**: programming-assistant 完成后自动执行 evolution-check.md

**模式分发规则**（由 programming-assistant 执行）：

| 关键词 | 模式 |
|-------|------|
| "创建"、"新建"、"初始化"、"实现"、"添加"、"开发" | Full Mode |
| "修复"、"fix"、"bug"、"报错"、"重构"、"优化"、"review" | Simple Mode |
| "怎么"、"为什么"、"解释" | Direct Answer |

> **重要**: 后置处理（进化检查）由 programming-assistant 内部的 `evolution-check.md` 模块执行。这样设计的原因是 programming-assistant 更了解任务执行上下文，能更准确判断是否需要提取经验。

### 2. 知识归纳请求

**触发词**：
"记住这个"、"保存经验"、"存储这个方案"、"复盘"、"总结经验"、"学到了什么"、"记录这次的教训"

**三阶段调度流程**：

```
┌─────────────────────────────────────────────────────────────────┐
│                    阶段 1: 前置处理                              │
├─────────────────────────────────────────────────────────────────┤
│  □ 使用 sequential-thinking 分析用户意图                        │
│  □ 检查进化模式状态:                                            │
│    python evolving-agent/scripts/toggle_mode.py --status        │
│  □ 如果未激活 → 执行初始化:                                     │
│    python evolving-agent/scripts/toggle_mode.py --init          │
│  □ 归纳会话上下文，识别待提取的经验要点                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    阶段 2: 主要任务                              │
├─────────────────────────────────────────────────────────────────┤
│  □ 加载 knowledge-base skill                                    │
│  □ 传递上下文（会话摘要、用户意图、进化状态）                   │
│  □ knowledge-base 内部流程:                                     │
│    - 分析会话上下文，提取有价值经验                             │
│    - 执行 trigger_detector.py 进行结构化提取                    │
│    - 调用 knowledge_summarizer.py 归纳知识                      │
│    - 存储到知识库对应分类                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    阶段 3: 后置处理                              │
├─────────────────────────────────────────────────────────────────┤
│  由 knowledge-base 执行:                                        │
│  □ 检查 .opencode/.evolution_mode_active 标记                   │
│  □ 验证存储结果，确认知识已正确分类                             │
│  □ 更新 knowledge-base/index.json 索引                          │
│  □ 反馈存储结果给用户                                           │
└─────────────────────────────────────────────────────────────────┘
```

**执行清单 (Checklist)**:
1. [ ] **前置**: 检查进化模式状态，必要时执行 `--init`
2. [ ] **前置**: 使用 sequential-thinking 归纳会话上下文
3. [ ] **主任务**: 加载 knowledge-base skill，执行经验提取
4. [ ] **后置**: knowledge-base 完成存储并反馈结果

> **重要**: 后置处理由 knowledge-base 内部执行。这样设计的原因是 knowledge-base 更了解知识存储上下文，能更准确进行分类和索引更新。

### 3. GitHub 仓库学习

**触发词**：
"学习这个仓库"、"从 GitHub 学习"、"提取这个项目的最佳实践"、"把这个仓库的经验存起来"、"分析这个开源项目"

**三阶段调度流程**：

```
┌─────────────────────────────────────────────────────────────────┐
│                    阶段 1: 前置处理                              │
├─────────────────────────────────────────────────────────────────┤
│  □ 使用 sequential-thinking 分析用户意图                        │
│  □ 检查进化模式状态:                                            │
│    python evolving-agent/scripts/toggle_mode.py --status        │
│  □ 如果未激活 → 执行初始化:                                     │
│    python evolving-agent/scripts/toggle_mode.py --init          │
│  □ 提取 GitHub URL 或仓库名称                                   │
│  □ 确定学习重点（架构 / 最佳实践 / 全部）                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    阶段 2: 主要任务                              │
├─────────────────────────────────────────────────────────────────┤
│  □ 加载 github-to-skills skill                                  │
│  □ 传递上下文（GitHub URL、学习重点、进化状态）                 │
│  □ github-to-skills 内部流程:                                   │
│    - 获取仓库信息: fetch_github_info.py                         │
│    - 分析技术栈、架构模式、最佳实践                             │
│    - 提取结构化知识: extract_patterns.py                        │
│    - 存储到知识库: store_to_knowledge.py                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    阶段 3: 后置处理                              │
├─────────────────────────────────────────────────────────────────┤
│  由 github-to-skills 执行:                                      │
│  □ 检查 .opencode/.evolution_mode_active 标记                   │
│  □ 验证知识已正确存储到 knowledge-base 各分类                   │
│  □ 更新 knowledge-base/index.json 索引                          │
│  □ 生成学习报告，告知用户提取了哪些关键知识                     │
│  □ 如果学习过程中发现额外经验 → 触发 knowledge_summarizer       │
└─────────────────────────────────────────────────────────────────┘
```

**执行清单 (Checklist)**:
1. [ ] **前置**: 检查进化模式状态，必要时执行 `--init`
2. [ ] **前置**: 使用 sequential-thinking 分析仓库学习目标
3. [ ] **主任务**: 加载 github-to-skills skill，执行仓库分析
4. [ ] **后置**: github-to-skills 完成存储、更新索引并反馈结果

> **重要**: 后置处理由 github-to-skills 内部执行。这样设计的原因是 github-to-skills 更了解仓库分析上下文，能更准确进行知识分类和索引更新。

### 4. 手动启动 (/evolve)

**触发词**：
"/evolve"

**调度逻辑**：
1. 执行 `~/.config/opencode/skills/evolving-agent/.venv/bin/python scripts/toggle_mode.py --init`
2. 输出详细引导提示
3. 等待用户输入编程任务

## 进化模式 (Evolution Mode)

提供会话级持久化，开启后会在整个 session 中持续生效。

**工作原理**：
1. 创建标记文件 `.opencode/.evolution_mode_active`
2. **所有下游 skill** 在任务完成后自动检测该文件：
   - `programming-assistant`: 每个开发/修复循环结束后检测
   - `knowledge-base`: 知识归纳完成后检测
   - `github-to-skills`: 仓库学习完成后检测
3. 如果存在，自动运行触发检测（降低阈值），提取经验并异步存储

**控制命令**：

> **重要**: 下面的命令已包含 Python 解释器路径，直接复制执行即可，**不要**在前面再加 `python`！

```bash
# 完整初始化
~/.config/opencode/skills/evolving-agent/.venv/bin/python ~/.config/opencode/skills/evolving-agent/scripts/toggle_mode.py --init

# 仅开启
~/.config/opencode/skills/evolving-agent/.venv/bin/python ~/.config/opencode/skills/evolving-agent/scripts/toggle_mode.py --on

# 关闭
~/.config/opencode/skills/evolving-agent/.venv/bin/python ~/.config/opencode/skills/evolving-agent/scripts/toggle_mode.py --off

# 查看状态
~/.config/opencode/skills/evolving-agent/.venv/bin/python ~/.config/opencode/skills/evolving-agent/scripts/toggle_mode.py --status
```

在开发目录中可使用简化命令：
```bash
python evolving-agent/scripts/toggle_mode.py --status
```

## Sequential-Thinking 示例

### 场景：新编程任务
```
Input: "帮我实现一个用户登录功能"

Thinking Process:
Thought 1: 检测关键词 "实现" → 编程任务
Thought 2: 检查状态 → 进化模式未激活
Thought 3: 决策 → 执行 --init，然后加载 programming-assistant
Thought 4: 归纳上下文 → 任务类型: 功能开发, 模式: Full Mode, 关键需求: 用户登录
Thought 5: 执行调度 → 启动协调器，加载编程助手，传递归纳后的上下文
```

### 场景：GitHub 仓库学习
```
Input: "学习这个仓库 https://github.com/facebook/react"

Thinking Process:
Thought 1: 检测关键词 "学习这个仓库" → GitHub 学习
Thought 2: 提取 URL → https://github.com/facebook/react
Thought 3: 决策 → 激活 github-to-skills
Thought 4: 执行调度 → 获取信息 → 提取知识 → 存储
```

## 存储与脚本

### 存储结构
- `experience/`: 本地经验存储
- `knowledge-base/`: 统一知识库存储

### 关键脚本
- `evolving-agent/scripts/toggle_mode.py`: 进化模式控制
- `evolving-agent/scripts/trigger_detector.py`: 触发检测
- `knowledge-base/scripts/knowledge_summarizer.py`: 知识归纳
- `knowledge-base/scripts/knowledge_query.py`: 知识查询

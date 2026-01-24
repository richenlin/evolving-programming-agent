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

**调度逻辑**：
1. 检查进化模式状态
   - **未激活**：执行 `~/.config/opencode/skills/evolving-agent/.venv/bin/python scripts/toggle_mode.py --init`（启动协调器 + 开启进化模式）
   - **已激活**：跳过初始化，直接进入下一步
2. 加载 **programming-assistant**
3. 传递上下文（任务类型、场景等）
4. **programming-assistant 内部流程**：
   - 场景识别：根据关键词选择 Full Mode 或 Simple Mode
   - 状态检查：读取 `progress.txt` 和 `feature_list.json`（了解上一步完成情况）
   - 执行任务：按模式内工作流执行
   - 状态更新：更新状态文件（给下一步指引）
5. 进入编程 → 知识进化迭代循环

**模式分发规则**（由 programming-assistant 执行）：

| 关键词 | 模式 |
|-------|------|
| "创建"、"新建"、"初始化"、"实现"、"添加"、"开发" | Full Mode |
| "修复"、"fix"、"bug"、"报错"、"重构"、"优化"、"review" | Simple Mode |
| "怎么"、"为什么"、"解释" | Direct Answer |

### 2. 知识归纳请求

**触发词**：
"记住这个"、"保存经验"、"存储这个方案"、"复盘"、"总结经验"、"学到了什么"、"记录这次的教训"

**调度逻辑**：
1. 分析会话上下文，提取有价值经验
2. 执行 `trigger_detector.py` 进行结构化提取
3. 调用 `knowledge_summarizer.py` 存储到知识库
4. 反馈存储结果

### 3. GitHub 仓库学习

**触发词**：
"学习这个仓库"、"从 GitHub 学习"、"提取这个项目的最佳实践"、"把这个仓库的经验存起来"、"分析这个开源项目"

**调度逻辑**：
1. 提取 GitHub URL 或仓库名称
2. 自动激活 **github-to-skills**
3. 执行：获取信息 → 分析提取 → 存储知识 → 更新索引
4. 反馈学习结果，告知知识可供后续使用

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
2. `programming-assistant` 在每次响应结束前自动检测该文件
3. 如果存在，自动运行触发检测（降低阈值），提取经验并异步存储

**控制命令**：
- `~/.config/opencode/skills/evolving-agent/.venv/bin/python scripts/toggle_mode.py --init` (完整初始化)
- `~/.config/opencode/skills/evolving-agent/.venv/bin/python scripts/toggle_mode.py --on` (仅开启)
- `~/.config/opencode/skills/evolving-agent/.venv/bin/python scripts/toggle_mode.py --off` (关闭)
- `~/.config/opencode/skills/evolving-agent/.venv/bin/python scripts/toggle_mode.py --status` (查看状态)

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

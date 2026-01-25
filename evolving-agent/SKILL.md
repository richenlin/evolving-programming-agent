---
name: evolving-agent
description: AI 编程系统协调器。触发词："开发"、"实现"、"创建"、"添加"、"修复"、"报错"、"重构"、"优化"、"review"、"评审"、"继续开发"、"怎么实现"、"为什么"、"记住这个"、"保存经验"、"提取最佳实践"、"分析GitHub"、"学习仓库"、"/evolve"
license: MIT

metadata:
  triggers: ["开发"、"实现"、"创建"、"添加"、"修复"、"报错"、"重构"、"优化"、"review"、"评审"、"继续开发"、"怎么实现"、"为什么"、"记住这个"、"保存经验"、"提取最佳实践"、"分析GitHub"、"学习仓库"、"evolve"]
---

# Evolving Agent - 协调器

统一入口，负责意图识别和模块调度。

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

## 快速路由

| 意图 | 触发词 | 加载模块 |
|------|--------|----------|
| **编程** | 开发、实现、创建、添加、修复、重构、优化、review | `@load modules/programming-assistant/README.md` |
| **归纳** | 记住这个、保存经验、复盘、/evolve | `@load modules/knowledge-base/README.md` |
| **学习** | 学习仓库、从GitHub学习、分析开源项目 | `@load modules/github-to-skills/README.md` |

## 核心流程

```
用户输入 → 意图识别 → 前置检查 → 加载模块 → 执行 → 后置检查
```

### 前置检查（必须）

```bash
# 检查进化模式
python scripts/run.py mode --status

# 未激活则初始化
python scripts/run.py mode --init
```

### 后置检查（由各模块执行）

各模块完成后自动检查 `.opencode/.evolution_mode_active`，满足条件则提取经验。

## 模块职责

| 模块 | 职责 | 详细文档 |
|------|------|----------|
| **programming-assistant** | 代码生成、修复、重构 | `modules/programming-assistant/` |
| **knowledge-base** | 知识存储、查询、归纳 | `modules/knowledge-base/` |
| **github-to-skills** | 仓库学习、模式提取 | `modules/github-to-skills/` |

## 命令速查

```bash
# 进化模式
python scripts/run.py mode --status|--init|--off

# 知识库
python scripts/run.py knowledge query --stats
python scripts/run.py knowledge trigger --input "..."

# GitHub
python scripts/run.py github fetch <url>

# 项目
python scripts/run.py project detect .

# 环境
python scripts/run.py info
```

## 进化模式

标记文件: `.opencode/.evolution_mode_active`

- **激活时**: 所有模块任务完成后自动提取经验
- **未激活时**: 仅在复杂问题或用户要求时提取

## 调度示例

### 编程任务
```
Input: "帮我实现登录功能"
→ 意图: 编程 (关键词"实现")
→ 前置: mode --init
→ 加载: @load modules/programming-assistant/README.md
→ 模式: Full Mode (新功能)
```

### 知识归纳
```
Input: "记住这个解决方案"
→ 意图: 归纳 (关键词"记住")
→ 加载: @load modules/knowledge-base/README.md
→ 执行: 提取经验 → 存储
```

### 仓库学习
```
Input: "学习 https://github.com/user/repo"
→ 意图: 学习 (关键词"学习")
→ 加载: @load modules/github-to-skills/README.md
→ 执行: fetch → extract → store
```

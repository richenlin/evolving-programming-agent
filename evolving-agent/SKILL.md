---
name: evolving-agent
description: AI 编程系统协调器。触发词："开发"、"实现"、"创建"、"添加"、"修复"、"报错"、"重构"、"优化"、"review"、"评审"、"继续开发"、"怎么实现"、"为什么"、"记住这个"、"保存经验"、"提取最佳实践"、"分析GitHub"、"学习仓库"、"/evolve"
license: MIT
metadata:
  triggers: ["开发", "实现", "创建", "添加", "修复", "报错", "重构", "优化", "review", "评审", "继续开发", "怎么实现", "为什么", "记住这个", "保存经验", "提取最佳实践", "分析GitHub", "学习仓库", "evolve"]
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

## ⚠️ 强制调度规则（必须执行）

**识别到意图后，必须立即加载对应模块并执行，不要停止或等待确认！**

| 意图 | 触发词 | 必须执行的操作 |
|------|--------|----------------|
| **编程** | 开发、实现、创建、添加、修复、重构、优化、review | 1. 读取 `$SKILLS_DIR/evolving-agent/modules/programming-assistant/README.md` <br> 2. 按照其中的流程执行 |
| **归纳** | 记住这个、保存经验、复盘、/evolve | 1. 读取 `$SKILLS_DIR/evolving-agent/modules/knowledge-base/README.md` <br> 2. 按照其中的流程执行 |
| **学习** | 学习仓库、从GitHub学习、分析开源项目 | 1. 读取 `$SKILLS_DIR/evolving-agent/modules/github-to-skills/README.md` <br> 2. 按照其中的流程执行 |

```
❌ 禁止: 完成意图识别后输出分析报告然后停止
✅ 必须: 识别意图 → 立即加载模块 → 立即开始执行任务
```

## 跨平台配置

> **跨平台支持**: 根据当前运行的平台，skills 目录位置不同：
> - **OpenCode**: `~/.config/opencode/skills`
> - **Claude Code / Cursor**: `~/.claude/skills`
>
> 执行命令前先设置路径变量：
> ```bash
> SKILLS_DIR=$([ -d ~/.config/opencode/skills/evolving-agent ] && echo ~/.config/opencode/skills || echo ~/.claude/skills)
> ```
>
> 后续所有命令使用 `$SKILLS_DIR` 变量。

## 核心流程（强制执行）

```
步骤1: 设置路径变量
  SKILLS_DIR=$([ -d ~/.config/opencode/skills/evolving-agent ] && echo ~/.config/opencode/skills || echo ~/.claude/skills)

步骤2: 初始化进化模式
  python $SKILLS_DIR/evolving-agent/scripts/run.py mode --init

步骤3: 意图识别
  识别用户意图: 编程 / 归纳 / 学习

步骤4: 知识检索（编程任务必须执行）
  如果是编程意图，执行异步知识检索：
  python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge trigger --input "用户输入" --format context > .knowledge-context.md
  
  然后读取 .knowledge-context.md 获取相关知识

步骤5: 加载对应模块
  ├─ 编程意图 → 读取 $SKILLS_DIR/evolving-agent/modules/programming-assistant/README.md
  ├─ 归纳意图 → 读取 $SKILLS_DIR/evolving-agent/modules/knowledge-base/README.md
  └─ 学习意图 → 读取 $SKILLS_DIR/evolving-agent/modules/github-to-skills/README.md

步骤6: 按照模块文档执行任务
  结合 .knowledge-context.md 中的知识（如有），执行模块中定义的完整流程
```

**重要**: 
- 步骤4的知识检索对于编程任务是强制的，可以帮助利用历史经验
- 步骤5和步骤6必须连续执行，不要在中间停止！

### 后置检查（由各模块执行）

各模块完成后自动检查 `.opencode/.evolution_mode_active`，满足条件则提取经验。

## 模块职责

| 模块 | 职责 | 详细文档 |
|------|------|----------|
| **programming-assistant** | 代码生成、修复、重构 | `modules/programming-assistant/` |
| **knowledge-base** | 知识存储、查询、归纳 | `modules/knowledge-base/` |
| **github-to-skills** | 仓库学习、模式提取 | `modules/github-to-skills/` |

## 命令速查

**重要**: 所有命令使用 `$SKILLS_DIR` 变量，可在任意目录执行。

```bash
# 设置路径变量（每个 shell 会话执行一次）
SKILLS_DIR=$([ -d ~/.config/opencode/skills/evolving-agent ] && echo ~/.config/opencode/skills || echo ~/.claude/skills)

# 进化模式
python $SKILLS_DIR/evolving-agent/scripts/run.py mode --status|--init|--off

# 知识库
python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge query --stats
python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge trigger --input "..."

# GitHub
python $SKILLS_DIR/evolving-agent/scripts/run.py github fetch <url>

# 项目
python $SKILLS_DIR/evolving-agent/scripts/run.py project detect .

# 环境
python $SKILLS_DIR/evolving-agent/scripts/run.py info
```

## 进化模式

标记文件: `.opencode/.evolution_mode_active`

- **激活时**: 所有模块任务完成后自动提取经验
- **未激活时**: 仅在复杂问题或用户要求时提取

## 调度示例

### 编程任务
```
Input: "帮我实现登录功能"

执行步骤:
1. 设置 SKILLS_DIR
2. 运行 mode --init
3. 识别意图: 编程 (关键词"实现")
4. 知识检索:
   python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge trigger \
     --input "实现登录功能" --format context > .knowledge-context.md
   读取 .knowledge-context.md 获取相关经验
5. 立即读取: $SKILLS_DIR/evolving-agent/modules/programming-assistant/README.md
6. 按 README.md 中的流程:
   - 识别为 Full Mode (新功能)
   - 结合 .knowledge-context.md 中的知识
   - 读取/创建 feature_list.json 和 progress.txt
   - 开始执行开发循环
   - 循环执行直到所有任务完成
7. 执行进化检查，归纳新经验
```

### 知识归纳
```
Input: "记住这个解决方案"

执行步骤:
1. 设置 SKILLS_DIR
2. 识别意图: 归纳 (关键词"记住")
3. 立即读取: $SKILLS_DIR/evolving-agent/modules/knowledge-base/README.md
4. 执行: 提取经验 → 存储到知识库
```

### 仓库学习
```
Input: "学习 https://github.com/user/repo"

执行步骤:
1. 设置 SKILLS_DIR
2. 识别意图: 学习 (关键词"学习")
3. 立即读取: $SKILLS_DIR/evolving-agent/modules/github-to-skills/README.md
4. 执行: fetch → extract → store
```

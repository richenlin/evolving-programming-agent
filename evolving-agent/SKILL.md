---
name: evolving-agent
description: 协调器 - 编排和管理所有 skill 组件，实现持续学习进化编程智能体的核心协调层。
type: orchestrator
license: MIT
metadata:
  version: "1.0.0"
  author: Khazix
  dependencies: ["github-to-skills", "skill-manager", "skill-evolution-manager", "programming-assistant"]
---

# Evolving Agent - 协调器

这是整个 Evolving Programming Agent 系统的**协调层**，负责编排和管理四个核心 skill 组件。

## 核心职责

1.  **学习触发器**：检测用户输入中的 GitHub URL，触发学习流程
2.  **进化触发器**：在编程任务结束后，自动触发进化流程
3.  **健康检查器**：定期扫描并检测过期或无效的 skill
4.  **会话管理器**：追踪会话状态，持久化上下文信息

## 触发条件

### 学习流程触发

**触发模式**：
- 用户发送 GitHub 仓库 URL
- "学习这个仓库"
- "提取这个项目的代码规范"
- "从这个项目中学习最佳实践"

**检测关键词**：
- `https://github.com/...`
- `http://github.com/...`
- `github.com/...`
- `learn`, `学习`, `提取`, `extract`

### 管理流程触发

**触发命令**：
- `/skill-manager check`
- `/skill-manager list`
- `/skill-manager enable <name>`
- `/skill-manager disable <name>`
- `/skill-manager health`
- "检查 skill 更新"
- "列出所有 skill"
- "启用/禁用 skill"

### 进化流程触发

**触发条件**（在 programming-assistant 会话结束时）：
1. 修复了复杂 Bug（连续尝试 > 1 次）
2. 用户给出明确反馈（"记住"、"保存"、"重要"等）
3. 发现了新的最佳实践
4. 使用了非标准解决方案

**自动触发**：
- 在 programming-assistant 中配置 `auto_evolve: true`
- 达到触发阈值后自动调用 `/evolve`

## 协调工作流程

```
用户输入
    │
    ▼
输入分析器
    │
    ├── GitHub URL? ───▶ 学习流程 (github-to-skills)
    ├── 编程任务? ───▶ 执行流程 (programming-assistant) ───▶ 进化流程 (skill-evolution-manager)
    └── 管理命令? ───▶ 管理流程 (skill-manager)
```

### 学习流程（Learning Workflow）

```
用户: 学习这个仓库 https://github.com/example/react-app
    │
    ▼
1. 触发 github-to-skills (学习模式)
    │
    ├── fetch_github_info.py - 获取仓库信息
    ├── extract_patterns.py - 提取编程范式
    │   ├── 分析项目架构
    │   ├── 检测技术栈
    │   └── 提取最佳实践
    │
    └── 生成 knowledge-addon.md
    │
    ▼
2. 附加到 programming-assistant
    │
    └── 编程助手下次使用时自动应用这些范式
```

### 进化流程（Evolution Workflow）

```
用户: 帮我修复这个 bug
助手: [分析并修复...]
    │
    ▼
1. programming-assistant 执行编程任务
    │
    ├── 修复 bug
    ├── 验证结果
    └── 更新 progress.txt
    │
    ▼
2. 会话结束检查
    │
    ├── 是否满足进化触发条件?
    │   ├── 是 → 调用 skill-evolution-manager
    │   │   ├── trigger_detector.py - 检测是否需要进化
    │   │   ├── extract_session_summary - 提取会话摘要
    │   │   ├── merge_evolution.py - 合并到 evolution.json
    │   │   └── smart_stitch.py - 缝合到 SKILL.md
    │   └── 自动进化完成
    │
    └── 否 → 正常结束会话
```

### 管理流程（Management Workflow）

```
用户: /skill-manager health
    │
    ▼
1. 触发 skill-manager
    │
    ├── health_check.py - 扫描所有 skill
    │   ├── 检查 SKILL.md 存在性
    │   ├── 检查 GitHub hash 过期
    │   └── 生成健康报告
    │
    ├── 报告状态
    │   ├── ✅ 健康的 skill
    │   ├── ⚠️  过期的 skill
    │   └── ❌ 无效的 skill
    │
    └── 提供建议操作
        ├── 更新过期 skill
        ├── 修复无效 skill
        └── 启用/禁用 skill
```

## 依赖关系

| 组件 | 用途 | 依赖 |
|--------|------|------|
| **github-to-skills** | 学习新技能 | 无 |
| **skill-manager** | 管理 skill 库 | 无 |
| **skill-evolution-manager** | 进化优化 | programming-assistant |
| **programming-assistant** | 执行编程任务 | github-to-skills, skill-evolution-manager |
| **evolving-agent** | 协调所有组件 | 以上全部 |

## 全局配置

配置文件位于 `config.yaml`：

```yaml
evolution:
  auto_evolve: true           # 启用自动进化
  threshold: medium             # 触发阈值: low/medium/high
  silent_mode: true            # 静默模式，不打断用户流程

skill_manager:
  auto_check_interval: 7d     # 每 7 天检查一次更新
  auto_update: false            # 是否自动更新过期 skill

learning:
  default_mode: tool            # 默认模式: tool/learn
  save_addons_to: ~/.config/opencode/skill/knowledge-addons/

logging:
  level: info                 # 日志级别: debug/info/warn/error
  file: ~/.config/evolving-agent.log
```

## 使用示例

### 示例 1: 学习新框架

```
用户: 学习这个 React 项目的最佳实践
      https://github.com/alan2207/bulletproof-react

智能体:
1. 检测到 GitHub URL，触发学习流程
2. 运行 fetch_github_info.py 获取仓库信息
3. 运行 extract_patterns.py 分析代码结构
4. 生成 bulletproof-react-knowledge addon
5. 自动附加到 programming-assistant

输出: "已学习 bulletproof-react 的最佳实践，包括:
      - Feature-Based 架构
      - React Query 状态管理
      - Zod 类型校验
      下次创建 React 项目时将自动应用这些范式。"
```

### 示例 2: 自动进化

```
用户: 帮我修复这个 API 报错

智能体:
1. 分析问题，定位到跨域配置错误
2. 修复代码，验证通过
3. 检测到这是一个值得保存的经验
4. 自动触发进化流程
5. 将 "Vite 开发服务器需要配置 proxy 解决跨域" 写入 evolution.json

用户下次遇到类似问题时，智能体会主动提示这个解决方案。
```

### 示例 3: 插件管理

```
用户: /skill-manager health

智能体:
1. 运行 health_check.py 扫描所有 skill
2. 生成健康检查报告

输出:
┌─────────────────────────────────────────────────────────┐
│               Skill 健康检查报告                         │
├─────────────────────────────────────────────────────────┤
│ 总计: 5 个 skill                                        │
│ ✅ 健康: 3                                              │
│ ⚠️  过期: 1 (yt-dlp-tool)                               │
│ ❌ 损坏: 1 (deprecated-helper)                          │
├─────────────────────────────────────────────────────────┤
│ 建议操作:                                               │
│ 1. 运行 `/skill-manager update yt-dlp-tool` 更新       │
│ 2. 运行 `/skill-manager delete deprecated-helper` 清理 │
└─────────────────────────────────────────────────────────┘
```

## 最佳实践

1. **非侵入式**：协调器不直接修改用户代码，只触发相应的 skill
2. **可观测性**：所有操作都记录日志，便于调试
3. **容错性**：单个组件失败不影响其他组件
4. **用户控制**：所有自动化功能都可以通过配置关闭或调整

## 统一知识查询 (Unified Knowledge)

协调器提供统一的知识查询接口，整合两个知识源：

1. **github-to-skills/knowledge**: 从 GitHub 仓库学习的模式
2. **programming-assistant-skill/experience**: 用户的个人经验和偏好

### 使用方式

```bash
# 根据项目自动检测并加载知识
python scripts/unified_knowledge.py --project /path/to/project

# 指定技术栈查询
python scripts/unified_knowledge.py --tech react,typescript,jest

# 查看统计信息
python scripts/unified_knowledge.py --stats

# Markdown 格式输出 (适合嵌入)
python scripts/unified_knowledge.py --project . --format markdown
```

### 输出结构

```json
{
  "detected": {"base_tech": ["javascript"], "frameworks": ["react"]},
  "github_knowledge": {"frameworks": {...}, "patterns": [...], "practices": [...]},
  "experience": {"preferences": [...], "fixes": [...], "tech_patterns": {...}},
  "combined_tips": ["[快速参考列表]"]
}
```

### 工作流程

```
项目目录
    │
    ▼
detect_project.py (自动检测技术栈)
    │
    ├── github-to-skills/knowledge/ (学习的模式)
    │   ├── frameworks/<framework>.json
    │   ├── patterns/<pattern>.json
    │   └── practices/<practice>.json
    │
    └── programming-assistant/experience/ (用户经验)
        ├── index.json (偏好/修复)
        └── tech/<tech>.json (技术特定模式)
    │
    ▼
统一输出 (combined_tips + 详细知识)
```

## 注意事项

- evolving-agent 主要作为**逻辑协调器**，实际工作由各个 skill 组件完成
- 在非自动化场景下，用户可以直接调用各个 skill 的命令
- 自动进化功能需要在 programming-assistant 中配置 `auto_evolve: true`
- 统一知识查询会合并 GitHub 学习和用户经验，提供完整的知识上下文

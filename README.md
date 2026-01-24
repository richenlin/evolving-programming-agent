# Evolving Programming Agent

**持续学习、自我进化的 AI 编程智能体**

Evolving Programming Agent 是一个模块化的 AI 编程系统。它不仅仅是一个代码生成工具，更是一个能够从 GitHub 学习最佳实践、从日常任务中积累经验、并不断优化自身能力的"成长型"智能体。

---

## 🚀 核心特性

- **🧠 统一协调大脑**: 通过 `evolving-agent` 进行意图识别和任务调度，智能处理编程、学习和管理任务。
- **🔄 自动进化闭环**: 在编程任务结束后，自动提取有价值的经验（Bug 修复、架构模式）并存入知识库。
- **📚 GitHub 学习引擎**: 主动分析 GitHub 开源项目，提取架构范式和代码规范，转化为可复用的技能。
- **⚡️ 异步知识流**: 知识检索和归纳在后台异步执行，提供流畅无阻塞的编程体验。
- **🧩 插件化架构**: 所有能力（编程、学习、管理）均为独立 Skill，支持热插拔和独立升级。

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

## 📦 安装

### Python 环境配置

本项目的 Skill 需要运行 Python 3.8+ 并安装 PyYAML 包。

**配置方法：**

```bash
# 运行安装脚本时自动为 Skill 配置虚拟环境
# 每个 skill 将拥有独立的 .venv 目录
# Python 路径自动修正，无需手动配置
```

### 快速安装

```bash
# 克隆仓库
git clone https://github.com/your-repo/evolving-programming-agent.git
cd evolving-programming-agent

# 安装所有组件 (支持 OpenCode, Claude Code, Cursor)
./install.sh --all
```

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

### 3. 从 GitHub 学习
让智能体学习优秀的开源项目：

> "学习这个仓库 https://github.com/shadcn/ui"

系统将自动提取组件设计模式，并在后续编程中复用。

### 4. 显式保存经验
虽然系统会自动进化，您也可以显式要求保存：

> "记住这个解决方案，以后遇到类似问题直接用"

## 🏗️ 架构组件

| 组件 | 目录 | 职责 |
|------|------|------|
| **evolving-agent** | `evolving-agent/` | **顶层协调器**。负责意图识别、任务调度和进化模式管理。 |
| **programming-assistant** | `programming-assistant/` | **执行引擎**。负责高质量的代码生成、修复和重构。 |
| **github-to-skills** | `github-to-skills/` | **学习引擎**。从 GitHub 仓库提取结构化知识。 |
| **skill-manager** | `skill-manager/` | **运维工具**。管理 Skill 的生命周期（更新、检查、启停）。 |
| **knowledge-base** | `knowledge-base/` | **统一知识库**。存储 7 大分类的编程知识和经验。 |

## 📖 文档

- [架构设计 (SOLUTION.md)](docs/SOLUTION.md): 详细的系统架构和设计理念。

## 🤝 贡献

欢迎提交 Pull Request 或 Issue 来帮助改进这个项目！

## 📄 许可证

MIT License

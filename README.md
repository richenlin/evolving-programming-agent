# Evolving Programming Agent

**持续学习、自我进化的 AI 编程智能体**

Evolving Programming Agent 是一个模块化的 AI 编程系统。它不仅仅是一个代码生成工具，更是一个能够从 GitHub 学习最佳实践、从日常任务中积累经验、并不断优化自身能力的"成长型"智能体。

---

## 🚀 核心特性

- **🧠 统一协调大脑**: 通过 `evolving-agent` 进行意图识别和任务调度，智能处理编程、学习和管理任务。
- **🔄 自动进化闭环**: 在编程任务结束后，自动提取有价值的经验（Bug 修复、架构模式）并存入知识库。
- **📚 GitHub 学习引擎**: 主动分析 GitHub 开源项目，提取架构范式和代码规范，转化为可复用的技能。
- **⚡️ 异步知识流**: 知识检索和归纳在后台异步执行，提供流畅无阻塞的编程体验。
- **🧩 插件化架构**: 所有能力（编程、学习、管理）均为独立 Skill，支持独立升级。

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
./scripts/install.sh --all
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
| **evolving-agent** | `evolving-agent/` | **核心 Skill**。包含协调器、编程助手、GitHub 学习和知识库模块。 |
| **skill-manager** | `skill-manager/` | **独立 Skill**。管理 Skill 的生命周期（更新、检查、启停）。 |

### evolving-agent 内部模块

| 模块 | 位置 | 职责 |
|------|------|------|
| programming-assistant | `modules/programming-assistant/` | 代码生成、修复和重构 |
| github-to-skills | `modules/github-to-skills/` | 从 GitHub 提取知识 |
| knowledge-base | `modules/knowledge-base/` | 统一知识库管理 |

### 统一命令行入口

所有功能通过 `run.py` 统一调用：

```bash
# 进化模式控制
python run.py mode --status           # 查看状态
python run.py mode --init             # 初始化
python run.py mode --on               # 开启
python run.py mode --off              # 关闭

# 知识库操作
python run.py knowledge query --stats
python run.py knowledge query --trigger "react,hooks"
python run.py knowledge store --category experience --name "xxx"
python run.py knowledge summarize --auto-store
python run.py knowledge trigger --input "修复CORS问题"

# GitHub 学习
python run.py github fetch <url>
python run.py github extract --input repo_info.json
python run.py github store --input extracted.json

# 项目检测
python run.py project detect .
python run.py project store --tech react --pattern "xxx"
python run.py project query --project .

# 环境信息
python run.py info
python run.py info --json
```

## 📖 文档

- [架构设计 (SOLUTION.md)](docs/SOLUTION.md): 详细的系统架构和设计理念。

## 🤝 贡献

欢迎提交 Pull Request 或 Issue 来帮助改进这个项目！

## 📄 许可证

MIT License

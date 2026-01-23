# Evolving Programming Agent - 持续学习进化编程智能体

持续学习进化的编程智能体 - 由 AI Skills 驱动的自适应编程助手。

## 项目愿景

打造一个能够**持续学习、自我进化**的编程智能体，通过组合现有的四个 skill 组件，构建一个具备以下能力的 AI 编程助手：

1. **自主学习**：从 GitHub 仓库中学习新的编程技能和最佳实践
2. **持续进化**：从每次编程任务中提取经验，不断优化自身能力
3. **灵活管理**：以插件形式管理技能库，支持热启用/禁用
4. **跨平台支持**：兼容 Claude Code、OpenCode、Cursor 三大主流 AI 编程环境

---

## Skills 组件

### 1. github-to-skills (技术学习器)

**功能**：将 GitHub 仓库转换为可学习的 AI skills

**双模式**：
- **工具模式**：将 CLI 工具包装为可调用的 skill
- **学习模式**：从优秀开源项目中提取编程范式和最佳实践

**输出**：knowledge-addon 格式的 Markdown 文件，包含：
- 项目架构模式（Feature-Based, Component-Based, MVC 等）
- 代码规范（TypeScript, Prettier, ESLint 等）
- 技术栈（React, Vue, Django, Flask 等）
- 最佳实践（测试覆盖, CI/CD, 文档说明等）

### 2. skill-manager (插件管理器)

**功能**：管理 skill 的完整生命周期

**核心能力**：
- ✅ **审计**：扫描本地 skills 目录
- ✅ **健康检查**：检测过期和无效的 skill
- ✅ **启用/禁用**：临时启用或禁用 skill（不删除）
- ✅ **更新检查**：对比本地和远程 GitHub hash
- ✅ **列表**：列出所有已安装的 skill
- ✅ **删除**：永久移除不需要的 skill

### 3. skill-evolution-manager (进化器)

**功能**：从对话中提取经验并持久化

**进化流程**：
1. **触发检测**：自动检测是否需要进化（复杂 bug 修复、用户反馈等）
2. **会话摘要**：提取修复尝试次数、完成状态、用户反馈
3. **数据合并**：增量合并新的经验到 `evolution.json`
4. **智能缝合**：将经验数据渲染到 `SKILL.md` 的独立章节

**支持的数据类型**：
- `preferences`：用户偏好设置
- `fixes`：已知问题和解决方案
- `patterns`：编程范式（按技术分类）
- `context_triggers`：场景触发的指令

### 4. programming-assistant (编程执行器)

**功能**：全栈开发和架构设计助手

**核心能力**：
- **完整模式**：新建项目/功能开发（系统规划、任务拆解）
- **简化模式**：问题修复/代码重构/代码审查
- **咨询模式**：技术咨询和建议
- **自动进化**：会话结束时自动调用进化流程

**新增功能**：
- ✅ `auto_evolve` 配置：启用/禁用自动进化
- ✅ `evolve_threshold`：触发阈值设置
- ✅ `silent_mode`：静默模式不打断用户流程

---

## 安装

### 快速安装（推荐）

```bash
# 安装所有组件到所有平台
./install.sh --all --with-mcp
```

### 选择性安装

```bash
# 仅安装到 OpenCode
./install.sh --opencode

# 仅安装到 Claude Code
./install.sh --claude-code

# 仅安装到 Cursor
./install.sh --cursor

# 指定要安装的 skill
./install.sh --skills "github-to-skills,skill-manager"
```

### 卸载

```bash
# 卸载所有组件
./uninstall.sh --all

# 选择性卸载
./uninstall.sh --opencode --skills "github-to-skills"
```

---

## 使用示例

### 示例 1：学习新框架

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

### 示例 2：自动进化

```
用户: 帮我修复这个 API 报错

智能体:
1. 分析问题，定位到跨域配置错误
2. 修复代码，验证通过
3. 检测到这是一个值得保存的经验:
   - 解决方案非显而易见
   - 涉及特定环境配置
4. 自动触发 /evolve
5. 将 "Vite 开发服务器需要配置 proxy 解决跨域" 写入 evolution.json

用户下次遇到类似问题时，智能体会主动提示这个解决方案。
```

### 示例 3：插件管理

```
用户: /skill-manager health

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

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Evolving Agent (协调层)                              │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌──────────────┐  │
│  │ 学习触发器      │  │ 进化触发器     │  │ 健康检查器      │  │ 会话管理器     │  │
│  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘  └──────┬───────┘  │
└──────────┼──────────────────┼──────────────────┼─────────────────┼──────────┘
           │                  │                  │                 │              
           ▼                  ▼                  ▼                 ▼                
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ 
│ github-to-skills │ │skill-evolution-  │ │  skill-manager   │ │ programming-     │ 
│ (技术学习器)       │ │manager (进化器)   │ │  (插件管理器)     │ │ assistant (执行器)│ 
│                  │ │                  │ │                  │ │                  │ 
│ ・工具模式         │ │ ・经验提取        │ │ ・启用/禁用        │ │ ・完整模式         │ 
│ ・学习模式         │ │ ・JSON持久化      │ │ ・健康检查         │ │ ・简化模式        │ 
│ ・范式提取         │ │ ・智能缝合        │ │ ・自动更新         │ │ ・自动进化         │ 
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘ 
           │                  │                  │                 │                 
           └──────────────────┴──────────────────┴─────────────────┴
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
             ┌───────────┐     ┌───────────┐     ┌───────────┐
             │ OpenCode  │     │Claude Code│     │  Cursor   │
             └───────────┘     └───────────┘     └───────────┘
```

---

## 文件结构

```
skills-evolution/
├── README.md                          # 项目总览（本文件）
├── SOLUTION.md                        # 完整设计文档
├── TASK.md                            # MVP 构建任务清单
├── install.sh                         # 统一安装器
├── uninstall.sh                       # 统一卸载器
│
├── github-to-skills/                 # 技术学习器
│   ├── SKILL.md
│   └── scripts/
│       ├── fetch_github_info.py       # 获取仓库信息（含文件树）
│       ├── create_github_skill.py
│       └── extract_patterns.py        # 提取编程范式 [新增]
│
├── skill-manager/                   # 插件管理器
│   ├── SKILL.md
│   └── scripts/
│       ├── scan_and_check.py
│       ├── update_helper.py
│       ├── list_skills.py
│       ├── delete_skill.py
│       ├── health_check.py            # 健康检查 [新增]
│       ├── toggle_skill.py            # 启用/禁用 [新增]
│       └── utils/
│           ├── __init__.py
│           └── frontmatter_parser.py # YAML 解析器 [新增]
│
├── skill-evolution-manager/          # 进化器
│   ├── SKILL.md
│   └── scripts/
│       ├── merge_evolution.py         # 合并进化数据 [扩展]
│       ├── smart_stitch.py            # 智能缝合 [扩展]
│       ├── align_all.py
│       └── trigger_detector.py       # 触发检测器 [新增]
│
├── programming-assistant-skill/       # 编程执行器
│   ├── SKILL.md                     # 含 evolution 配置 [更新]
│   ├── install.sh
│   ├── uninstall.sh
│   └── templates/
│       ├── progress.txt
│       └── feature_list.json
│
├── evolving-agent/                    # 协调器 [新增]
│   ├── SKILL.md                     # 协调逻辑
│   ├── config.yaml                  # 全局配置
│   ├── __init__.py
│   └── scripts/                    # 预留给协调脚本
│
└── tests/                             # 端到端测试 [新增]
    ├── e2e_learning.sh              # 学习流程测试
    └── e2e_plugin_manager.sh        # 插件管理测试
```

---

## 依赖要求

- Python 3.8+
- Git (用于 GitHub 仓库操作)
- Bash 4.0+ (用于安装脚本)
- PyYAML (可选，用于 YAML frontmatter 解析)

---

## 开发和测试

### 运行测试

```bash
# 学习流程测试
./tests/e2e_learning.sh

# 插件管理测试
./tests/e2e_plugin_manager.sh
```

### 构建步骤

详见 `TASK.md` 中的 28 个任务，按 6 个阶段组织：
- **Phase 1**: 插件管理系统 (9 tasks)
- **Phase 2**: GitHub 学习器 (6 tasks)
- **Phase 3**: 自动进化机制 (5 tasks)
- **Phase 4**: 跨平台支持 (4 tasks)
- **Phase 5**: 协调器 (3 tasks)
- **Phase 6**: 集成测试 (3 tasks)

---

## 使用场景

### 场景 1：学习新框架

智能体自动从 GitHub 仓库中提取：
- 项目架构模式
- 代码规范和最佳实践
- 技术栈和工具链
- 测试和部署策略

### 场景 2：自动进化

智能体无需人工干预：
- 检测复杂问题解决
- 提取用户反馈
- 保存经验到 evolution.json
- 自动更新 SKILL.md

### 场景 3：智能管理

自动监控 skill 状态：
- 检测过期版本
- 识别无效配置
- 提醒用户更新
- 支持热启用/禁用

---

## 贡献

欢迎贡献！请随时：
- 报告问题
- 提交 Pull Requests
- 分享你的自定义 skills

---

## 许可证

MIT License - 详见 LICENSE 文件

---

## 作者

**Khazix**

如果你发现这个项目有用，请考虑给这个仓库一个 ⭐ Star！

---

## 相关项目

- [OpenCode](https://opencode.ai)
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
- [Cursor](https://cursor.sh)
- [Khazix-Skills](https://github.com/KKKKhazix/Khazix-Skills)

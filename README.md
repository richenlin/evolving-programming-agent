# Evolving Programming Agent - 持续学习进化编程智能体

持续学习进化的编程智能体 - 由 AI Skills 驱动的自适应编程助手。

## 项目愿景

打造一个能够**持续学习、自我进化**的编程智能体，通过组合现有的核心组件，构建一个具备以下能力的 AI 编程助手：

1. **自主学习**：从 GitHub 仓库中学习新的编程技能和最佳实践
2. **持续进化**：从每次编程任务中提取经验，不断优化自身能力
3. **灵活管理**：以插件形式管理技能库，支持热启用/禁用
4. **跨平台支持**：兼容 Claude Code、OpenCode、Cursor 三大主流 AI 编程环境
5. **统一知识库**：7大分类的知识存储系统，支持智能触发加载
6. **异步子会话**：知识检索和归纳异步执行，不阻塞主任务

## 核心架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Evolving Programming Agent                          │
├─────────────────────────────────────────────────────────────────────────┤
│                      ┌─────────────┐                                    │
│                      │协调层        │                                    │
│                      └──────┬──────┘                                    │
│                             │                                           │
│         ┌───────────────────┼───────────────────┐────────────┐          │
│         │                   │                   │            │          │
│         ▼                   ▼                   ▼            ▼          │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐     │
│  │ 技术学习  │      │ 知识库     │     │ 进化管理器 │      │ 插件管理器 │     │
│  └─────┬────┘      └─────┬────┘      └─────┬────┘      └─────┬────┘     │
│        │                 │                 │                 │          │
│        ▼                 ▼                 ▼                 ▼          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │              统一知识库                                            │   │
│  │  - experience (经验)  - tech-stack (技术栈)                        │   │
│  │  - scenario (场景)    - problem (问题解决)                         │    │
│  │  - testing (测试)      - pattern (编程范式)                        │    │
│  │  - skill (技能)                                                   │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│        │                 │                 │                 │           │
│        ▼                 ▼                 ▼                 ▼           │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │              异步子会话层                                          │    │
│  │  - knowledge-retrieval (检索)                                     │    │
│  │  - knowledge-summarize (归纳)                                     │    │
│  └──────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────┘
```

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

**集成**：学习结果自动存储到统一知识库

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

**功能**：从对话中提取经验并持久化到统一知识库

**进化流程**：
1. **触发检测**：自动检测是否需要进化（复杂 bug 修复、用户反馈等）
2. **会话摘要**：提取修复尝试次数、完成状态、用户反馈
3. **异步归纳**：启动子会话分析会话内容
4. **智能分类**：自动分类到 7 大知识分类
5. **知识存储**：存储到 knowledge-base/

### 4. programming-assistant (编程执行器)

**功能**：全栈开发和架构设计助手

**核心能力**：
- **完整模式**：新建项目/功能开发（系统规划、任务拆解）
- **简化模式**：问题修复/代码重构/代码审查
- **咨询模式**：技术咨询和建议
- **异步知识检索**：任务开始时自动触发知识加载
- **异步知识归纳**：任务结束时自动归纳经验

**新增功能**：
- ✅ `knowledge_enabled: true` - 启用知识辅助
- ✅ 异步子会话支持知识检索和归纳
- ✅ 根据用户输入和项目自动触发相关知识

### 5. knowledge-base (统一知识库) [新增]

**功能**：7 大分类的知识存储、检索、触发系统

**知识分类**：
- **experience** - 经验积累
- **tech-stack** - 技术栈知识
- **scenario** - 场景知识
- **problem** - 问题解决
- **testing** - 测试知识
- **pattern** - 编程范式
- **skill** - 编程技能

**核心工具**：
- `knowledge_store.py` - 存储工具（支持 7 类便捷方法）
- `knowledge_query.py` - 查询工具（按触发关键字、分类、全文）
- `knowledge_trigger.py` - 触发检测器（自动检测项目技术栈、场景、问题）
- `knowledge_summarizer.py` - 归纳总结器（分析会话提取知识）

**异步子代理**：
- `agents/retrieval-agent.md` - 知识检索子代理
- `agents/summarize-agent.md` - 知识归纳子代理

**触发机制**：
- 项目检测（package.json, go.mod, pom.xml 等）
- 关键字匹配
- 场景推断（创建→scenario, 修复→problem, 测试→testing）
- 问题症状识别（cors, memory, timeout 等）

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

### 示例 1：学习新框架并存储到知识库

```
用户: 学习这个 React 项目的最佳实践
       https://github.com/alan2207/bulletproof-react

智能体:
1. 检测到 GitHub URL，触发学习流程
2. 运行 fetch_github_info.py 获取仓库信息
3. 运行 extract_patterns.py 分析代码结构
4. 自动存储到 knowledge-base:
   - tech-stacks/react.json (技术栈知识)
   - patterns/feature-based-architecture.json (架构模式)
   - experiences/ (最佳实践)

输出: "已学习 bulletproof-react 的最佳实践，包括:
       - Feature-Based 架构
       - React Query 状态管理
       - Zod 类型校验
       存储到统一知识库，下次创建 React 项目时自动触发加载。"
```

### 示例 2：自动触发知识辅助编程

```
用户: 帮我用 Koatty 创建一个 gRPC 服务

智能体:
1. 异步启动知识检索子会话:
   python knowledge-base/scripts/knowledge_trigger.py \
     --input "Koatty gRPC 服务" \
     --format context > .knowledge-context.md

2. 主任务继续执行，不等待检索完成

3. 读取 .knowledge-context.md 获取知识:
   - Koatty 多协议服务配置
   - 创建 Koatty 企业级应用场景
   - IOC 依赖注入模式

4. 基于知识提供具体指导:
   - 使用 koatty_cli 创建项目
   - 配置 protocol: ["grpc"]
   - 创建 @GrpcController 控制器
```

### 示例 3：问题解决后自动归纳

```
用户: 帮我修复这个 CORS 跨域问题

智能体:
1. 异步启动知识检索（不阻塞）
2. 检测到 .knowledge-context.md 有 CORS 知识
3. 基于知识提供解决方案: Vite 代理配置
4. 验证修复成功

[会话结束]
智能体:
1. 检测到进化触发条件（非标准解决方案）
2. 异步启动知识归纳子会话
3. 分析会话内容并存储:
   - problem: CORS 跨域问题
   - experience: Vite 代理配置
4. 用户下次遇到 CORS 问题时自动提示此解决方案
```

### 示例 4：查询知识库

```
用户: 查询 React 相关的最佳实践

智能体:
1. 运行查询命令:
   python knowledge-base/scripts/knowledge_query.py --trigger react --format markdown

2. 返回相关知识:
   ### React 技术栈
   - **最佳实践**: 使用函数组件和 Hooks
   - **最佳实践**: 状态提升避免 prop drilling
   - **坑**: useEffect 依赖数组要完整

   ### 相关经验
   - Vite 开发服务器代理配置
   - Feature-Based 架构
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

### 统一知识管理

提供统一的命令管理所有知识：

```bash
# 查询知识库
python knowledge-base/scripts/knowledge_query.py --stats
python knowledge-base/scripts/knowledge_query.py --trigger react,hooks
python knowledge-base/scripts/knowledge_query.py --category problem

# 触发检索
python knowledge-base/scripts/knowledge_trigger.py --input "CORS 跨域" --format context

# 归纳知识
echo "会话内容" | python knowledge-base/scripts/knowledge_summarizer.py --auto-store

# 更新知识有效性
python knowledge-base/scripts/knowledge_summarizer.py --feedback positive --entry-id "entry-id"
```

---

## 贡献

欢迎贡献！请随时：
- 报告问题
- 提交 Pull Requests
- 分享你的自定义 skills

---

## 许可证

MIT License - 详见 LICENSE 文件

如果你发现这个项目有用，请考虑给这个仓库一个 ⭐ Star！

---

## 相关项目

- [OpenCode](https://opencode.ai)
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
- [Cursor](https://cursor.sh)
- [Khazix-Skills](https://github.com/KKKKhazix/Khazix-Skills)

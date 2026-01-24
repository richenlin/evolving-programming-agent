---
name: skill-evolution-manager
description: Skill 进化管理器。当用户说"开发"、"实现"、"创建"、"添加"、"修复"、"报错"、"重构"、"优化"、"review"、"评审"、"继续开发"、"怎么实现"、"为什么"、"记住这个"、"保存经验"、"存储这个方案"、"复盘"、"总结经验"、"evolve"、"/evolve"、"学到了什么"、"记录这次的教训"、"学习这个仓库"、"从 GitHub 学习"、"提取最佳实践"、"分析GitHub"、"分析开源项目"时使用。支持经验提取、渐进式存储、按技术栈/上下文分类、按需加载、GitHub 仓库学习。
license: MIT
metadata:
  triggers: ["开发", "实现", "创建", "添加", "修复", "报错", "重构", "优化", "review", "评审", "继续开发", "怎么实现", "为什么", "记住这个", "保存经验", "存储这个方案", "复盘", "总结经验", "evolve", "/evolve", "学到了什么", "记录这次的教训", "学习这个仓库", "从 GitHub 学习", "提取最佳实践", "分析GitHub", "分析开源项目"]
---

# Skill Evolution Manager

AI 技能系统的"进化中枢"，作为统一入口协调编程助手、知识进化和 GitHub 仓库学习流程。

## 核心职责

1. **协调器**: 统一入口，协调 programming-assistant、知识进化和 GitHub 仓库学习
2. **智能调度**: 使用 sequential-thinking 进行深度意图分析和智能决策
3. **自动识别**: 识别用户意图（编程任务 / 知识归纳 / GitHub 学习）
4. **进化模式**: 管理 session 级的持续知识提取状态
5. **经验提取**: 将用户反馈转化为结构化数据
6. **渐进式存储**: 按技术栈/上下文分类存储经验
7. **仓库学习**: 从 GitHub 仓库自动提取编程知识并集成到知识库

## 智能调度流程 (Sequential-Thinking)

当此 skill 被触发时，使用 **sequential-thinking** 进行深度分析和智能调度：

### 思维序列

```
Step 1: 关键词检测
  - 扫描用户输入
  - 识别触发词类型（编程 / 知识归纳 / 命令）

Step 2: 意图识别
  - 判断用户意图类型
  - 分析上下文和对话历史

Step 3: 状态检查
  - 检查进化模式是否已激活
  - 检查 programming-assistant 是否已加载

Step 4: 决策制定
  - 根据意图和状态制定调度策略
  - 考虑任务复杂度和上下文

Step 5: 执行调度
  - 执行初始化（如果需要）
  - 加载相应的 skill 或流程

Step 6: 反馈输出
  - 向用户反馈执行结果
  - 提供后续建议
```

### 调度决策树

```
用户输入触发
    ↓
[Sequential-Thinking 分析]
    ↓
判断意图类型
    ├─ 编程任务
    │   ↓
    │   检查进化模式
    │   ├─ 未激活 → 执行 --init + 加载 programming-assistant
    │   └─ 已激活 → 直接加载 programming-assistant
    │       ↓
    │   传递上下文到 programming-assistant
    │
    ├─ 知识归纳请求
    │   ↓
    │   执行 trigger_detector.py
    │   → 提取知识 → 存储到知识库
    │
    ├─ GitHub 仓库学习
    │   ↓
    │   自动激活 github-to-skills
    │   ├─ 获取仓库信息
    │   ├─ 分析提取知识
    │   └─ 存储到 knowledge-base
    │       ↓
    │   更新索引 → 知识可供后续编程使用
    │
    ├─ "/evolve" 命令
    │   ↓
    │   执行 --init（完整初始化）
    │   → 输出引导提示
    │
    └─ 自动触发条件
        ↓
        复杂问题修复成功
        → 静默执行知识归纳
```

### 使用 Sequential-Thinking 示例

#### 示例 1：编程任务

**用户输入**："帮我实现一个用户认证功能"

**Sequential-Thinking 分析**：
```
Thought 1: 检测关键词 - "实现" 是编程任务关键词
Thought 2: 识别意图 - 这是一个编程任务，需要加载 programming-assistant
Thought 3: 检查状态 - 进化模式未激活，需要初始化
Thought 4: 制定决策 - 执行 toggle_mode.py --init，然后加载 programming-assistant
Thought 5: 传递上下文 - 场景：功能开发，模式：full-mode
Thought 6: 执行调度 - 初始化协调器，加载编程助手
```

**执行结果**：
- ✅ 进化模式已激活
- ✅ programming-assistant 已加载
- ✅ 进入开发流程

#### 示例 2：知识归纳请求

**用户输入**："记住这个解决方案"

**Sequential-Thinking 分析**：
```
Thought 1: 检测关键词 - "记住这个" 是知识归纳关键词
Thought 2: 识别意图 - 用户希望将当前解决方案保存到知识库
Thought 3: 分析上下文 - 会话中包含一个技术问题的解决方案
Thought 4: 制定决策 - 执行 trigger_detector.py 扫描会话
Thought 5: 存储知识 - 提取有价值信息，存储到统一知识库
Thought 6: 反馈输出 - 向用户确认知识已保存
```

**执行结果**：
- ✅ 知识已提取
- ✅ 已存储到知识库
- ✅ 向用户反馈成功信息

#### 示例 3：手动启动

**用户输入**："/evolve"

**Sequential-Thinking 分析**：
```
Thought 1: 检测命令 - "/evolve" 是特殊命令
Thought 2: 识别意图 - 用户显式请求启动完整流程
Thought 3: 检查状态 - 进化模式未激活
Thought 4: 制定决策 - 执行完整初始化（--init），输出引导提示
Thought 5: 引导用户 - 提示下一步可以输入编程任务
Thought 6: 等待输入 - 保持协调器激活状态
```

**执行结果**：
- ✅ 协调器已启动
- ✅ 进化模式已激活
- ✅ 输出引导提示

#### 示例 4：GitHub 仓库学习

**用户输入**："学习这个仓库 https://github.com/facebook/react"

**Sequential-Thinking 分析**：
```
Thought 1: 检测关键词 - "学习这个仓库"、"GitHub"
Thought 2: 识别意图 - GitHub 仓库学习请求
Thought 3: 分析上下文 - 用户提供了一个 GitHub URL
Thought 4: 制定决策 - 自动激活 github-to-skills
Thought 5: 执行调度
  1. 获取仓库信息（fetch_github_info.py）
  2. 分析提取知识（extract_knowledge.py）
  3. 存储到 knowledge-base（store_to_knowledge.py）
  4. 更新索引
Thought 6: 反馈输出 - 告知用户知识已提取并可供后续使用
```

**执行结果**：
- ✅ GitHub 仓库信息已获取
- ✅ 知识已提取（技术栈、架构、最佳实践）
- ✅ 已存储到 knowledge-base
- ✅ 索引已更新
- ✅ 后续编程任务可自动使用这些知识



## 触发流程

### 流程 1：编程任务（完整协调器流程）

**触发条件**：
- 用户输入包含编程关键词
- 意图判断为编程任务

**执行流程**：
```
1. 启动协调器（skill-evolution-manager）
   ↓
2. 开启进化模式（创建标记文件）
   ↓
3. 自动加载 programming-assistant
   ↓
4. 进入编程 → 知识进化迭代循环
   - 执行编程任务
   - 每次响应结束前检查进化模式
   - 自动提取有价值经验
```

**实现方式**：
```bash
# 执行完整初始化
python scripts/toggle_mode.py --init

# 然后触发 programming-assistant
# 通过 @load 或直接调用 skill 内容
```

**输出**：
- 首次激活：输出引导提示
- 已激活：静默模式

### 流程 2：知识归纳请求

**触发条件**：
- 用户输入 "记住这个"、"保存经验" 等关键词
- 复杂问题修复成功后自动触发
- 用户显式请求知识归纳

**执行流程**：
```
1. 提取会话上下文
   ↓
2. 运行触发检测（trigger_detector.py）
   ↓
3. 异步归纳知识
   ↓
4. 存储到统一知识库
```

**实现方式**：
```bash
# 异步启动知识归纳子会话
Task(
    subagent_type="general",
    description="Knowledge summarization",
    prompt="""
    分析以下会话内容并提取知识:

    {会话摘要}

    执行:
    echo "{content}" | python knowledge-base/scripts/knowledge_summarizer.py \
      --auto-store \
      --session-id "{session_id}"
    """
)
```

### 流程 3：GitHub 仓库学习

**触发条件**：
- 用户输入包含 GitHub 仓库学习关键词
- 提供了 GitHub URL 或仓库名

**执行流程**：
```
1. 自动激活 github-to-skills
   ↓
2. 获取仓库信息（fetch_github_info.py）
   ↓
3. 分析提取知识（extract_knowledge.py）
   ↓
4. 存储到 knowledge-base（store_to_knowledge.py）
   ↓
5. 更新索引
   ↓
6. 知识可供后续编程任务使用
```

**实现方式**：
```bash
# 1. 获取仓库信息
python github-to-skills/scripts/fetch_github_info.py <github_url>

# 2. 提取知识
python github-to-skills/scripts/extract_knowledge.py --input <repo_info.json>

# 3. 存储到知识库
python github-to-skills/scripts/store_to_knowledge.py --input <extracted.json>

# 4. 更新索引（自动）
```

**提取内容**：
- **技术栈知识**：框架、库、版本、配置方式
- **架构模式**：目录结构、分层设计、模块划分
- **最佳实践**：代码规范、命名约定、注释风格
- **常见问题**：README 中的 FAQ、已知问题

**知识闭环**：
```
GitHub 仓库学习
    ↓
存储到 knowledge-base/
    ↓
更新触发索引
    ↓
后续编程任务自动使用这些知识
    ↓
编程 + 知识进化完整闭环
```

## 协调器工作模式

### 自动触发关键词（编程任务）

| 触发词 | 示例 | 触发流程 |
|--------|------|---------|
| "开发" | "帮我开发一个登录功能" | 完整协调器流程 |
| "实现" | "实现一个用户认证模块" | 完整协调器流程 |
| "创建" | "创建一个 REST API" | 完整协调器流程 |
| "添加" | "添加一个搜索功能" | 完整协调器流程 |
| "修复" | "修复这个 bug" | 完整协调器流程 |
| "报错" | "报错了，帮我看看" | 完整协调器流程 |
| "重构" | "重构这段代码" | 完整协调器流程 |
| "优化" | "优化这个查询" | 完整协调器流程 |
| "review" | "review 这段代码" | 完整协调器流程 |
| "评审" | "评审这个 PR" | 完整协调器流程 |
| "继续开发" | "继续开发上次的任务" | 完整协调器流程 |
| "怎么实现" | "怎么实现 WebSocket" | 完整协调器流程 |
| "为什么" | "为什么这个报错" | 完整协调器流程 |

### 知识归纳关键词

| 触发词 | 示例 | 触发流程 |
|--------|------|---------|
| "记住这个" | "记住这个解决方案" | 知识归纳流程 |
| "保存经验" | "保存这个经验" | 知识归纳流程 |
| "存储这个方案" | "存储这个方案" | 知识归纳流程 |
| "复盘" | "复盘一下这次开发" | 知识归纳流程 |
| "总结经验" | "总结这次的经验" | 知识归纳流程 |
| "evolve" | "evolve 这个解决方案" | 知识归纳流程 |
| "/evolve" | "/evolve" | 特殊：完整初始化 |
| "学到了什么" | "学到了什么" | 知识归纳流程 |
| "记录这次的教训" | "记录这次的教训" | 知识归纳流程 |

### GitHub 仓库学习关键词

| 触发词 | 示例 | 触发流程 |
|--------|------|---------|
| "学习这个仓库" | "学习这个仓库 https://github.com/facebook/react" | GitHub 仓库学习流程 |
| "从 GitHub 学习" | "从 GitHub 学习这个项目" | GitHub 仓库学习流程 |
| "提取这个项目的最佳实践" | "提取这个项目的最佳实践" | GitHub 仓库学习流程 |
| "把这个仓库的经验存起来" | "把这个仓库的经验存起来" | GitHub 仓库学习流程 |
| "分析这个开源项目" | "分析这个开源项目的架构" | GitHub 仓库学习流程 |

### 特殊触发：/evolve

`/evolve` 作为手动触发命令，行为特殊：

- 如果用户明确输入 `/evolve` → 执行完整初始化（包括输出引导提示）
- 如果是编程任务或知识归纳请求 → 按正常流程处理

## 进化模式控制

| 命令 | 说明 |
|------|------|
| `python scripts/toggle_mode.py --init` | 完整初始化：启动协调器 + 开启进化模式 |
| `python scripts/toggle_mode.py --on` | 仅开启进化模式 |
| `python scripts/toggle_mode.py --off` | 关闭进化模式 |
| `python scripts/toggle_mode.py --toggle` | 切换进化模式状态 |
| `python scripts/toggle_mode.py --status` | 查看当前状态 |

**工作原理**：
1. 执行 `--init` 或 `--on` 创建标记文件：`.opencode/.evolution_mode_active`
2. `programming-assistant` 在每次响应结束前检测该文件
3. 如果文件存在，自动运行触发检测（降低触发阈值）
4. 提取的经验异步存储到知识库
5. 无需用户反复输入 `/evolve`

**优势**：
- ✅ 单次触发，整个 session 持续生效
- ✅ 基于文件系统，不依赖 LLM 上下文记忆
- ✅ 可随时关闭，不影响正常对话
- ✅ 静默扫描，仅在发现有价值经验时报告

## 工作流

### 1. 经验提取

扫描上下文 → 识别经验类型 → 分类存储

### 2. 存储命令

```bash
# 存储偏好
python scripts/store_experience.py --preference "偏好"

# 存储修复方案
python scripts/store_experience.py --fix "修复方案"

# 存储技术模式
python scripts/store_experience.py --tech <tech> --pattern "模式"

# 存储上下文触发
python scripts/store_experience.py --context <ctx> --instruction "指令"
```

### 3. 查询命令

```bash
python scripts/query_experience.py --tech react
python scripts/query_experience.py --context when_testing
python scripts/query_experience.py --search "关键词"
```

## 存储结构

```
experience/
├── index.json       # 索引摘要
├── tech/            # 按技术栈分类
│   ├── react.json
│   └── python.json
└── contexts/        # 按上下文分类
    └── when_testing.json
```

## 脚本

| 脚本 | 用途 |
|------|------|
| `merge_evolution.py` | 合并旧格式数据 |
| `smart_stitch.py` | 迁移到渐进式结构 |
| `trigger_detector.py` | 检测进化触发条件 |
| `align_all.py` | 批量对齐所有 Skill |

## 统一知识库集成 (新增)

### 进化时同步到统一知识库

当检测到进化触发时，除了更新本地 experience/ 外，还应同步到统一知识库：

```bash
# 分析会话内容并存储到统一知识库
cat session_content.txt | python knowledge-base/scripts/knowledge_summarizer.py \
  --auto-store \
  --session-id "{session_id}"
```

### 知识分类映射

| 本地经验类型 | 统一知识库分类 |
|--------------|----------------|
| preference | experience |
| fix | problem |
| tech pattern | tech-stack |
| context trigger | scenario |

### 工作流程

```
进化触发
    │
    ├── 本地存储 (experience/)
    │
    └── 同步到统一知识库 (knowledge-base/)
        │
        ├── 自动分类
        ├── 生成触发关键字
        └── 更新索引
```

## Sequential-Thinking 实施指南

### 基本用法

在协调器被触发时，使用 `sequential-thinking` 进行深度分析：

```python
# 意图分析序列
thought_sequence = [
    {
        "thought": "Step 1: 检测用户输入中的关键词",
        "next_thought_needed": True
    },
    {
        "thought": "Step 2: 识别意图类型（编程任务 / 知识归纳 / 手动启动）",
        "next_thought_needed": True
    },
    {
        "thought": "Step 3: 分析会话上下文和历史对话",
        "next_thought_needed": True
    },
    {
        "thought": "Step 4: 判断进化模式状态（已激活 / 未激活）",
        "next_thought_needed": True
    },
    {
        "thought": "Step 5: 制定调度决策（加载哪个 skill / 执行哪个流程）",
        "next_thought_needed": True
    },
    {
        "thought": "Step 6: 执行调度并向用户反馈结果",
        "next_thought_needed": False
    }
]
```

### 决策逻辑示例

#### 场景 1：新编程任务

**Input**: "帮我实现一个用户登录功能"

**Thinking Process**:
```
Thought 1: 检测到关键词 "实现"，属于编程任务类别
Thought 2: 识别意图为编程任务，需要加载 programming-assistant
Thought 3: 分析上下文 - 这是一个新功能开发请求
Thought 4: 检查进化模式状态 - 未激活
Thought 5: 决策 - 执行 toggle_mode.py --init 启动协调器和进化模式
Thought 6: 执行调度 - 加载 programming-assistant，传递上下文：功能开发
```

**Action**:
```bash
python scripts/toggle_mode.py --init
# 然后加载 programming-assistant 的 full-mode 模块
```

#### 场景 2：连续编程任务

**Input**: "再添加一个用户注册功能"

**Thinking Process**:
```
Thought 1: 检测到关键词 "添加"，属于编程任务类别
Thought 2: 识别意图为编程任务，需要加载 programming-assistant
Thought 3: 分析上下文 - 这是同一项目的连续开发
Thought 4: 检查进化模式状态 - 已激活
Thought 5: 决策 - 无需再次初始化，直接加载 programming-assistant
Thought 6: 执行调度 - 加载 programming-assistant，传递上下文：功能开发（连续）
```

**Action**:
```bash
# 直接加载 programming-assistant，不执行初始化
```

#### 场景 3：知识归纳请求

**Input**: "记住这个 CORS 跨域问题的解决方案"

**Thinking Process**:
```
Thought 1: 检测到关键词 "记住"，属于知识归纳类别
Thought 2: 识别意图为知识归纳请求
Thought 3: 分析上下文 - 会话中刚解决了 CORS 跨域问题
Thought 4: 检查进化模式状态 - 已激活
Thought 5: 决策 - 执行 trigger_detector.py 扫描会话内容
Thought 6: 执行调度 - 提取知识并存储到统一知识库
```

**Action**:
```bash
python scripts/trigger_detector.py --context <会话内容>
# 然后调用 knowledge_summarizer.py 存储知识
```

### 最佳实践

#### 1. 意图识别优先级

```
优先级 1: 显式命令
  - "/evolve" → 立即执行完整初始化

优先级 2: 知识归纳请求
  - "记住这个"、"保存经验" 等 → 执行知识归纳

优先级 3: 编程任务
  - "开发"、"实现" 等 → 加载 programming-assistant

优先级 4: 自动触发
  - 复杂问题修复成功 → 静默知识归纳
```

#### 2. 上下文感知

**Sequential-Thinking 应考虑**：
- 对话历史：这是新任务还是连续任务？
- 进化模式：是否已经激活？
- 任务类型：新功能开发 / 问题修复 / 代码重构？
- 复杂度：简单任务可能不需要知识提取

#### 3. 自适应阈值

**动态调整知识提取的触发阈值**：
- 简单任务 → 提高阈值（减少干扰）
- 复杂任务 → 降低阈值（积极提取）
- 连续任务 → 只提取新出现的经验（避免重复）

### 集成到 Skill 文件

在 `skill-evolution-manager/SKILL.md` 的开头添加：

```markdown
## 智能调度协议

当此 skill 被触发时，必须使用 **sequential-thinking** 进行深度分析：

1. **意图识别**: 识别用户意图类型
2. **上下文分析**: 分析会话上下文和历史
3. **状态检查**: 检查进化模式和协调器状态
4. **决策制定**: 根据分析结果制定调度策略
5. **执行调度**: 执行相应的初始化、skill 加载或流程
6. **反馈输出**: 向用户反馈执行结果和建议
```

### 调试和验证

使用以下方式验证 sequential-thinking 的效果：

```bash
# 开启 verbose 模式查看思维过程
python scripts/toggle_mode.py --init --verbose

# 查看决策日志
cat .opencode/.coordinator.log
```

---

**文档版本**: 3.0
**最后更新**: 2025-01-24
**新特性**: ✅ 集成 Sequential-Thinking 智能调度

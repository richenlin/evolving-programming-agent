# MVP 构建计划

> 基于 `docs/architecture-review.md` 全部优化方案 + 架构师二次评审反馈
> 日期：2026-03-02（合并 v1 + v2）
> 状态：**Phase 1~4 全部完成**（TASK-01~34 全部 pass，148 测试通过）
> 目标：覆盖 architecture-review.md 中所有 8 个方案 + 6 个产品能力

---

## 当前状态

| 阶段 | 状态 | 说明 |
|------|------|------|
| Phase 1：基础设施 + 状态管理器 | ✅ 完成 | TASK-01~09 全部 pass |
| Phase 2：知识系统加固 | ✅ 完成 | TASK-10~14 全部 pass |
| Phase 3：知识升级 + 智能路由 | ✅ 完成 | TASK-15~22 全部 pass |
| Phase 4：进阶 + 产品能力 | ✅ 完成 | TASK-23~34 全部 pass |

---

## 方案覆盖对照表

| 原 review 方案 | 任务覆盖 | 状态 |
|----------------|-----------|------|
| **S1** 状态管理器 | TASK-01~09（Phase 1） | ✅ 完成 |
| **S1 补充** 幂等性 | TASK-24 | ✅ 完成 |
| **S1 补充** 审计日志 | TASK-25 | ✅ 完成 |
| **S2** 知识库生命周期 | TASK-15~17（Phase 3） | ✅ 完成 |
| **S3** 上下文感知路由 | TASK-20~21（Phase 3）+ TASK-27（Phase 4） | ✅ 完成 |
| **T1** 知识检索基础（模糊匹配+排序） | TASK-18~19（Phase 3） | ✅ 完成 |
| **T1** jieba 中文分词 | TASK-28 | ✅ 完成 |
| **T1** embedding 语义搜索 | TASK-29 | ✅ 完成 |
| **T2** 归纳格式校验 | TASK-10~11（Phase 2） | ✅ 完成 |
| **T2** schema 对齐 | TASK-31（验证测试） | ✅ 完成 |
| **T3** 文件写入原子化 | TASK-02（Phase 1） | ✅ 完成 |
| **T3 补充** fsync | TASK-23 | ✅ 完成 |
| **T4** Shell 参数转义 | TASK-01（Phase 1） | ✅ 完成 |
| **D1** workflow 去重 | TASK-12~14（Phase 2） | ✅ 完成 |
| **新增** 集中配置 | TASK-26 | ✅ 完成 |
| 知识库导入导出 CLI | TASK-30 | ✅ 完成 |
| 多项目知识隔离 | TASK-32 | ✅ 完成 |
| 知识库 dashboard | TASK-33 | ✅ 完成 |

---

## 任务总览

| ID | 任务 | 类型 | 依赖 | 状态 |
|----|------|------|------|------|
| **Phase 1：基础设施 + 状态管理器** | | | | |
| TASK-01 | Shell 参数转义安全加固 | 安全加固 | 无 | ✅ |
| TASK-02 | 创建 file_utils.py（原子写入工具） | 基础设施 | 无 | ✅ |
| TASK-03 | 创建 task_manager.py — 状态转换校验核心 | 核心 | TASK-02 | ✅ |
| TASK-04 | 实现 task create 命令 | CLI | TASK-03 | ✅ |
| TASK-05 | 实现 task list 命令 | CLI | TASK-04 | ✅ |
| TASK-06 | 实现 task transition 命令 | CLI | TASK-03 | ✅ |
| TASK-07 | 实现 task status 命令 | CLI | TASK-05 | ✅ |
| TASK-08 | S1 集成测试 — 完整状态机流程 | 测试 | TASK-04~07 | ✅ |
| TASK-09 | 文档适配 — workflow 改用 CLI 命令 | 文档 | TASK-08 | ✅ |
| **Phase 2：知识系统加固** | | | | |
| TASK-10 | 归纳格式校验 — validate_input 函数 | 校验 | 无 | ✅ |
| TASK-11 | 归纳格式校验 — 集成到 summarize 流程 | 集成 | TASK-10 | ✅ |
| TASK-12 | workflow 去重 — 创建 _base.md | 重构 | TASK-09 | ✅ |
| TASK-13 | workflow 去重 — 精简 full-mode.md | 重构 | TASK-12 | ✅ |
| TASK-14 | workflow 去重 — 精简 simple-mode.md | 重构 | TASK-12 | ✅ |
| **Phase 3：知识升级 + 智能路由** | | | | |
| TASK-15 | 知识库 — usage_count 追踪 | 数据采集 | 无 | ✅ |
| TASK-16 | 知识库 — effectiveness 衰减 | 生命周期 | TASK-15 | ✅ |
| TASK-17 | 知识库 — gc/decay CLI 命令注册 | CLI | TASK-16 | ✅ |
| TASK-18 | 知识检索 — 模糊匹配 | 检索升级 | 无 | ✅ |
| TASK-19 | 知识检索 — 相关性排序 | 检索升级 | TASK-18 | ✅ |
| TASK-20 | 上下文感知路由 — task status 扩展 | 路由 | TASK-07 | ✅ |
| TASK-21 | 上下文感知路由 — SKILL.md 文档适配 | 文档 | TASK-20 | ✅ |
| TASK-22 | Phase 1~3 集成测试 + 回归验证 | 验收 | TASK-01~21 | ✅ |
| **Phase 4：进阶 + 产品能力** | | | | |
| TASK-23 | file_utils.py — fsync 持久性加固 | 缺陷修复 | 无 | ✅ |
| TASK-24 | task_manager.py — 幂等性状态转换 | 缺陷修复 | 无 | ✅ |
| TASK-25 | task_manager.py — 审计日志 | 新功能 | 建议 TASK-24 后 | ✅ |
| TASK-26 | 集中配置管理 — 提取 magic numbers | 重构 | 无 | ✅ |
| TASK-27 | SKILL.md — 修复上下文感知路由 | 文档修复 | 无 | ✅ |
| TASK-28 | 知识检索 — jieba 中文分词（可选依赖） | 新功能 | 建议 TASK-26 后 | ✅ |
| TASK-29 | 语义搜索 — embedding（可选依赖） | 新功能 | TASK-28 | ✅ |
| TASK-30 | 知识库导入导出 — 接入 CLI | 接线 | 无 | ✅ |
| TASK-31 | store.py 与 schema.json 对齐验证 | 测试补充 | 无 | ✅ |
| TASK-32 | 多项目知识隔离 | 新功能 | 建议 TASK-26 后 | ✅ |
| TASK-33 | 知识库可视化 dashboard | 新功能 | 无 | ✅ |
| TASK-34 | 全量回归验收 | 验收 | 全部 | ✅ |

**总计：34 个任务，全部完成** | 148 测试通过，3 跳过（可选依赖）

---

## Phase 4 任务详情

> Phase 1~3 的任务详情见 git 历史。以下仅保留 Phase 4 的实现记录。

---

### TASK-23：file_utils.py — 添加 fsync 保证持久性

| 字段 | 值 |
|------|-----|
| 来源 | 架构师评审新发现 |
| 解决 | 原子写入在系统崩溃时可能丢数据（temp 文件内容未刷盘就 rename 了） |
| 文件 | `evolving-agent/scripts/core/file_utils.py` |

**实现**：在 `atomic_write_json` 的 `json.dump()` 后、`os.replace()` 前添加 `f.flush()` + `os.fsync(f.fileno())`。

---

### TASK-24：task_manager.py — 幂等性状态转换

| 字段 | 值 |
|------|-----|
| 来源 | 架构师评审新发现 |
| 解决 | agent 因重试导致 "in_progress → in_progress" 时报错，应视为 no-op |
| 文件 | `evolving-agent/scripts/core/task_manager.py`，`tests/test_task_manager.py` |

**实现**：在 `transition()` 的 `VALID_TRANSITIONS` 校验之前添加 `if current_status == to_status: return task`。`completed → completed` 也是 no-op（不要求 actor=reviewer）。新增 3 个测试。

---

### TASK-25：task_manager.py — 审计日志

| 字段 | 值 |
|------|-----|
| 来源 | 架构师评审新发现 |
| 解决 | 状态转换无记录，出问题后无法追溯 |
| 文件 | `evolving-agent/scripts/core/task_manager.py`，`tests/test_task_manager.py` |

**实现**：每次非幂等状态转换后追加 `audit_log` 条目（`from`/`to`/`actor`/`timestamp`）。`create_task` 初始化 `"audit_log": []`。新增 4 个测试。

---

### TASK-26：集中配置管理 — 提取 magic numbers

| 字段 | 值 |
|------|-----|
| 来源 | 架构师评审新发现 |
| 解决 | 衰减率、GC 阈值、模糊匹配阈值等 magic numbers 散落在 6 个文件中 |
| 文件 | 新建 `evolving-agent/scripts/core/config.py`，修改 `lifecycle.py`/`query.py`/`summarizer.py` |

**实现**：新建 `config.py` 集中定义 `DECAY_DAYS_THRESHOLD`、`DECAY_RATE`、`GC_EFFECTIVENESS_THRESHOLD`、`FUZZY_MATCH_THRESHOLD`、`RELEVANCE_WEIGHTS`、`RECENCY_DECAY_DAYS`、`USAGE_NORMALIZATION`、`TOP_K_RESULTS`、`MIN_INPUT_LENGTH`。各模块从 config 导入，函数参数仍可覆盖。

---

### TASK-27：SKILL.md — 修复上下文感知路由

| 字段 | 值 |
|------|-----|
| 来源 | 架构师评审 + 审计发现 TASK-21 标记 pass 但实际未落地 |
| 解决 | SKILL.md 步骤 2 仍是纯关键词匹配，缺少上下文判断 |
| 文件 | `evolving-agent/SKILL.md` |

**实现**：步骤 2 拆分为 2.1（上下文优先检查：`run.py task status --json`）和 2.2（关键词匹配兜底）。

---

### TASK-28：知识检索 — jieba 中文分词（可选依赖）

| 字段 | 值 |
|------|-----|
| 来源 | Phase 4 检索升级 |
| 解决 | 中文文本 "修复CORS跨域问题" 被当成整体字符串，无法匹配 "跨域" trigger |
| 文件 | `evolving-agent/scripts/knowledge/query.py`，`requirements.txt` |

**实现**：方案 A（可选依赖 + graceful degradation）。新增 `tokenize()` 函数：有 jieba 时用 `jieba.lcut()`，否则用 `re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9]+', text)`。`query_by_triggers()` 的模糊匹配阶段使用 `tokenize()` 拆分。新增 5 个测试（1 个需 jieba 时 skip）。

---

### TASK-29：语义搜索 — embedding（可选依赖）

| 字段 | 值 |
|------|-----|
| 来源 | Phase 4 检索升级 |
| 解决 | 关键词/模糊匹配无法覆盖语义相关但词汇不同的场景 |
| 文件 | 新建 `evolving-agent/scripts/knowledge/embedding.py`，修改 `query.py`，`requirements.txt` |

**实现**：方案 A（本地 `sentence-transformers` + `all-MiniLM-L6-v2`）。新增 `embedding.py`（`get_model()`/`encode()`/`build_index()`/`search()`）。`query.py` 新增 `query_semantic()`/`query_hybrid()`，CLI 增加 `--mode keyword|semantic|hybrid`。不安装时自动 fallback 到关键词模式。新增 3 个测试（2 个需 sentence-transformers 时 skip）。

---

### TASK-30：知识库导入导出 — 接入 CLI

| 字段 | 值 |
|------|-----|
| 来源 | 审计发现代码已有但未接线 |
| 解决 | `knowledge_io.py` 的 `export_all`/`import_all` 已实现，但 `run.py` 中无对应 CLI 命令 |
| 文件 | `evolving-agent/scripts/run.py`，`tests/test_knowledge_io.py` |

**实现**：`run.py` 新增 `knowledge export --output <path> [--format json|markdown]` 和 `knowledge import --input <path> [--merge skip|overwrite|merge]`。新增 1 个 CLI 级 E2E 测试。

---

### TASK-31：store.py 与 schema.json 对齐 — 补充验证测试

| 字段 | 值 |
|------|-----|
| 来源 | 审计确认已对齐，补测试 |
| 解决 | 确认 7 个 store 函数均输出结构化 content |
| 文件 | `tests/test_store_schema_alignment.py` |

**实现**：原有 3 个测试（experience/problem/tech-stack），新增 4 个（scenario/testing/pattern/skill），共 7 个 category 全覆盖。

---

### TASK-32：多项目知识隔离

| 字段 | 值 |
|------|-----|
| 来源 | Phase 4 产品能力 |
| 解决 | 所有项目共享同一知识库，不同项目的经验相互干扰 |
| 文件 | `path_resolver.py`，`store.py`，`query.py`，`run.py` |

**实现方案（项目本地隔离）**：

```
~/.config/opencode/knowledge/      # 全局知识库（不变）
├── experiences/
├── problems/
└── ...

$PROJECT_ROOT/.opencode/knowledge/  # 项目级知识库
├── experiences/
├── problems/
└── ...
```

- **存储**：默认存全局；指定 `--project <path>` 或传入 `project_root` 参数时存入 `$PROJECT_ROOT/.opencode/knowledge/`
- **检索**：指定 `project_root` 时先查项目级 → 再查全局 → 按 ID 去重合并；不指定时只查全局（向后兼容）
- **优势**：无需 hash 映射、无需迁移脚本、项目知识天然随项目目录移动/删除
- **回退**：删除 `$PROJECT_ROOT/.opencode/knowledge/` 即可

具体改动：
1. `path_resolver.py` 新增 `get_project_kb_root(project_root)` 和 `get_global_kb_root()`
2. `store.py` 的 `store_knowledge()` 和 `store_experience()` 增加 `project_root=None` 参数
3. `query.py` 的 `query_by_triggers()` 增加 `project_root=None` 参数，内部拆分为 `_query_by_triggers_single_root()` 辅助函数
4. `run.py` knowledge 子命令增加 `--project` 可选参数

新增 4 个测试：`test_global_store_and_query`、`test_project_store_and_query`、`test_cross_project_no_leak`、`test_project_plus_global_merge`。

---

### TASK-33：知识库可视化 dashboard

| 字段 | 值 |
|------|-----|
| 来源 | Phase 4 产品能力 |
| 解决 | 用户无法直观了解知识库健康状态 |
| 文件 | 新建 `evolving-agent/scripts/knowledge/dashboard.py`，修改 `run.py` |

**实现**：`generate_stats()` 返回 `total_entries`/`by_category`/`top_used`/`recently_added`/`stale_count`/`avg_effectiveness`。`format_dashboard()` 输出 ASCII 柱状图 + 表格。CLI: `knowledge dashboard [--json]`。空知识库输出 "Knowledge base is empty"。新增 3 个测试。

---

### TASK-34：全量回归验收

| 字段 | 值 |
|------|-----|
| 来源 | 最终验收 |

**结果**：
- `pytest tests/ -v`：**148 passed, 3 skipped**（skip 为可选依赖 jieba/sentence-transformers 未安装）
- 所有 CLI 命令验证通过
- 审计日志完整
- 无 `.tmp` 残留文件
- config.py 集中管理生效

---

## Phase 5：Claude Code 多 Agent 调度升级

> 状态：✅ 已完成
> 来源：架构评审发现文档描述过时

### 背景

Claude Code 自 2026-02 起提供稳定的 Task tool (Subagents)。项目文档中 6 个文件 11 处仍将 Claude Code 描述为"无原生多 agent 系统，由当前 agent 串行模拟"，需要更新。

### TASK-35：更新 Claude Code 多 Agent 调度文档

| 字段 | 值 |
|------|-----|
| 来源 | 架构评审 — Claude Code 平台能力已更新 |
| 解决 | 6 个 md 文件中"串行模拟"描述过时，reviewer/evolver 缺乏上下文隔离 |
| 文件 | `SKILL.md`、`_base.md`、`full-mode.md`、`simple-mode.md`、`README.md`、`evolution-check.md` |
| 预计 | 30 分钟 |

**具体工作**：

将 Claude Code 的调度描述从"串行模拟 + 加载 md 切换角色"统一更新为"Task tool spawn subagent"：

1. **SKILL.md** — "多 Agent 调度（编程意图）" 的 Claude Code 章节：
   - 删除"无原生多 agent 系统，由当前 agent 串行模拟"
   - 改为：当前 agent 扮演 orchestrator，通过 Task tool spawn reviewer/evolver/coder 为独立 subagent
   - 保留与 OpenCode 的差异说明（`@agent` 语法 vs `Task(subagent_type, prompt)` 语法）

2. **_base.md / full-mode.md / simple-mode.md** — 平台差异表：
   ```
   原：| Claude Code | 当前 agent 串行模拟 orchestrator 逻辑 | 通过 Read 加载对应 agent 文档切换角色 |
   改：| Claude Code | 当前 agent 扮演 orchestrator，通过 Task tool 调度 | Task tool spawn reviewer/evolver subagent（独立上下文） |
   ```

3. **README.md** — 闭环图中的 `[Claude Code]` 行：
   ```
   原：[Claude Code] 加载 agents/reviewer.md 切换角色审查
   改：[Claude Code] Task tool spawn reviewer subagent（加载 agents/reviewer.md 作为 prompt）
   ```

4. **evolution-check.md** — 平台差异表同 2

**验收标准**：
- `grep -r "串行模拟" evolving-agent/` 返回 0 结果
- `grep -r "切换角色" evolving-agent/` 返回 0 结果
- 所有 `[Claude Code]` 注释使用 Task tool 语法
- OpenCode 相关描述不受影响
- `pytest tests/ -v` 全部通过

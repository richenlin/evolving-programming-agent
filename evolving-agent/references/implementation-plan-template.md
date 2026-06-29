# Implementation Plan 模板

> orchestrator 在 **full-mode** 拆解任务后写入 `$PROJECT_ROOT/.opencode/.implementation-plan.md`。
> 借鉴 Superpowers writing-plans：假设执行者零项目上下文。

## 文档头（必填）

```markdown
# [功能名] Implementation Plan

> **For @coder:** 按 feature_list.json 中对应 task-id 执行；TDD 见 references/tdd-rules.md。

**Goal:** [一句话目标]

**Architecture:** [2-3 句方案概述]

**Tech Stack:** [关键技术/库]

## Global Constraints

[从用户需求/设计摘要复制的项目级约束——版本、命名、依赖限制，逐条 verbatim]

---
```

## 任务块结构

每个 `feature_list.json` 任务在此有对应章节（task-id 对齐）：

```markdown
### Task {task-id}: {name}

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Interfaces:**
- Consumes: [前置任务产出——函数签名/类型]
- Produces: [后续任务依赖——函数签名/类型]

**Acceptance Criteria:**
- [ ] [可验证的验收条件 1]
- [ ] [可验证的验收条件 2]

**Steps:**
- [ ] **Step 1: Write failing test** — 展示完整测试代码
- [ ] **Step 2: Verify RED** — `命令` → Expected: FAIL with "..."
- [ ] **Step 3: Minimal implementation** — 展示完整实现代码
- [ ] **Step 4: Verify GREEN** — `命令` → Expected: PASS
- [ ] **Step 5: Commit** — `git add ... && git commit -m "..."`
```

## 禁止项（plan 失败）

- TBD / TODO / "implement later"
- "Add appropriate error handling"（无具体代码）
- "Similar to Task N"（必须重复代码——执行者可能乱序读）
- 无 exact file path 的步骤

## Plan Self-Review（orchestrator 写入后自检）

1. **Spec 覆盖**：用户需求每条是否对应某 task？
2. **Placeholder 扫描**：搜索 TBD/TODO/"appropriate"/"similar to"
3. **类型一致**：前后 task 的函数名/签名是否一致？
4. **AC 对齐**：每个 task 的 Acceptance Criteria 是否已同步到 `feature_list.json` 对应任务的 `acceptance_criteria` 字段？

问题 inline 修复后再进入编码循环。

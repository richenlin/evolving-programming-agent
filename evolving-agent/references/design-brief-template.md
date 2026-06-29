# Design Brief 模板（可选）

> 仅 **full-mode + 多子系统/架构级需求** 时由 orchestrator 写入
> `$PROJECT_ROOT/.opencode/.design-brief.md`。
> simple-mode / 单文件修复 **跳过**。

## 触发条件（满足任一）

- 用户需求涉及 **3+ 独立子系统**（如 auth + billing + storage）
- 需要 **架构选型**（框架/数据库/部署模式）
- 变更跨越 **3+ 模块** 且边界不清

## 文档结构

```markdown
# [功能名] Design Brief

**Problem:** [解决什么问题]
**Success Criteria:** [怎样算完成]

## Approaches Considered

### Option A (Recommended)
- Pros: ...
- Cons: ...
- Why chosen: ...

### Option B
- Pros: ...
- Cons: ...

## Architecture
[组件、数据流、错误处理、测试策略——按复杂度分段，每段 200 字以内]

## Scope Boundaries
- In scope: ...
- Out of scope (YAGNI): ...

## Task Decomposition Preview
| Task | 职责 | depends_on |
|------|------|------------|
| task-001 | ... | [] |
```

## orchestrator 行为

1. 结合 `.design-context.md`（codegraph 检索）填写 brief
2. **不阻塞 simple 路径**：brief 是 orchestrator 内部文档，无需用户逐段审批
3. brief 完成后 → 按 `implementation-plan-template.md` 写 plan → 拆解 feature_list

## 与 Superpowers brainstorming 的差异

| Superpowers | EPA |
|-------------|-----|
| 逐问用户、分段审批 | orchestrator 自主产出 brief（检索+推理） |
| 所有项目强制 | 仅多子系统 full-mode |
| 人类 gate | 知识检索 + 计划自检 gate |

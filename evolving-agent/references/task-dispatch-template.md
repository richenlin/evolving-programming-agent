# @coder 调度模板（Fresh Context）

> orchestrator 调度 @coder 时使用。每个任务 **独立上下文**，不传递 orchestrator 会话历史。
> 借鉴 Superpowers subagent-driven-development 的 implementer prompt 模式。

## 调度 Prompt 模板

```
读取 $PROJECT_ROOT/.opencode/agents/coder.md 作为角色定义。
读取 {workflow_file} 作为工作指南。
读取 $PROJECT_ROOT/.opencode/references/tdd-rules.md 并遵循 TDD 铁律。

## 任务
- task-id: {TASK_ID}
- 名称: {TASK_NAME}
- 描述: {TASK_DESCRIPTION}

## 验收标准（Spec）
{ACCEPTANCE_CRITERIA_BULLETS}

## 计划片段（仅本任务）
从 $PROJECT_ROOT/.opencode/.implementation-plan.md 提取 Task {TASK_ID} 章节。
（simple-mode 或无 plan 文件时跳过此段）

## 项目上下文（按需）
读取 $PROJECT_ROOT/.opencode/.knowledge-context.md（如存在）

## 修复上下文（如 rejected）
读取 feature_list.json 中本任务的 reviewer_notes

## 约束
- 项目根目录: $PROJECT_ROOT
- 完成后状态 → review_pending（禁止自行 completed）
- 禁止加载 evolving-agent skill
- 只改本任务相关文件；不扩散 scope
```

## orchestrator 规则

1. **每任务一次调度**——不批量塞多个 task 到一个 @coder prompt（并行批次除外：每 task 仍独立一条调度）
2. **最小上下文**：只注入上表列出的文件，不传完整会话 transcript
3. full-mode 必须先有 `.implementation-plan.md`（或 task 描述含完整 AC）
4. rejected 回流时必须在 prompt 中 verbatim 附带 reviewer_notes

## 并行批次

同一批次无依赖的多 task：在同一消息发出 **多条** 独立调度（每条用本模板），而非一条调度包含多 task。

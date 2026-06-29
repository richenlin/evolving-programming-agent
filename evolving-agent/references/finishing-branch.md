# 分支收尾 Checklist

> orchestrator 在 **步骤 4 最终验证** 中，所有任务 completed 且知识归纳完成后执行。
> 借鉴 Superpowers finishing-a-development-branch。

## 前置条件

- [ ] `python $RUN_PY task status` 全部 completed
- [ ] 测试套件通过（orchestrator 或最后一次 @coder 已验证）
- [ ] `codegraph extract` 已执行或 evolution mode 未激活

## 验证命令

```bash
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
RUN_PY="$PROJECT_ROOT/.opencode/scripts/run.py"

python "$RUN_PY" task status --json
git status -sb
# 项目测试命令，例如:
# pytest -q  或  npm test
```

## 向用户呈现选项

所有任务完成后，orchestrator 向用户报告并询问：

1. **Merge** — 合并到主分支（如已在 feature branch）
2. **Create PR** — 推送并创建 Pull Request
3. **Keep branch** — 保留分支，稍后继续
4. **Discard** — 放弃变更（需用户明确确认）

## 清理

```bash
python "$PROJECT_ROOT/.opencode/scripts/run.py" task cleanup
```

`task cleanup` 清除 `.opencode/feature_list.json` 等会话文件，**不**删除 plan/brief（可留作文档）。

## orchestrator 禁止

- 未经用户确认 force push / hard reset
- 自动 merge 到 main（除非用户明确要求）
- 跳过测试验证直接宣布完成

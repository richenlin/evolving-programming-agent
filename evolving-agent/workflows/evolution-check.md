# Evolution Check — 知识归纳

在编码/修复循环结束后执行。由 SKILL.md 步骤 3.5 直接运行 `codegraph extract`。

## 环境变量

```bash
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
RUN_PY="$PROJECT_ROOT/.opencode/scripts/run.py"
```

---

## 执行条件

检查 `.opencode/.evolution_mode_active`：
- 存在 → 执行下方流程
- 不存在 → 跳过

脚本内置质量过滤，以下情况自动跳过：
- 全部 pass 且无问题/决策/review 发现
- 候选条目未通过质量门槛

以下情况会提取：
- reviewer reject 后修复成功
- progress.txt 中的问题/决策
- feature_list.json 中的 reviewer_notes
- 用户明确要求"记住"（写入 progress 即可）

---

## 流程

```bash
python $RUN_PY codegraph extract --project "$PROJECT_ROOT"
```

等价别名：

```bash
python $RUN_PY evolve --project "$PROJECT_ROOT"
```

强制提取（跳过 pass-only 过滤）：

```bash
python $RUN_PY codegraph extract --project "$PROJECT_ROOT" --force
```

---

## 存储规则（脚本自动执行）

| 经验类型 | 全局 KB | 项目 KB |
|---------|---------|---------|
| 通用解法（跨项目普适） | ✅ | ❌ |
| 项目特有 / 架构决策 / 环境配置 | ❌ | ✅ |

项目 KB 条目同时写入向量索引，供下次 `codegraph context` 检索。

---

## 格式规范（写入 progress.txt 以提高提取质量）

```
问题：<问题描述> → 解决：<解决方案>
决策：<选择了什么> → 原因：<为什么>
教训：<什么情况下> → 避免：<不要做什么>
```

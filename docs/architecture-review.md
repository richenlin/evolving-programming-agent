# Architecture Review & MVP Build Plan
## Evolving Programming Agent

> 视角：资深软件工程师  
> 参考：[sanyuan0704/code-review-expert](https://github.com/sanyuan0704/code-review-expert)  
> 日期：2026-03-01  
> 版本：v5.0 架构审查 + MVP 构建计划

---

## Part 1: 架构审查摘要

### 核心结论

**顶层设计正确，最大优化空间在 reviewer 审查深度。**

当前系统的核心价值（硬约束闭环 + 角色分离 + DAG 调度）是正确的，不需要重构。最高回报的单一改进是：参考 `code-review-expert` 为 reviewer 引入结构化 references checklist，将审查覆盖率从 ~30% 提升到 ~80%。

### 已确认的问题清单

| ID | 问题 | 文件 | 严重性 | 影响 |
|----|------|------|--------|------|
| BUG-01 | reviewer 模型配置冲突：`model` 字段写的是 `opencode/gpt-5.3-codex`，但设计意图是 `openrouter/anthropic/claude-sonnet-4.6` | `agents/reviewer.md:4` | P1 | 审查质量低于设计意图 |
| BUG-02 | 进化模式标记文件路径使用 `Path.cwd()` 而非 git 根目录，在子目录运行时失效 | `scripts/run.py:215` | P2 | 子目录执行时进化模式检测失败 |
| GAP-01 | reviewer 缺乏 SOLID 检查（SRP/OCP/LSP/ISP/DIP） | `agents/reviewer.md` | P1 | 无法检测架构级技术债务 |
| GAP-02 | reviewer 安全检查不完整（缺 JWT/TOCTOU/Supply Chain/Prototype Pollution） | `agents/reviewer.md` | P1 | 安全漏洞可能通过审查 |
| GAP-03 | reviewer 缺乏死代码/移除候选检查 | `agents/reviewer.md` | P2 | 无用代码积累 |
| GAP-04 | reviewer 缺乏 preflight 变更范围评估（大 diff 处理策略） | `agents/reviewer.md` | P2 | 大 PR 审查质量下降 |
| GAP-05 | `reviewer_notes` 为自由文本，evolver 提取教训时无法结构化分析 | `agents/reviewer.md:61-70` | P2 | 知识提取精度低 |
| GAP-06 | GitHub 学习需要 3 条命令手动串联，中间有丢失数据的风险 | `scripts/github/` | P3 | 使用体验差，易出错 |

### 架构强项（保持不变）

- **硬约束状态机**：`pending → in_progress → review_pending → completed/rejected` 不可跳过
- **角色分离**：coder 不自审，reviewer 不写代码，evolver 不执行任务
- **DAG 并行调度**：`depends_on` + 批次并行是 agent 编排的工程最优解
- **跨平台知识共享**：`~/.config/opencode/knowledge/` 三平台共用

---

## Part 2: MVP 定义

**MVP 目标**：让 reviewer agent 具备系统化、可操作的审查能力，使代码审查覆盖率从 ~30% 提升到 ~80%。

**MVP 范围**（10 个任务，按实现顺序）：

```
T01  修复 reviewer 模型配置                    ← 零风险，1 行
T02  修复进化模式路径 bug                       ← 低风险，5 行
T03  创建 references/solid-checklist.md        ← 纯新增文档
T04  创建 references/security-checklist.md     ← 纯新增文档
T05  创建 references/quality-checklist.md      ← 纯新增文档
T06  创建 references/removal-plan.md           ← 纯新增文档
T07  升级 reviewer：添加 preflight 步骤         ← 轻度修改
T08  升级 reviewer：引入 6 步结构化流程         ← 中度修改（依赖 T03-T06）
T09  升级 reviewer：严重级别对齐 P0-P3          ← 轻度修改（依赖 T07-T08）
T10  添加 `github learn` 一键命令              ← 纯新增代码
```

**Post-MVP**（可选，有破坏性变更）：

```
T11  结构化 reviewer_notes（Breaking Change）  ← 需用户决策
T12  evolver/orchestrator 适配新格式            ← 依赖 T11
```

---

## Part 3: MVP 任务分步计划

> **执行规则**：每次只执行一个任务。完成验证后再开始下一个。

---

### T01 — 修复 reviewer 模型配置冲突

**问题**：`reviewer.md` 的 `model` 字段与架构设计不符。

**开始状态**：`agents/reviewer.md:4` 的值是 `opencode/gpt-5.3-codex`

**精确改动**：

```
文件：evolving-agent/agents/reviewer.md
位置：第 4 行
改前：model: opencode/gpt-5.3-codex
改后：model: openrouter/anthropic/claude-sonnet-4.6
```

**结束状态**：`reviewer.md:4` 值为 `openrouter/anthropic/claude-sonnet-4.6`

**验证**：
```bash
grep "model:" evolving-agent/agents/reviewer.md
# 期望输出：model: openrouter/anthropic/claude-sonnet-4.6
```

**破坏性**：无。仅改 frontmatter 配置，不影响任何逻辑。

---

### T02 — 修复进化模式标记文件路径 bug

**问题**：`run.py` 中 `get_evolution_mode_status()` 使用 `Path.cwd()` 定位标记文件，在子目录运行时会找不到文件。

**开始状态**：`scripts/run.py:215` 使用 `Path.cwd()`

**精确改动**：

```
文件：evolving-agent/scripts/run.py
函数：get_evolution_mode_status()

改前：
def get_evolution_mode_status() -> str:
    """获取进化模式状态"""
    marker = Path.cwd() / '.opencode' / '.evolution_mode_active'
    return "ACTIVE" if marker.exists() else "INACTIVE"

改后：
def get_evolution_mode_status() -> str:
    """获取进化模式状态"""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True, text=True, check=True
        )
        project_root = Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        project_root = Path.cwd()
    marker = project_root / '.opencode' / '.evolution_mode_active'
    return "ACTIVE" if marker.exists() else "INACTIVE"
```

**结束状态**：从任意子目录运行 `python run.py info` 均能正确检测进化模式。

**验证**：
```bash
# 在项目根目录触发进化模式（创建标记文件）
mkdir -p .opencode && touch .opencode/.evolution_mode_active

# 从子目录运行，应显示 ACTIVE
cd evolving-agent && python scripts/run.py info | grep "Evolution Mode"
# 期望输出：Evolution Mode:  ACTIVE

# 清理
rm .opencode/.evolution_mode_active
```

**破坏性**：无。行为变更是从"错误"变为"正确"，无副作用。

---

### T03 — 创建 references/solid-checklist.md

**问题**：reviewer 无 SOLID 检查，无法发现架构级问题。

**开始状态**：目录 `evolving-agent/agents/references/` 不存在。

**精确改动**：

创建文件 `evolving-agent/agents/references/solid-checklist.md`，内容涵盖：
- SRP/OCP/LSP/ISP/DIP 各自的 smell 识别问题
- 常见代码气味（Long Method、Feature Envy、Data Clumps 等）
- 重构启发式规则（按职责拆分、引入抽象的时机等）

参考 `code-review-expert/references/solid-checklist.md`，针对 Python/JS/TS 场景本地化。

**结束状态**：文件存在且包含 5 个 SOLID 原则的检查要点。

**验证**：
```bash
ls evolving-agent/agents/references/solid-checklist.md
# 期望：文件存在

grep -c "^##" evolving-agent/agents/references/solid-checklist.md
# 期望：>= 5（至少5个二级标题，对应5个原则）

grep "SRP\|OCP\|LSP\|ISP\|DIP" evolving-agent/agents/references/solid-checklist.md | wc -l
# 期望：>= 5
```

**破坏性**：无。纯新增文件。

---

### T04 — 创建 references/security-checklist.md

**问题**：reviewer 安全检查仅覆盖 SQL 注入、XSS、越权，缺失 JWT/Race Condition/Supply Chain。

**开始状态**：`evolving-agent/agents/references/security-checklist.md` 不存在。

**精确改动**：

创建文件 `evolving-agent/agents/references/security-checklist.md`，内容涵盖：
- Input/Output 安全（XSS、注入、SSRF、Path Traversal、Prototype Pollution）
- AuthN/AuthZ（IDOR、RBAC、Session 管理）
- JWT 安全（Algorithm Confusion、exp 验证、Payload 敏感数据）
- Race Conditions（TOCTOU、Check-Then-Act、数据库并发、Shared State）
- Secrets/PII（硬编码密钥、日志泄露、git history）
- 运行时风险（无限循环、缺少超时、ReDoS）

**结束状态**：文件存在，包含 Race Condition 的 TOCTOU 示例和 JWT 检查。

**验证**：
```bash
ls evolving-agent/agents/references/security-checklist.md

grep -c "TOCTOU\|Race Condition\|JWT\|SSRF" evolving-agent/agents/references/security-checklist.md
# 期望：>= 4
```

**破坏性**：无。纯新增文件。

---

### T05 — 创建 references/quality-checklist.md

**问题**：reviewer 的性能检查和边界条件检查粒度不足。

**开始状态**：`evolving-agent/agents/references/quality-checklist.md` 不存在。

**精确改动**：

创建文件 `evolving-agent/agents/references/quality-checklist.md`，内容涵盖：

**错误处理**：
- 吞异常（空 catch 块）
- 过宽的 catch（捕获基类 Exception）
- 未处理的 async 错误
- 错误信息泄露（stack trace 暴露给用户）

**性能**：
- N+1 查询（含反例代码）
- 缓存问题（无 TTL、无失效策略、键冲突）
- ReDoS（复杂正则在热路径中）
- 内存：无界集合增长

**边界条件**：
- Null/undefined 处理（含"truthy check 排除 0 和空字符串"的 anti-pattern）
- 空集合（`arr[0]` 无长度检查）
- 数值边界（除以零、整数溢出）
- 字符串边界（空字符串、仅空白、超长）

**结束状态**：文件存在，含 N+1 查询反例和边界条件 anti-pattern。

**验证**：
```bash
ls evolving-agent/agents/references/quality-checklist.md

grep -c "N+1\|null\|cache\|boundary\|Null\|Cache" evolving-agent/agents/references/quality-checklist.md
# 期望：>= 4
```

**破坏性**：无。纯新增文件。

---

### T06 — 创建 references/removal-plan.md

**问题**：reviewer 无死代码/移除候选检查。

**开始状态**：`evolving-agent/agents/references/removal-plan.md` 不存在。

**精确改动**：

创建文件 `evolving-agent/agents/references/removal-plan.md`，内容涵盖：
- **识别标准**：未调用函数、已禁用的 feature flag 分支、重复逻辑、过时注释
- **安全删除 vs 延迟删除**的判断标准
  - 安全删除：无外部调用、有测试覆盖、变更范围局限
  - 延迟删除：公开 API、跨服务调用、不确定调用方
- **输出模板**：
  ```
  ## Removal Candidates
  | 位置 | 类型 | 理由 | 建议 |
  |------|------|------|------|
  | file.py:42 | 未使用函数 | 无调用者 | 安全删除 |
  ```

**结束状态**：文件存在，含"安全删除"和"延迟删除"判断标准。

**验证**：
```bash
ls evolving-agent/agents/references/removal-plan.md

grep "安全删除\|safe delete\|defer" evolving-agent/agents/references/removal-plan.md | wc -l
# 期望：>= 2
```

**破坏性**：无。纯新增文件。

---

### T07 — 升级 reviewer：添加 preflight 步骤

**前置条件**：T01 已完成（模型配置正确）。

**问题**：reviewer 直接进入审查，缺乏变更范围评估，大 diff（>500 行）时审查质量下降。

**开始状态**：`reviewer.md` 的"步骤 1"是直接 `git diff HEAD~1`。

**精确改动**：

```
文件：evolving-agent/agents/reviewer.md

在 "## 审查流程" 下，将现有 "步骤 1：获取变更" 替换为以下两个步骤：

### 步骤 0：Preflight — 评估变更范围

\`\`\`bash
git status -sb
git diff --stat HEAD~1
\`\`\`

根据输出决定审查策略：
- **变更 ≤ 200 行**：直接完整审查
- **变更 200-500 行**：按文件分组，逐组审查
- **变更 > 500 行**：先输出文件级摘要，再按模块/功能分批审查，明确告知用户当前审查的批次范围

### 步骤 1：获取变更详情

\`\`\`bash
git diff HEAD~1
\`\`\`
（余下步骤顺序后移，原步骤 1 变为步骤 1，原步骤 2 变为步骤 2，原步骤 3 变为步骤 3）
```

**结束状态**：`reviewer.md` 包含 preflight 步骤，且有大 diff 处理策略。

**验证**：
```bash
grep "Preflight\|200 行\|500 行" evolving-agent/agents/reviewer.md | wc -l
# 期望：>= 3

grep -n "步骤 0" evolving-agent/agents/reviewer.md
# 期望：存在，且行号在 "步骤 1" 之前
```

**破坏性**：无。仅在 reviewer 流程前增加一步，不影响输出格式。

---

### T08 — 升级 reviewer：引入 6 步结构化流程

**前置条件**：T03、T04、T05、T06 已完成（references/ 目录下 4 个 checklist 均存在）。

**问题**：reviewer 的"步骤 2：逐维度审查"是一张表格，缺乏可操作的 checklist 引用。

**开始状态**：`reviewer.md` 的审查维度是一张 5 行表格，无 checklist 引用。

**精确改动**：

```
文件：evolving-agent/agents/reviewer.md

将 "步骤 2：逐维度审查" 的内容替换为以下 4 个子步骤：

### 步骤 2a：SOLID + 架构审查

加载并遵循 `references/solid-checklist.md`，重点检查：
- 当前变更是否引入了新的 SRP/DIP 违反
- 是否有可以通过扩展而非修改解决的地方（OCP）
- 新增类/函数是否与现有接口的契约一致（LSP）

### 步骤 2b：移除候选

加载并遵循 `references/removal-plan.md`，识别：
- 变更中是否顺带删除了应该删除的死代码
- 是否存在新增的冗余逻辑

### 步骤 2c：安全扫描

加载并遵循 `references/security-checklist.md`，重点检查：
- 新增的输入处理路径（注入/SSRF/路径穿越）
- 并发修改的共享状态（Race Condition/TOCTOU）
- 认证/授权边界（IDOR/缺少租户检查）

### 步骤 2d：代码质量扫描

加载并遵循 `references/quality-checklist.md`，重点检查：
- 错误处理完整性（吞异常/async 错误）
- 性能热路径（N+1/无界集合/缓存策略）
- 边界条件（null 处理/空集合/数值边界）
```

**结束状态**：`reviewer.md` 包含 4 个子步骤，每个子步骤明确引用对应 checklist。

**验证**：
```bash
grep "solid-checklist\|security-checklist\|quality-checklist\|removal-plan" evolving-agent/agents/reviewer.md | wc -l
# 期望：>= 4（4个 checklist 均被引用）

grep "步骤 2a\|步骤 2b\|步骤 2c\|步骤 2d" evolving-agent/agents/reviewer.md | wc -l
# 期望：4
```

**破坏性**：无。仅展开原有的审查维度，不改变输出格式。

---

### T09 — 升级 reviewer：严重级别对齐 P0-P3

**前置条件**：T07、T08 已完成（reviewer 流程已升级）。

**问题**：reviewer 使用"严重/一般/建议"三级，与行业标准（P0-P3）不对齐，且"严重/一般"边界模糊。

**开始状态**：`reviewer.md` 中"审查标准"和 `reviewer_notes` 示例使用【严重】【一般】【建议】格式。

**精确改动**：

```
文件：evolving-agent/agents/reviewer.md

1. 将 "## 审查标准" 替换为：

## 严重级别

| 级别 | 名称 | 判断标准 | 行动 |
|------|------|---------|------|
| **P0** | Critical | 安全漏洞、数据丢失风险、正确性 bug（生产必现） | 必须 reject，阻断合并 |
| **P1** | High | 逻辑错误、明显 SOLID 违反、性能回归 | 应 reject，合并前修复 |
| **P2** | Medium | 代码气味、可维护性问题、轻微 SOLID 违反 | 当前 PR 修复或创建 follow-up |
| **P3** | Low | 命名、注释、风格建议 | 可选改进 |

## 审查结论规则

- 有 **P0 或 P1** 问题 → 必须 reject
- 有 **P2** 问题 → 建议 reject（影响小时可 pass + 记录）
- 仅有 **P3** 问题 → pass，在 reviewer_notes 中记录

2. 将 "拒绝时" 的示例格式更新为：

\`\`\`json
{
  "review_status": "reject",
  "reviewer_notes": [
    "[P1] scripts/github/fetch_info.py:95 — urllib.request.urlopen 无超时设置，可被恶意服务器挂起；建议添加 timeout=30 参数",
    "[P2] agents/reviewer.md:42 — 审查表格缺少 SOLID 检查维度；建议引用 solid-checklist.md",
    "[P3] scripts/run.py:294 — run_script 函数名不够描述性；建议改为 run_subscript"
  ]
}
\`\`\`
```

**结束状态**：`reviewer.md` 使用 P0/P1/P2/P3 四级，`reviewer_notes` 示例格式为 `[Px] file:line — 问题 ; 建议`。

**验证**：
```bash
grep "P0\|P1\|P2\|P3" evolving-agent/agents/reviewer.md | wc -l
# 期望：>= 8（4个级别 × 至少2处引用）

grep "\[P1\]\|\[P0\]\|\[P2\]\|\[P3\]" evolving-agent/agents/reviewer.md | wc -l
# 期望：>= 3（示例中至少3条）
```

**破坏性**：`reviewer_notes` 的格式从 `【严重】...` 变为 `[P1] file:line — ...`。

**影响范围**：
- `agents/evolver.md`：evolver 读取 `reviewer_notes` 提取教训。现有逻辑是自然语言分析，格式变更不影响功能，但 evolver 可以从新格式中提取更精准的信息（file + line）。
- `agents/orchestrator.md`：orchestrator 读取 `review_status` 字段决策（pass/reject），不读取 `reviewer_notes` 内容，**不受影响**。

**结论**：此变更对现有功能无破坏，是向后兼容的格式升级。

---

### T10 — 添加 `github learn` 一键命令

**问题**：GitHub 学习需要 3 条命令手动串联，中间有数据丢失风险且使用体验差。

**开始状态**：`run.py` 的 github 模块只支持 `fetch/extract/store` 三个独立 action。

**精确改动**：

**Step 1**：创建 `evolving-agent/scripts/github/learn.py`

```python
#!/usr/bin/env python3
"""
github learn — 一键学习 GitHub 仓库

自动串联 fetch → extract → store 三步，使用临时文件传递中间数据。
"""
import json
import sys
import tempfile
from pathlib import Path

def main():
    import argparse
    parser = argparse.ArgumentParser(description='一键学习 GitHub 仓库')
    parser.add_argument('url', help='GitHub 仓库 URL')
    parser.add_argument('--knowledge-dir', help='知识库目录（可选）')
    parser.add_argument('--dry-run', action='store_true', help='仅 fetch+extract，不存储')
    args = parser.parse_args()

    # Step 1: fetch
    from fetch_info import get_repo_info
    print(f"[1/3] 获取仓库信息: {args.url}", file=sys.stderr)
    repo_info = get_repo_info(args.url)

    # Step 2: extract
    sys.path.insert(0, str(Path(__file__).parent))
    from extract_patterns import (
        detect_architecture_patterns,
        detect_tech_stack,
        detect_conventions,
        extract_best_practices
    )
    from datetime import datetime
    print(f"[2/3] 提取知识模式...", file=sys.stderr)
    extracted = {
        'name': repo_info.get('name', 'unknown'),
        'url': repo_info.get('url', ''),
        'hash': repo_info.get('latest_hash', ''),
        'extracted_at': datetime.now().isoformat(),
        'architecture_patterns': detect_architecture_patterns(repo_info.get('file_tree', [])),
        'tech_stack': detect_tech_stack(repo_info.get('readme', '')),
        'conventions': detect_conventions(repo_info.get('readme', '')),
        'practices': extract_best_practices(repo_info.get('readme', '')),
    }

    # Step 3: store（unless dry-run）
    if args.dry_run:
        print("[3/3] Dry-run 模式，跳过存储", file=sys.stderr)
        print(json.dumps(extracted, indent=2, ensure_ascii=False))
    else:
        from extract_patterns import store_to_knowledge_base
        print(f"[3/3] 存储到知识库...", file=sys.stderr)
        store_to_knowledge_base(extracted, args.knowledge_dir)

if __name__ == '__main__':
    main()
```

**Step 2**：在 `run.py` 的 `handle_github` 函数中添加 `learn` 映射：

```python
# 在 handle_github 函数的 mapping 字典中添加：
"learn": ("github", "learn"),

# 在 github_parser 的 action choices 中添加 "learn"：
choices=["fetch", "extract", "store", "learn"],
help="操作: fetch(获取信息), extract(提取模式), store(存储知识), learn(一键学习)"
```

**结束状态**：
- `scripts/github/learn.py` 存在
- `run.py github` 支持 `learn` action

**验证**：
```bash
# 验证命令注册
python evolving-agent/scripts/run.py github --help | grep learn
# 期望：learn 出现在帮助信息中

# 验证 dry-run 不报错（需要网络）
python evolving-agent/scripts/run.py github learn https://github.com/sanyuan0704/code-review-expert --dry-run 2>&1 | head -5
# 期望：显示 [1/3] [2/3] [3/3] 进度，输出 JSON
```

**破坏性**：无。纯新增功能，不修改现有 fetch/extract/store 行为。

---

## Part 4: Post-MVP 破坏性变更方案

以下两个任务涉及 `reviewer_notes` schema 变更，**需要用户决策后再执行**。

---

### T11 — 结构化 reviewer_notes（Breaking Change）

**背景**：当前 `reviewer_notes` 是 `string[]`，evolver 需要从自然语言中提取 file/severity/suggestion，精度较低。

**建议变更**：将 `reviewer_notes` 从 `string[]` 改为 `object[]`：

```json
{
  "reviewer_notes": [
    {
      "severity": "P1",
      "file": "scripts/github/fetch_info.py",
      "line": 95,
      "issue": "urllib.request.urlopen 无超时，可被恶意服务器挂起",
      "suggestion": "添加 timeout=30 参数"
    }
  ]
}
```

**破坏性影响**：

| 影响点 | 影响描述 | 是否需要更新 |
|--------|---------|-------------|
| `agents/reviewer.md` | 输出格式变更 | ✅ 需要 |
| `agents/evolver.md` | 读取 reviewer_notes 的方式变更 | ✅ 需要 |
| `modules/.../template/feature_list.json` | schema 示例需更新 | ✅ 需要 |
| `agents/orchestrator.md` | 只读 review_status，不读 notes | ❌ 不影响 |

**两个实现选项，请选择一个后再执行 T11**：

**选项 A（推荐）：向后兼容模式**
- `reviewer_notes` 同时接受 `string` 和 `object` 两种格式
- evolver 检查条目类型：如果是 object 使用结构化字段；如果是 string 使用旧逻辑
- **优点**：历史数据（已有的 `feature_list.json` 文件）不失效
- **缺点**：evolver 需要处理两种格式，代码稍复杂

**选项 B：强制迁移模式**
- `reviewer_notes` 只接受 `object[]`
- 同时提供迁移脚本将现有 string 格式转换为 object 格式
- **优点**：代码简洁，格式统一
- **缺点**：存量 `feature_list.json` 文件需要手动迁移

---

### T12 — evolver 适配结构化 reviewer_notes

**前置条件**：T11 已完成，且已决定选项 A 或 B。

**改动**：更新 `agents/evolver.md` 中读取 reviewer_notes 的指令，使其能处理结构化格式并提取 severity/file/issue 字段作为知识存储的分类依据。

---

## Part 5: 验收标准

MVP 完成（T01-T10 全部通过）后，系统应满足：

| 验收项 | 验证方式 |
|--------|---------|
| reviewer 使用正确模型 | `grep "model:" agents/reviewer.md` 输出 `openrouter/anthropic/claude-sonnet-4.6` |
| 进化模式路径正确 | 从子目录运行 `run.py info` 能检测到项目根目录的标记文件 |
| references/ 目录完整 | `ls agents/references/` 输出 4 个文件 |
| reviewer 流程包含 preflight | `grep "Preflight" agents/reviewer.md` 有输出 |
| reviewer 引用全部 4 个 checklist | `grep "checklist\|removal-plan" agents/reviewer.md` 有 4 行输出 |
| reviewer 使用 P0-P3 级别 | `grep "\[P0\]\|\[P1\]\|\[P2\]\|\[P3\]" agents/reviewer.md` 有输出 |
| github learn 命令可用 | `python run.py github learn <url> --dry-run` 成功执行 |

---

*本计划共 10 个 MVP 任务 + 2 个可选 Post-MVP 任务。每个任务独立可测试，无需依赖上下文历史记录即可执行。*

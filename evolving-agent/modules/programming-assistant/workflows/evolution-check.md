# Evolution Check - 进化检查

**必须**在每个开发/修复循环结束后执行。此步骤为**强制执行**，不可因任务简单而跳过。

---

## 平台差异

| 平台 | 执行方式 |
|------|----------|
| **OpenCode** | orchestrator 调用 `@evolver` subagent（独立 agent，后台执行） |
| **Claude Code** | 加载 `$SKILLS_DIR/evolving-agent/agents/evolver.md` 中的指令，切换角色执行 |

---

## ⚠️ 重要：知识归纳格式

```
❌ 错误方式（多行文本会返回空结果）:
cat << 'EOF' | python ... knowledge summarize --auto-store
问题1：xxx
问题2：xxx
EOF

✅ 正确方式（每条经验单独存储）:
echo "问题：xxx → 解决：yyy" | python ... knowledge summarize --auto-store
echo "问题：aaa → 解决：bbb" | python ... knowledge summarize --auto-store
```

**原则**: 一条命令存储一条经验，格式为 `问题：xxx → 解决：yyy`

---

## 强制执行条件

以下情况**必须**执行（不可选）：

| 场景 | 是否执行 |
|------|----------|
| 所有任务 completed 后 | ✅ **强制** |
| reviewer reject 后修复成功 | ✅ **高价值** |
| 用户说"记住这个" | ✅ |
| 发现更优方案 | ✅ |
| 特定环境 workaround | ✅ |

以下情况**跳过**：

| 场景 | 是否执行 |
|------|----------|
| 简单修改一行代码（无 reviewer 发现问题） | ❌ |
| 用户说"很好"、"ok"（无新知识产出） | ❌ |

> 注意：即使是"简单任务"，只要 reviewer_notes 中有发现，就必须提取。

---

## 检查流程

```
步骤1: 检测任务复杂度
    读取 .opencode/feature_list.json 检查任务数
    ├─ 任务数 > 10 或 会话轮数 > 50 → 需要会话压缩
    └─ 否则 → 直接进入步骤3

步骤2: 会话压缩（如需要）
    执行 /compact 命令压缩会话历史
    保留关键决策、问题解决方案、技术栈选择等

步骤3: 提取经验来源
    - 读取 $PROJECT_ROOT/.opencode/progress.txt（"遇到的问题"、"关键决策"）
    - 读取 $PROJECT_ROOT/.opencode/feature_list.json（所有 reviewer_notes）
    - 回顾本次会话中的架构决策

步骤4: 知识归纳（逐条存储）
    [OpenCode] 调用 @evolver 执行
    [Claude Code] 按 evolver.md 指令执行：
      ⚠️ 每条经验单独存储，不要批量存储！
      echo "..." | python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge summarize --auto-store
```

---

## 存储命令

```bash
# 设置路径变量（每个 shell 会话执行一次）
SKILLS_DIR=$([ -d ~/.config/opencode/skills/evolving-agent ] && echo ~/.config/opencode/skills || echo ~/.claude/skills)

# ⚠️ 每条经验单独存储
echo "问题：xxx → 解决：yyy" | python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge summarize --auto-store
```

---

## 示例

### 示例1: 单个问题修复

```bash
echo "问题：Vite项目跨域报错 → 解决：配置 server.proxy" | \
  python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge summarize --auto-store
```

### 示例2: reviewer 发现问题后修复

```bash
# reviewer 发现 SQL 注入，修复后提取教训
echo "教训：SQL 拼接字符串存在注入风险 → 避免：始终使用参数化查询或 ORM" | \
  python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge summarize --auto-store

echo "问题：bcrypt 编译报错 → 解决：使用 @node-rs/bcrypt 替代" | \
  python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge summarize --auto-store
```

### 示例3: 技术决策

```bash
echo "决策：选择 bcrypt 而非 argon2 → 原因：bcrypt 更成熟，无需 native 编译" | \
  python $SKILLS_DIR/evolving-agent/scripts/run.py knowledge summarize --auto-store
```

---

## 注意事项

- **单条存储**: 每条经验单独一个 `echo | python` 命令，不要批量
- **格式规范**: 使用 `问题/决策/教训：xxx → 解决/原因/避免：yyy` 格式
- **去重机制**: 知识库会自动去重相似条目
- **强制执行**: 任务完成后此步骤不可跳过

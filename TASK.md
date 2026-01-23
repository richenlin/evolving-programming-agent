# Evolving Programming Agent - MVP 构建任务清单

> 本文档将 SOLUTION.md 中的设计拆解为最小可测试的任务单元。
> 每个任务都可以独立执行和验证，按顺序完成即可构建完整 MVP。

---

## 任务执行说明

每个任务包含：
- **目标**：明确要实现什么
- **输入**：开始任务需要什么
- **输出**：任务完成后应该产出什么
- **验证**：如何测试任务是否成功

请按顺序执行，每完成一个任务后进行验证再继续下一个。

---

## Phase 1: 插件管理系统 (skill-manager 扩展)

### Task 1.1: 创建 YAML frontmatter 解析工具函数

**目标**: 创建一个可复用的 Python 函数，用于解析 SKILL.md 文件中的 YAML frontmatter。

**输入**: 
- 现有文件 `skill-manager/scripts/scan_and_check.py` 作为参考

**输出**: 
- 新文件 `skill-manager/scripts/utils/frontmatter_parser.py`
- 包含函数 `parse_frontmatter(file_path: str) -> dict`

**验证**:
```bash
cd skill-manager/scripts
python -c "
from utils.frontmatter_parser import parse_frontmatter
result = parse_frontmatter('../../github-to-skills/SKILL.md')
print(result)
assert 'name' in result
assert result['name'] == 'github-to-skills'
print('PASS')
"
```

**实现要点**:
- 读取文件内容
- 识别 `---` 分隔符之间的 YAML 块
- 使用 PyYAML 解析（如不可用则用正则表达式）
- 返回字典，解析失败返回空字典

---

### Task 1.2: 创建 toggle_skill.py 脚本框架

**目标**: 创建禁用/启用 skill 的基础脚本框架（仅包含参数解析和帮助信息）。

**输入**: 
- 无

**输出**: 
- 新文件 `skill-manager/scripts/toggle_skill.py`
- 支持命令行参数 `--enable <name>` 和 `--disable <name>`
- 支持 `--skills-dir <path>` 指定 skills 目录（默认 `~/.config/opencode/skill`）

**验证**:
```bash
cd skill-manager/scripts
python toggle_skill.py --help
# 应显示帮助信息

python toggle_skill.py --enable test-skill --skills-dir /tmp/test-skills
# 应显示 "Error: test-skill 未被禁用或不存在"
```

**实现要点**:
- 使用 argparse 处理命令行参数
- 互斥组确保 --enable 和 --disable 不能同时使用
- 验证 skills-dir 路径存在

---

### Task 1.3: 实现 disable_skill 函数

**目标**: 在 toggle_skill.py 中实现禁用 skill 的核心逻辑。

**输入**: 
- Task 1.2 产出的 `toggle_skill.py`

**输出**: 
- 更新的 `toggle_skill.py`，包含完整的 `disable_skill()` 函数

**验证**:
```bash
# 准备测试环境
mkdir -p /tmp/test-skills/test-skill
echo "---\nname: test-skill\n---\n# Test" > /tmp/test-skills/test-skill/SKILL.md

# 执行禁用
cd skill-manager/scripts
python toggle_skill.py --disable test-skill --skills-dir /tmp/test-skills

# 验证
ls /tmp/test-skills/.disabled/test-skill/SKILL.md
# 应该存在

ls /tmp/test-skills/test-skill
# 应该不存在（已移动）

# 清理
rm -rf /tmp/test-skills
```

**实现要点**:
- 检查源目录是否存在
- 创建 `.disabled` 目录（如不存在）
- 使用 shutil.move 移动目录
- 输出操作结果

---

### Task 1.4: 实现 enable_skill 函数

**目标**: 在 toggle_skill.py 中实现启用 skill 的核心逻辑。

**输入**: 
- Task 1.3 产出的 `toggle_skill.py`

**输出**: 
- 更新的 `toggle_skill.py`，包含完整的 `enable_skill()` 函数

**验证**:
```bash
# 准备测试环境（模拟已禁用的 skill）
mkdir -p /tmp/test-skills/.disabled/test-skill
echo "---\nname: test-skill\n---\n# Test" > /tmp/test-skills/.disabled/test-skill/SKILL.md

# 执行启用
cd skill-manager/scripts
python toggle_skill.py --enable test-skill --skills-dir /tmp/test-skills

# 验证
ls /tmp/test-skills/test-skill/SKILL.md
# 应该存在

ls /tmp/test-skills/.disabled/test-skill 2>/dev/null
# 应该不存在（已移动）

# 清理
rm -rf /tmp/test-skills
```

**实现要点**:
- 检查 `.disabled/<name>` 目录是否存在
- 使用 shutil.move 移回主目录
- 处理目标目录已存在的冲突情况
- 输出操作结果

---

### Task 1.5: 创建 health_check.py 脚本框架

**目标**: 创建健康检查脚本的基础框架，能够扫描 skills 目录并列出所有 skill。

**输入**: 
- Task 1.1 产出的 `frontmatter_parser.py`

**输出**: 
- 新文件 `skill-manager/scripts/health_check.py`
- 能够扫描指定目录，输出 skill 列表（JSON 格式）

**验证**:
```bash
cd skill-manager/scripts
python health_check.py --skills-dir ../../

# 应输出类似:
# {
#   "timestamp": "2026-01-23T...",
#   "total": 4,
#   "skills": ["github-to-skills", "skill-manager", "skill-evolution-manager", "programming-assistant-skill"]
# }
```

**实现要点**:
- 遍历目录，过滤以 `.` 开头的隐藏目录
- 检查每个子目录是否包含 SKILL.md
- 输出 JSON 格式结果

---

### Task 1.6: 实现 SKILL.md 存在性检查

**目标**: 在 health_check.py 中添加检查 SKILL.md 是否存在的逻辑。

**输入**: 
- Task 1.5 产出的 `health_check.py`

**输出**: 
- 更新的 `health_check.py`
- 每个 skill 增加 `has_skill_md: true/false` 字段
- 汇总增加 `invalid` 计数

**验证**:
```bash
# 准备测试环境
mkdir -p /tmp/test-skills/valid-skill
mkdir -p /tmp/test-skills/invalid-skill
echo "---\nname: valid\n---" > /tmp/test-skills/valid-skill/SKILL.md
# invalid-skill 故意不创建 SKILL.md

cd skill-manager/scripts
python health_check.py --skills-dir /tmp/test-skills

# 应输出 invalid: 1

# 清理
rm -rf /tmp/test-skills
```

---

### Task 1.7: 实现 GitHub hash 过期检查

**目标**: 在 health_check.py 中添加检查 GitHub 仓库是否有新版本的逻辑。

**输入**: 
- Task 1.6 产出的 `health_check.py`
- 现有的 `github-to-skills/scripts/fetch_github_info.py` 作为参考

**输出**: 
- 更新的 `health_check.py`
- 增加函数 `get_remote_hash(github_url: str) -> str`
- 每个 skill 增加 `is_outdated: true/false` 字段

**验证**:
```bash
# 准备测试环境（模拟过期的 skill）
mkdir -p /tmp/test-skills/outdated-skill
cat > /tmp/test-skills/outdated-skill/SKILL.md << 'EOF'
---
name: outdated-skill
github_url: https://github.com/octocat/Hello-World
github_hash: 0000000000000000000000000000000000000000
---
# Test
EOF

cd skill-manager/scripts
python health_check.py --skills-dir /tmp/test-skills

# 应输出 outdated: 1

# 清理
rm -rf /tmp/test-skills
```

**实现要点**:
- 使用 `git ls-remote <url> HEAD` 获取远程 hash
- 比较本地 hash 和远程 hash
- 网络错误时跳过检查，不标记为过期

---

### Task 1.8: 实现健康检查报告格式化输出

**目标**: 在 health_check.py 中添加人类可读的报告格式输出（除 JSON 外）。

**输入**: 
- Task 1.7 产出的 `health_check.py`

**输出**: 
- 更新的 `health_check.py`
- 增加 `--format` 参数，支持 `json`（默认）和 `table` 格式

**验证**:
```bash
cd skill-manager/scripts
python health_check.py --skills-dir ../../ --format table

# 应输出类似:
# ┌─────────────────────────────────────────────────────────┐
# │               Skill 健康检查报告                         │
# ├─────────────────────────────────────────────────────────┤
# │ 总计: 4 个 skill                                        │
# │ ✅ 健康: 4                                              │
# │ ⚠️  过期: 0                                              │
# │ ❌ 无效: 0                                              │
# └─────────────────────────────────────────────────────────┘
```

---

### Task 1.9: 更新 skill-manager SKILL.md 添加新命令

**目标**: 更新 skill-manager 的 SKILL.md 文档，添加新命令的触发逻辑。

**输入**: 
- 现有的 `skill-manager/SKILL.md`

**输出**: 
- 更新的 `skill-manager/SKILL.md`
- 包含 `enable`, `disable`, `status`, `health` 命令说明

**验证**:
```bash
grep -E "enable|disable|health" skill-manager/SKILL.md
# 应找到相关命令的文档
```

**实现要点**:
- 在 "Usage" 部分添加新命令
- 添加示例输出
- 说明每个命令的参数

---

## Phase 2: GitHub 学习器 (github-to-skills 扩展)

### Task 2.1: 扩展 fetch_github_info.py 获取文件树

**目标**: 扩展现有脚本，增加获取仓库文件树结构的能力。

**输入**: 
- 现有的 `github-to-skills/scripts/fetch_github_info.py`

**输出**: 
- 更新的 `fetch_github_info.py`
- 输出 JSON 增加 `file_tree` 字段（顶层目录列表）

**验证**:
```bash
cd github-to-skills/scripts
python fetch_github_info.py https://github.com/alan2207/bulletproof-react | python -c "
import sys, json
data = json.load(sys.stdin)
assert 'file_tree' in data
assert len(data['file_tree']) > 0
print('file_tree:', data['file_tree'][:5])
print('PASS')
"
```

**实现要点**:
- 使用 GitHub API（如可用）或解析 README 推断结构
- 备选方案：从 README 中提取目录结构描述
- 限制深度，只获取前两层

---

### Task 2.2: 创建 extract_patterns.py 脚本框架

**目标**: 创建范式提取脚本的基础框架，能从 stdin 读取 repo info 并输出基础模板。

**输入**: 
- Task 2.1 产出的 `fetch_github_info.py`

**输出**: 
- 新文件 `github-to-skills/scripts/extract_patterns.py`
- 能从 stdin 读取 JSON，输出 knowledge-addon 格式的 Markdown 骨架

**验证**:
```bash
cd github-to-skills/scripts
echo '{"name": "test-repo", "url": "https://github.com/test/repo", "latest_hash": "abc123", "readme": "# Test", "file_tree": []}' | python extract_patterns.py

# 应输出类似:
# ---
# name: test-repo-knowledge
# type: knowledge-addon
# target_skill: programming-assistant
# ...
# ---
# # test-repo 学习笔记
```

---

### Task 2.3: 实现基于文件树的架构模式检测

**目标**: 在 extract_patterns.py 中实现基于文件树的架构模式检测逻辑。

**输入**: 
- Task 2.2 产出的 `extract_patterns.py`

**输出**: 
- 更新的 `extract_patterns.py`
- 函数 `detect_architecture_patterns(file_tree: list) -> list`
- 能检测: Feature-Based, Component-Based, Hooks Pattern, MVC, Layered

**验证**:
```bash
cd github-to-skills/scripts
python -c "
from extract_patterns import detect_architecture_patterns

# 测试 Feature-Based
tree1 = ['src/features/auth', 'src/features/dashboard']
patterns1 = detect_architecture_patterns(tree1)
assert 'Feature-Based Architecture' in patterns1

# 测试 Component-Based
tree2 = ['src/components/Button', 'src/components/Modal']
patterns2 = detect_architecture_patterns(tree2)
assert 'Component-Based Design' in patterns2

print('PASS')
"
```

**实现要点**:
- 检测 `features/` 目录 → Feature-Based
- 检测 `components/` 目录 → Component-Based
- 检测 `hooks/` 目录 → Custom Hooks Pattern
- 检测 `models/`, `views/`, `controllers/` → MVC

---

### Task 2.4: 实现基于 README 的技术栈检测

**目标**: 从 README 内容中提取使用的技术栈和工具。

**输入**: 
- Task 2.3 产出的 `extract_patterns.py`

**输出**: 
- 更新的 `extract_patterns.py`
- 函数 `detect_tech_stack(readme: str) -> dict`
- 返回 `{"frameworks": [...], "tools": [...], "libraries": [...]}`

**验证**:
```bash
cd github-to-skills/scripts
python -c "
from extract_patterns import detect_tech_stack

readme = '''
# My Project
Built with React, TypeScript, and Vite.
Uses React Query for data fetching and Zustand for state management.
Testing with Vitest and Playwright.
'''

stack = detect_tech_stack(readme)
assert 'React' in stack['frameworks']
assert 'TypeScript' in stack['tools']
assert 'Vitest' in stack['tools'] or 'Vitest' in stack['libraries']
print('PASS')
"
```

**实现要点**:
- 使用关键词匹配（React, Vue, Angular, Next.js, etc.）
- 检测常见工具（TypeScript, ESLint, Prettier, etc.）
- 检测包管理器（npm, yarn, pnpm）

---

### Task 2.5: 实现 knowledge-addon 完整生成

**目标**: 整合所有检测结果，生成完整的 knowledge-addon Markdown 文件。

**输入**: 
- Task 2.4 产出的 `extract_patterns.py`

**输出**: 
- 更新的 `extract_patterns.py`
- 完整的 `generate_knowledge_addon()` 函数
- 输出包含: 项目架构、代码规范、技术栈、最佳实践、应用场景

**验证**:
```bash
cd github-to-skills/scripts
python fetch_github_info.py https://github.com/alan2207/bulletproof-react | python extract_patterns.py > /tmp/test-addon.md

# 检查输出
grep "type: knowledge-addon" /tmp/test-addon.md
grep "## 项目架构" /tmp/test-addon.md
grep "## 技术栈" /tmp/test-addon.md

# 清理
rm /tmp/test-addon.md
```

---

### Task 2.6: 更新 github-to-skills SKILL.md 添加学习模式

**目标**: 更新 SKILL.md，添加学习模式的触发逻辑和使用说明。

**输入**: 
- 现有的 `github-to-skills/SKILL.md`

**输出**: 
- 更新的 `github-to-skills/SKILL.md`
- 包含学习模式触发条件: `/learn <url>`, "学习这个仓库"
- 包含工作流说明

**验证**:
```bash
grep -E "learn|学习" github-to-skills/SKILL.md
# 应找到学习模式相关内容
```

---

## Phase 3: 自动进化机制 (skill-evolution-manager 扩展)

### Task 3.1: 扩展 evolution.json 数据结构

**目标**: 更新 merge_evolution.py 支持新的数据结构字段。

**输入**: 
- 现有的 `skill-evolution-manager/scripts/merge_evolution.py`

**输出**: 
- 更新的 `merge_evolution.py`
- 支持新字段: `patterns`, `context_triggers`

**验证**:
```bash
cd skill-evolution-manager/scripts

# 准备测试数据
mkdir -p /tmp/test-skill
echo '{"preferences": ["old pref"]}' > /tmp/test-skill/evolution.json

# 合并新数据
python merge_evolution.py /tmp/test-skill '{"patterns": {"react": ["use hooks"]}, "context_triggers": {"when_testing": "use vitest"}}'

# 验证
cat /tmp/test-skill/evolution.json
# 应包含 preferences, patterns, context_triggers

# 清理
rm -rf /tmp/test-skill
```

**实现要点**:
- patterns 是嵌套的 dict，需要深度合并
- context_triggers 是 dict，键值对合并

---

### Task 3.2: 扩展 smart_stitch.py 支持新字段

**目标**: 更新 smart_stitch.py 将新字段渲染到 SKILL.md 中。

**输入**: 
- Task 3.1 产出的新 evolution.json 格式
- 现有的 `skill-evolution-manager/scripts/smart_stitch.py`

**输出**: 
- 更新的 `smart_stitch.py`
- 能渲染 `patterns` 和 `context_triggers` 到 Markdown

**验证**:
```bash
cd skill-evolution-manager/scripts

# 准备测试数据
mkdir -p /tmp/test-skill
cat > /tmp/test-skill/SKILL.md << 'EOF'
---
name: test
---
# Test Skill
EOF

cat > /tmp/test-skill/evolution.json << 'EOF'
{
  "preferences": ["use pnpm"],
  "patterns": {"react": ["use hooks", "use TypeScript"]},
  "context_triggers": {"when_creating_component": "use functional component"}
}
EOF

python smart_stitch.py /tmp/test-skill

# 验证
grep "patterns" /tmp/test-skill/SKILL.md || grep "React" /tmp/test-skill/SKILL.md
grep "context_triggers" /tmp/test-skill/SKILL.md || grep "when_creating" /tmp/test-skill/SKILL.md

# 清理
rm -rf /tmp/test-skill
```

---

### Task 3.3: 创建进化触发条件检测函数

**目标**: 创建一个独立的函数，用于判断当前会话是否应触发进化。

**输入**: 
- 无

**输出**: 
- 新文件 `skill-evolution-manager/scripts/trigger_detector.py`
- 函数 `should_trigger_evolution(session_summary: dict) -> bool`

**验证**:
```bash
cd skill-evolution-manager/scripts
python -c "
from trigger_detector import should_trigger_evolution

# 测试 1: 复杂 bug 修复（多次尝试）
summary1 = {'attempts': 3, 'success': True, 'feedback': None}
assert should_trigger_evolution(summary1) == True

# 测试 2: 简单修改（一次成功）
summary2 = {'attempts': 1, 'success': True, 'feedback': None}
assert should_trigger_evolution(summary2) == False

# 测试 3: 用户明确反馈
summary3 = {'attempts': 1, 'success': True, 'feedback': '记住这个'}
assert should_trigger_evolution(summary3) == True

print('PASS')
"
```

**实现要点**:
- 检测 attempts > 1
- 检测 feedback 包含关键词: "记住", "以后", "保存", "重要"
- 返回布尔值

---

### Task 3.4: 创建会话摘要提取函数

**目标**: 创建一个函数，从对话上下文中提取会话摘要。

**输入**: 
- Task 3.3 产出的 `trigger_detector.py`

**输出**: 
- 更新的 `trigger_detector.py`
- 函数 `extract_session_summary(context: str) -> dict`

**验证**:
```bash
cd skill-evolution-manager/scripts
python -c "
from trigger_detector import extract_session_summary

context = '''
用户: 帮我修复这个 bug
助手: 让我看看...第一次尝试失败
用户: 还是不行
助手: 让我换个方法...第二次尝试失败
用户: 再试试
助手: 这次成功了！
用户: 太好了，记住这个解决方案
'''

summary = extract_session_summary(context)
assert summary['attempts'] >= 2
assert summary['success'] == True
assert '记住' in (summary['feedback'] or '')
print('PASS')
"
```

**实现要点**:
- 统计"尝试"、"失败"等关键词出现次数
- 检测"成功"、"完成"等关键词
- 提取用户的明确反馈语句

---

### Task 3.5: 更新 programming-assistant SKILL.md 添加进化配置

**目标**: 在 programming-assistant 的 SKILL.md 中添加自动进化配置和检查流程。

**输入**: 
- 现有的 `programming-assistant-skill/SKILL.md`

**输出**: 
- 更新的 `programming-assistant-skill/SKILL.md`
- 在 frontmatter 中添加 `evolution` 配置
- 在会话结束检查中添加进化检查步骤

**验证**:
```bash
grep "evolution" programming-assistant-skill/SKILL.md
grep "auto_evolve" programming-assistant-skill/SKILL.md
grep "进化检查" programming-assistant-skill/SKILL.md
```

---

## Phase 4: 跨平台支持

### Task 4.1: 创建统一安装器入口脚本

**目标**: 在项目根目录创建统一的 install.sh，能够安装所有 skill 组件。

**输入**: 
- 现有的 `programming-assistant-skill/install.sh` 作为参考

**输出**: 
- 新文件 `install.sh`（项目根目录）
- 支持 `--all`, `--opencode`, `--claude-code`, `--cursor` 参数
- 支持 `--skills <list>` 指定要安装的 skill

**验证**:
```bash
./install.sh --help
# 应显示帮助信息，包含所有选项

./install.sh --dry-run --all
# 应显示将要执行的操作，但不实际执行
```

---

### Task 4.2: 实现批量 skill 安装逻辑

**目标**: 在 install.sh 中实现遍历多个 skill 目录并安装的逻辑。

**输入**: 
- Task 4.1 产出的 `install.sh`

**输出**: 
- 更新的 `install.sh`
- 能够安装多个 skill: github-to-skills, skill-manager, skill-evolution-manager, programming-assistant

**验证**:
```bash
./install.sh --dry-run --skills "github-to-skills,skill-manager"
# 应显示将安装这两个 skill
```

---

### Task 4.3: 实现 Cursor 格式适配

**目标**: 在 install.sh 中实现 Cursor 的特殊格式处理（移除 frontmatter）。

**输入**: 
- Task 4.2 产出的 `install.sh`

**输出**: 
- 更新的 `install.sh`
- Cursor 安装时自动移除 YAML frontmatter

**验证**:
```bash
./install.sh --dry-run --cursor --skills "programming-assistant"
# 应显示将转换格式

# 实际测试（如果 Cursor 已安装）
./install.sh --cursor --skills "programming-assistant"
head -5 ~/.cursor/rules/programming-assistant.md
# 第一行应该不是 "---"
```

---

### Task 4.4: 创建 uninstall.sh 统一卸载器

**目标**: 创建统一的卸载脚本，能够移除所有已安装的 skill。

**输入**: 
- Task 4.1-4.3 产出的 `install.sh` 作为参考

**输出**: 
- 新文件 `uninstall.sh`
- 支持 `--all`, `--opencode`, `--claude-code`, `--cursor` 参数
- 支持 `--skills <list>` 指定要卸载的 skill

**验证**:
```bash
./uninstall.sh --help
# 应显示帮助信息

./uninstall.sh --dry-run --all
# 应显示将要删除的内容，但不实际执行
```

---

## Phase 5: 协调器 (Evolving Agent)

### Task 5.1: 创建 evolving-agent 目录结构

**目标**: 创建协调器的基本目录结构和配置文件。

**输入**: 
- 无

**输出**: 
- 新目录 `evolving-agent/`
- 文件 `evolving-agent/SKILL.md`（基本框架）
- 文件 `evolving-agent/config.yaml`（配置模板）

**验证**:
```bash
ls evolving-agent/
# 应显示 SKILL.md 和 config.yaml

cat evolving-agent/SKILL.md
# 应包含 name: evolving-agent
```

---

### Task 5.2: 编写 evolving-agent SKILL.md 核心内容

**目标**: 编写协调器的完整 SKILL.md，定义触发条件和工作流程。

**输入**: 
- Task 5.1 产出的 `evolving-agent/SKILL.md`

**输出**: 
- 更新的 `evolving-agent/SKILL.md`
- 包含: 职责说明、触发条件、工作流程、与其他 skill 的协调逻辑

**验证**:
```bash
grep "github-to-skills" evolving-agent/SKILL.md
grep "skill-manager" evolving-agent/SKILL.md
grep "skill-evolution-manager" evolving-agent/SKILL.md
grep "programming-assistant" evolving-agent/SKILL.md
# 应都能找到
```

**实现要点**:
- 定义何时触发学习流程（检测 GitHub URL）
- 定义何时触发管理流程（/skill-manager 命令）
- 定义何时触发进化流程（会话结束 + 触发条件满足）

---

### Task 5.3: 创建 config.yaml 全局配置

**目标**: 定义系统的全局配置，包括各种阈值和开关。

**输入**: 
- Task 5.1 产出的 `evolving-agent/config.yaml`

**输出**: 
- 更新的 `evolving-agent/config.yaml`
- 包含: 进化阈值、自动更新检查间隔、日志级别等

**验证**:
```bash
cat evolving-agent/config.yaml
# 应包含 evolution_threshold, auto_check_interval 等配置
```

**配置项**:
```yaml
evolution:
  auto_evolve: true
  threshold: medium  # low, medium, high
  silent_mode: true

skill_manager:
  auto_check_interval: 7d  # 每 7 天检查一次更新
  auto_update: false

learning:
  default_mode: tool  # tool, learn
  save_addons_to: ~/.config/opencode/skill/knowledge-addons/
```

---

## Phase 6: 集成测试

### Task 6.1: 创建端到端测试脚本 - 学习流程

**目标**: 创建测试脚本验证 GitHub URL → 学习 → 生成 addon 的完整流程。

**输入**: 
- 所有 Phase 2 的产出

**输出**: 
- 新文件 `tests/e2e_learning.sh`
- 能够执行完整学习流程并验证输出

**验证**:
```bash
./tests/e2e_learning.sh https://github.com/alan2207/bulletproof-react
# 应输出 PASS 或 FAIL
```

---

### Task 6.2: 创建端到端测试脚本 - 插件管理

**目标**: 创建测试脚本验证 enable/disable/health 的完整流程。

**输入**: 
- 所有 Phase 1 的产出

**输出**: 
- 新文件 `tests/e2e_plugin_manager.sh`
- 能够执行完整插件管理流程并验证结果

**验证**:
```bash
./tests/e2e_plugin_manager.sh
# 应输出 PASS 或 FAIL
```

---

### Task 6.3: 更新项目 README.md

**目标**: 更新项目 README，反映 MVP 的新功能和使用方法。

**输入**: 
- 现有的 `README.md`
- 所有新增功能

**输出**: 
- 更新的 `README.md`
- 包含: 新功能说明、安装方法、使用示例

**验证**:
```bash
grep "学习模式" README.md
grep "health" README.md
grep "install.sh" README.md
# 应都能找到
```

---

## 任务依赖关系图

```
Phase 1 (插件管理)
├── Task 1.1 ────┐
├── Task 1.2 ──┬─┤
├── Task 1.3 ◄─┘ │
├── Task 1.4 ◄───┘
├── Task 1.5 ◄── Task 1.1
├── Task 1.6 ◄── Task 1.5
├── Task 1.7 ◄── Task 1.6
├── Task 1.8 ◄── Task 1.7
└── Task 1.9 ◄── Task 1.8

Phase 2 (学习器)
├── Task 2.1
├── Task 2.2 ◄── Task 2.1
├── Task 2.3 ◄── Task 2.2
├── Task 2.4 ◄── Task 2.3
├── Task 2.5 ◄── Task 2.4
└── Task 2.6 ◄── Task 2.5

Phase 3 (自动进化)
├── Task 3.1
├── Task 3.2 ◄── Task 3.1
├── Task 3.3
├── Task 3.4 ◄── Task 3.3
└── Task 3.5 ◄── Task 3.4

Phase 4 (跨平台)
├── Task 4.1
├── Task 4.2 ◄── Task 4.1
├── Task 4.3 ◄── Task 4.2
└── Task 4.4 ◄── Task 4.3

Phase 5 (协调器)
├── Task 5.1
├── Task 5.2 ◄── Task 5.1
└── Task 5.3 ◄── Task 5.1

Phase 6 (集成测试)
├── Task 6.1 ◄── Phase 2 完成
├── Task 6.2 ◄── Phase 1 完成
└── Task 6.3 ◄── 所有 Phase 完成
```

---

## 进度追踪

| Phase | Task | 状态 | 完成日期 |
|-------|------|------|---------|
| 1 | 1.1 frontmatter_parser | ⬜ pending | |
| 1 | 1.2 toggle_skill 框架 | ⬜ pending | |
| 1 | 1.3 disable_skill | ⬜ pending | |
| 1 | 1.4 enable_skill | ⬜ pending | |
| 1 | 1.5 health_check 框架 | ⬜ pending | |
| 1 | 1.6 SKILL.md 存在检查 | ⬜ pending | |
| 1 | 1.7 GitHub hash 检查 | ⬜ pending | |
| 1 | 1.8 报告格式化 | ⬜ pending | |
| 1 | 1.9 更新 SKILL.md | ⬜ pending | |
| 2 | 2.1 文件树获取 | ⬜ pending | |
| 2 | 2.2 extract_patterns 框架 | ⬜ pending | |
| 2 | 2.3 架构模式检测 | ⬜ pending | |
| 2 | 2.4 技术栈检测 | ⬜ pending | |
| 2 | 2.5 addon 完整生成 | ⬜ pending | |
| 2 | 2.6 更新 SKILL.md | ⬜ pending | |
| 3 | 3.1 evolution.json 扩展 | ⬜ pending | |
| 3 | 3.2 smart_stitch 扩展 | ⬜ pending | |
| 3 | 3.3 触发条件检测 | ⬜ pending | |
| 3 | 3.4 会话摘要提取 | ⬜ pending | |
| 3 | 3.5 更新 SKILL.md | ⬜ pending | |
| 4 | 4.1 install.sh 入口 | ⬜ pending | |
| 4 | 4.2 批量安装 | ⬜ pending | |
| 4 | 4.3 Cursor 适配 | ⬜ pending | |
| 4 | 4.4 uninstall.sh | ⬜ pending | |
| 5 | 5.1 目录结构 | ⬜ pending | |
| 5 | 5.2 SKILL.md 内容 | ⬜ pending | |
| 5 | 5.3 config.yaml | ⬜ pending | |
| 6 | 6.1 学习流程测试 | ⬜ pending | |
| 6 | 6.2 插件管理测试 | ⬜ pending | |
| 6 | 6.3 更新 README | ⬜ pending | |

---

## 附录: 快速参考

### 关键文件路径

```
# 插件管理
skill-manager/scripts/utils/frontmatter_parser.py  # Task 1.1
skill-manager/scripts/toggle_skill.py              # Task 1.2-1.4
skill-manager/scripts/health_check.py              # Task 1.5-1.8

# 学习器
github-to-skills/scripts/fetch_github_info.py      # Task 2.1 (修改)
github-to-skills/scripts/extract_patterns.py       # Task 2.2-2.5

# 自动进化
skill-evolution-manager/scripts/merge_evolution.py # Task 3.1 (修改)
skill-evolution-manager/scripts/smart_stitch.py    # Task 3.2 (修改)
skill-evolution-manager/scripts/trigger_detector.py # Task 3.3-3.4

# 跨平台
install.sh                                         # Task 4.1-4.3
uninstall.sh                                       # Task 4.4

# 协调器
evolving-agent/SKILL.md                            # Task 5.1-5.2
evolving-agent/config.yaml                         # Task 5.3

# 测试
tests/e2e_learning.sh                              # Task 6.1
tests/e2e_plugin_manager.sh                        # Task 6.2
```

### 常用测试命令

```bash
# 创建测试 skill 目录
mkdir -p /tmp/test-skills/test-skill
echo "---\nname: test\n---\n# Test" > /tmp/test-skills/test-skill/SKILL.md

# 清理测试目录
rm -rf /tmp/test-skills

# 运行 Python 单元测试
python -c "from module import func; assert func(input) == expected; print('PASS')"

# 检查文件内容
grep "keyword" file.md
```

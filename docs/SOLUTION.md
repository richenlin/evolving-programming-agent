# Evolving Programming Agent - 持续学习进化编程智能体

## 项目愿景

打造一个能够**持续学习、自我进化**的编程智能体，通过组合现有的四个 skill 组件，构建一个具备以下能力的 AI 编程助手：

1. **自主学习**：从 GitHub 仓库中学习新的编程技能和最佳实践
2. **持续进化**：从每次编程任务中提取经验，不断优化自身能力
3. **灵活管理**：以插件形式管理技能库，支持热启用/禁用
4. **跨平台支持**：兼容 Claude Code、OpenCode、Cursor 三大主流 AI 编程环境

---

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Evolving Agent (协调层)                              │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌──────────────┐  │
│  │ 学习触发器    │  │ 进化触发器    │  │ 健康检查器    │  │ 会话管理器   │  │
│  │ (GitHub URL   │  │ (任务完成后   │  │ (定期扫描     │  │ (上下文追踪  │  │
│  │  自动检测)    │  │  自动调用)    │  │  过期Skill)   │  │  状态持久化) │  │
│  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘  └──────┬───────┘  │
└──────────┼──────────────────┼──────────────────┼─────────────────┼──────────┘
           │                  │                  │                 │
           ▼                  ▼                  ▼                 ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ github-to-skills │ │skill-evolution-  │ │  skill-manager   │ │ programming-     │
│ (技术学习器)     │ │manager (进化器)  │ │  (插件管理器)    │ │ assistant (执行器)│
│                  │ │                  │ │                  │ │                  │
│ ・工具模式       │ │ ・经验提取       │ │ ・启用/禁用      │ │ ・完整模式       │
│ ・学习模式 [新]  │ │ ・JSON持久化     │ │ ・健康检查 [新]  │ │ ・简化模式       │
│ ・范式提取 [新]  │ │ ・智能缝合       │ │ ・自动更新 [新]  │ │ ・自动进化 [新]  │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
           │                  │                  │                 │
           └──────────────────┴──────────────────┴─────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
             ┌───────────┐     ┌───────────┐     ┌───────────┐
             │ OpenCode  │     │Claude Code│     │  Cursor   │
             └───────────┘     └───────────┘     └───────────┘
```

### 数据流架构

```
                     用户输入
                        │
                        ▼
            ┌───────────────────────┐
            │   输入分析器          │
            │   ├─ GitHub URL?      │───────▶ 学习流程
            │   ├─ 编程任务?        │───────▶ 执行流程
            │   └─ 管理命令?        │───────▶ 管理流程
            └───────────────────────┘
                                              
    学习流程                执行流程              管理流程
        │                      │                    │
        ▼                      ▼                    ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│fetch_github   │    │programming-   │    │skill-manager  │
│_info.py       │    │assistant      │    │               │
│               │    │执行编程任务    │    │启用/禁用/检查 │
└───────┬───────┘    └───────┬───────┘    └───────────────┘
        │                    │
        ▼                    ▼
┌───────────────┐    ┌───────────────┐
│extract_       │    │进化触发检查   │
│patterns.py    │    │               │
│分析代码范式   │    │是否有经验?    │
└───────┬───────┘    └───────┬───────┘
        │                    │
        ▼                    ▼
┌───────────────┐    ┌───────────────┐
│生成           │    │skill-         │
│knowledge-     │    │evolution-     │
│addon.md       │    │manager        │
│知识补丁       │    │提取并持久化   │
└───────┬───────┘    └───────────────┘
        │
        ▼
┌───────────────┐
│附加到         │
│programming-   │
│assistant      │
└───────────────┘
```

---

## 核心能力设计

### 能力一：GitHub 学习器 (Tech Learning Pipeline)

#### 设计目标
将 `github-to-skills` 从单一的"工具包装器"升级为双模式学习系统：
- **工具模式**（现有）：将 CLI 工具包装为可调用的 skill
- **学习模式**（新增）：从优秀开源项目中提取编程范式和最佳实践

#### 学习模式输出格式

```yaml
---
name: react-patterns-knowledge
type: knowledge-addon          # 新类型：知识补丁
target_skill: programming-assistant
source_repo: https://github.com/alan2207/bulletproof-react
source_hash: abc123...
created_at: 2026-01-23
---

# React 最佳实践 (来源: bulletproof-react)

## 项目结构模式

### Feature-Based 架构
```
src/
├── features/           # 按业务功能划分
│   ├── auth/
│   │   ├── api/       # 该 feature 的 API 调用
│   │   ├── components/# 该 feature 的组件
│   │   ├── hooks/     # 该 feature 的 hooks
│   │   └── types/     # 该 feature 的类型
│   └── dashboard/
├── components/         # 共享/通用组件
├── hooks/             # 共享 hooks
└── lib/               # 第三方库封装
```

## 代码规范

### 类型安全
- 使用 Zod 进行运行时类型校验
- API 响应必须经过 schema 验证

### 状态管理
- 服务端状态：React Query
- 客户端状态：Zustand (简单) / Redux Toolkit (复杂)

## 编程范式

### API 层设计
```typescript
// 标准 API 函数模式
export const getUser = (userId: string): Promise<User> => {
  return axios.get(`/users/${userId}`).then(res => userSchema.parse(res.data));
};
```

## 应用场景
当用户请求"创建 React 项目"或"重构 React 代码"时，自动应用这些范式。
```

#### 实现方案

**新增脚本**: `github-to-skills/scripts/extract_patterns.py`

```python
#!/usr/bin/env python3
"""
从 GitHub 仓库中提取编程范式和最佳实践
"""

import json
import sys
from pathlib import Path

def analyze_project_structure(readme: str, file_tree: list) -> dict:
    """分析项目结构模式"""
    patterns = {
        "architecture": [],
        "conventions": [],
        "best_practices": []
    }
    
    # 检测常见架构模式
    if any("features/" in f for f in file_tree):
        patterns["architecture"].append("Feature-Based Architecture")
    if any("components/" in f for f in file_tree):
        patterns["architecture"].append("Component-Based Design")
    if any("hooks/" in f for f in file_tree):
        patterns["conventions"].append("Custom Hooks Pattern")
    
    return patterns

def generate_knowledge_addon(repo_info: dict, patterns: dict) -> str:
    """生成 knowledge-addon 格式的 Markdown"""
    template = f"""---
name: {repo_info['name']}-knowledge
type: knowledge-addon
target_skill: programming-assistant
source_repo: {repo_info['url']}
source_hash: {repo_info['latest_hash']}
created_at: {repo_info.get('created_at', 'unknown')}
---

# {repo_info['name']} 学习笔记

## 项目架构
{chr(10).join(f"- {a}" for a in patterns.get('architecture', []))}

## 代码规范
{chr(10).join(f"- {c}" for c in patterns.get('conventions', []))}

## 最佳实践
{chr(10).join(f"- {b}" for b in patterns.get('best_practices', []))}

## 应用场景
当处理相关技术栈的项目时，自动参考这些范式。
"""
    return template

if __name__ == "__main__":
    # 从 stdin 读取 fetch_github_info.py 的输出
    repo_info = json.load(sys.stdin)
    
    # 这里应该调用 LLM 进行更智能的分析
    # 当前为简化实现
    patterns = analyze_project_structure(
        repo_info.get('readme', ''),
        repo_info.get('file_tree', [])
    )
    
    addon = generate_knowledge_addon(repo_info, patterns)
    print(addon)
```

**扩展 SKILL.md 触发逻辑**:

```markdown
## 使用场景

**工具模式触发**:
- `/github-to-skills <url>` - 包装为可调用工具
- "把这个仓库包装成 skill"

**学习模式触发** [新增]:
- `/learn <url>` - 学习编程范式
- "学习这个仓库的最佳实践"
- "从这个项目中提取代码规范"
```

---

### 能力二：自动进化机制 (Auto-Evolution)

#### 设计目标
在 `programming-assistant` 执行完编程任务后，自动检测是否存在值得保存的经验，并触发 `skill-evolution-manager` 进行持久化。

#### 进化触发条件

```
┌─────────────────────────────────────────────────────────┐
│                    进化触发条件检测                      │
├─────────────────────────────────────────────────────────┤
│ 1. 修复了复杂 Bug                                       │
│    - 连续尝试 > 1 次                                    │
│    - 涉及非显而易见的解决方案                            │
│                                                         │
│ 2. 发现了新的最佳实践                                   │
│    - 用户明确表示"这个方案更好"                          │
│    - 代码重构后性能/可读性提升                           │
│                                                         │
│ 3. 用户给出明确反馈                                     │
│    - "记住这个"                                         │
│    - "以后都这样做"                                      │
│    - "这个设置很重要"                                    │
│                                                         │
│ 4. 使用了非标准解决方案                                 │
│    - 特定环境的 workaround                              │
│    - 用户自定义的代码风格                                │
└─────────────────────────────────────────────────────────┘
```

#### 扩展 programming-assistant 的会话结束检查

在 `SKILL.md` 中添加自动进化配置：

```yaml
---
name: programming-assistant
# ... 其他配置 ...
evolution:
  auto_evolve: true           # 启用自动进化
  evolve_threshold: medium    # 触发阈值: low/medium/high
  silent_mode: true           # 静默模式，不打断用户流程
---
```

扩展会话结束检查流程：

```markdown
### 会话结束检查（扩展版）

每次会话结束前必须确保：

| 检查项 | 要求 |
|--------|------|
| 代码状态 | 可运行，无阻塞性错误 |
| Git 状态 | 所有变更已提交 |
| progress.txt | 已记录本次进展和下一步 |
| **[新增] 进化检查** | 检测是否有值得保存的经验 |

#### 进化检查流程

```
是否满足进化触发条件？
    │
    ├─ 是 → 调用 /evolve 命令
    │       ├─ 静默模式: 后台执行，不输出
    │       └─ 交互模式: 询问用户确认
    │
    └─ 否 → 正常结束会话
```
```

#### 进化数据结构增强

扩展 `evolution.json` 格式：

```json
{
  "preferences": [
    "用户偏好使用 pnpm 而非 npm",
    "代码注释使用中文"
  ],
  "fixes": [
    "macOS 上 node-gyp 需要先安装 Xcode CLI tools",
    "Windows WSL2 下文件监听需要 polling 模式"
  ],
  "custom_prompts": "每次提交代码前先运行 lint",
  "patterns": {
    "react": [
      "组件文件使用 PascalCase 命名",
      "hooks 文件以 use 开头"
    ],
    "api": [
      "所有 API 调用包装在 try-catch 中",
      "统一使用 axios 实例"
    ]
  },
  "context_triggers": {
    "when_creating_react_component": "使用函数式组件 + TypeScript",
    "when_writing_tests": "使用 Vitest + Testing Library"
  }
}
```

---

### 能力三：插件管理系统 (Plugin Manager)

#### 设计目标
将 `skill-manager` 升级为完整的插件管理系统，支持：
- 热启用/禁用 skill
- 健康检查和过期检测
- 自动更新提醒

#### 扩展命令

```bash
# 现有命令
/skill-manager check          # 检查更新
/skill-manager list           # 列出所有 skill
/skill-manager delete <name>  # 删除 skill

# 新增命令
/skill-manager enable <name>   # 启用 skill
/skill-manager disable <name>  # 禁用 skill (移到 .disabled/)
/skill-manager status          # 查看所有 skill 状态（含启用/禁用）
/skill-manager health          # 健康检查
/skill-manager auto-update     # 自动更新过期 skill
```

#### 健康检查机制

**新增脚本**: `skill-manager/scripts/health_check.py`

```python
#!/usr/bin/env python3
"""
Skill 健康检查器
检测过期、无效、依赖缺失的 skill
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

def check_skill_health(skill_dir: Path) -> dict:
    """检查单个 skill 的健康状态"""
    result = {
        "name": skill_dir.name,
        "status": "healthy",
        "issues": []
    }
    
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        result["status"] = "invalid"
        result["issues"].append("SKILL.md 不存在")
        return result
    
    # 解析 frontmatter
    content = skill_md.read_text()
    # ... 解析逻辑 ...
    
    # 检查 GitHub hash 是否过期
    if "github_url" in metadata:
        remote_hash = get_remote_hash(metadata["github_url"])
        if remote_hash != metadata.get("github_hash"):
            result["status"] = "outdated"
            result["issues"].append(f"版本过期: 本地 {metadata.get('github_hash', 'unknown')[:7]}, 远程 {remote_hash[:7]}")
    
    # 检查依赖
    if "dependencies" in metadata:
        for dep in metadata["dependencies"]:
            if not check_dependency(dep):
                result["status"] = "broken"
                result["issues"].append(f"依赖缺失: {dep}")
    
    # 检查 evolution.json 语法
    evolution_json = skill_dir / "evolution.json"
    if evolution_json.exists():
        try:
            json.loads(evolution_json.read_text())
        except json.JSONDecodeError as e:
            result["issues"].append(f"evolution.json 语法错误: {e}")
    
    return result

def main():
    skills_dir = Path(os.path.expanduser("~/.config/opencode/skill"))
    
    results = []
    for skill_dir in skills_dir.iterdir():
        if skill_dir.is_dir() and not skill_dir.name.startswith('.'):
            results.append(check_skill_health(skill_dir))
    
    # 输出报告
    print(json.dumps({
        "timestamp": datetime.now().isoformat(),
        "total": len(results),
        "healthy": sum(1 for r in results if r["status"] == "healthy"),
        "outdated": sum(1 for r in results if r["status"] == "outdated"),
        "broken": sum(1 for r in results if r["status"] == "broken"),
        "invalid": sum(1 for r in results if r["status"] == "invalid"),
        "details": results
    }, indent=2))

if __name__ == "__main__":
    main()
```

#### 启用/禁用机制

```
skills/
├── programming-assistant/     # 启用状态
├── github-to-skills/          # 启用状态
├── .disabled/                 # 禁用目录
│   └── deprecated-tool/       # 被禁用的 skill
└── .backup/                   # 备份目录
```

**新增脚本**: `skill-manager/scripts/toggle_skill.py`

```python
#!/usr/bin/env python3
"""启用/禁用 skill"""

import os
import sys
import shutil
from pathlib import Path

def enable_skill(skill_name: str, skills_dir: Path):
    """从 .disabled 移回主目录"""
    disabled_dir = skills_dir / ".disabled" / skill_name
    target_dir = skills_dir / skill_name
    
    if not disabled_dir.exists():
        print(f"Error: {skill_name} 未被禁用或不存在")
        return False
    
    shutil.move(str(disabled_dir), str(target_dir))
    print(f"已启用: {skill_name}")
    return True

def disable_skill(skill_name: str, skills_dir: Path):
    """移到 .disabled 目录"""
    source_dir = skills_dir / skill_name
    disabled_dir = skills_dir / ".disabled"
    
    if not source_dir.exists():
        print(f"Error: {skill_name} 不存在")
        return False
    
    disabled_dir.mkdir(exist_ok=True)
    target_dir = disabled_dir / skill_name
    shutil.move(str(source_dir), str(target_dir))
    print(f"已禁用: {skill_name}")
    return True
```

---

### 能力四：跨平台支持

#### 平台适配矩阵

| 平台 | Skill 路径 | MCP 配置路径 | 格式要求 |
|------|-----------|-------------|---------|
| OpenCode | `~/.config/opencode/skill/<name>/SKILL.md` | `~/.config/opencode/opencode.json` (mcp字段) | YAML frontmatter + Markdown |
| Claude Code | `~/.claude/skills/<name>/SKILL.md` | `~/.claude/claude_desktop_config.json` | YAML frontmatter + Markdown |
| Cursor | `~/.cursor/rules/<name>.md` | `~/.cursor/mcp.json` | 纯 Markdown (无frontmatter) |

#### 统一安装器设计

**文件**: `install.sh` (已存在，需扩展)

扩展功能：
1. 检测已安装的平台
2. 自动适配格式
3. 批量安装多个 skill
4. MCP 服务器自动配置

```bash
#!/bin/bash
# 使用示例

# 完整安装（推荐）
./install.sh --all --with-mcp

# 仅安装到 OpenCode
./install.sh --opencode --with-mcp

# 批量安装多个 skill
./install.sh --skills "programming-assistant,github-to-skills,skill-manager"

# 预览模式
./install.sh --dry-run --all
```

#### MCP 配置统一

所有平台共享相同的 MCP 服务器配置：

```json
{
  "mcpServers": {
    "context7": {
      "url": "https://mcp.context7.com/mcp"
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    }
  }
}
```

---

## 实现路线图

### Phase 1: 基础增强 (1-2 周)

```
Week 1:
├── [ ] 扩展 github-to-skills 支持学习模式
│   ├── [ ] 新增 extract_patterns.py
│   ├── [ ] 定义 knowledge-addon 格式
│   └── [ ] 更新 SKILL.md 触发逻辑
│
└── [ ] 扩展 skill-manager 为插件系统
    ├── [ ] 新增 health_check.py
    ├── [ ] 新增 toggle_skill.py
    └── [ ] 更新 SKILL.md 命令定义

Week 2:
├── [ ] 实现自动进化触发机制
│   ├── [ ] 定义进化触发条件
│   ├── [ ] 修改 programming-assistant 会话结束逻辑
│   └── [ ] 扩展 evolution.json 格式
│
└── [ ] 完善跨平台安装器
    ├── [ ] 扩展 install.sh 批量安装能力
    └── [ ] 统一 MCP 配置格式
```

### Phase 2: 集成测试 (1 周)

```
├── [ ] 端到端测试: GitHub URL → 学习 → 应用
├── [ ] 端到端测试: 编程任务 → 自动进化 → 验证持久化
├── [ ] 跨平台测试: OpenCode / Claude Code / Cursor
└── [ ] 编写用户文档和示例
```

### Phase 3: 高级功能 (2 周+)

```
├── [ ] LLM 增强的代码分析 (更智能的范式提取)
├── [ ] 知识图谱: 关联不同 knowledge-addon
├── [ ] 进化历史追溯和回滚
└── [ ] Web UI 管理界面 (可选)
```

---

## 文件结构规划

```
skills-evolution/
├── README.md                          # 项目总览
├── SOLUTION.md                        # 本设计文档
├── install.sh                         # 统一安装器 [扩展]
├── uninstall.sh                       # 统一卸载器
│
├── github-to-skills/
│   ├── SKILL.md                       # [修改] 增加学习模式
│   └── scripts/
│       ├── fetch_github_info.py
│       ├── create_github_skill.py
│       └── extract_patterns.py        # [新增] 范式提取
│
├── skill-manager/
│   ├── SKILL.md                       # [修改] 增加插件管理命令
│   └── scripts/
│       ├── scan_and_check.py
│       ├── update_helper.py
│       ├── list_skills.py
│       ├── delete_skill.py
│       ├── health_check.py            # [新增] 健康检查
│       └── toggle_skill.py            # [新增] 启用/禁用
│
├── skill-evolution-manager/
│   ├── SKILL.md
│   └── scripts/
│       ├── merge_evolution.py
│       ├── smart_stitch.py
│       └── align_all.py
│
├── programming-assistant-skill/
│   ├── SKILL.md                       # [修改] 增加自动进化配置
│   ├── install.sh
│   ├── uninstall.sh
│   └── templates/
│       ├── progress.txt
│       └── feature_list.json
│
└── evolving-agent/                    # [新增] 协调器
    ├── SKILL.md                       # 协调器主文件
    ├── config.yaml                    # 全局配置
    └── scripts/
        ├── orchestrator.py            # 协调调度
        ├── trigger_detector.py        # 触发检测
        └── session_manager.py         # 会话管理
```

---

## 使用场景示例

### 场景 1: 学习新框架

```
用户: 学习这个 React 项目的最佳实践
      https://github.com/alan2207/bulletproof-react

智能体:
1. 检测到 GitHub URL，触发学习流程
2. 运行 fetch_github_info.py 获取仓库信息
3. 运行 extract_patterns.py 分析代码结构
4. 生成 react-patterns-knowledge addon
5. 自动附加到 programming-assistant

输出: "已学习 bulletproof-react 的最佳实践，包括:
      - Feature-Based 架构
      - React Query 状态管理
      - Zod 类型校验
      下次创建 React 项目时将自动应用这些范式。"
```

### 场景 2: 自动进化

```
用户: 帮我修复这个 API 报错

智能体:
1. 分析问题，定位到跨域配置错误
2. 修复代码，验证通过
3. 检测到这是一个值得保存的经验:
   - 解决方案非显而易见
   - 涉及特定环境配置
4. 自动触发 /evolve
5. 将 "Vite 开发服务器需要配置 proxy 解决跨域" 写入 evolution.json

下次遇到类似问题时，智能体会主动提示这个解决方案。
```

### 场景 3: 插件管理

```
用户: /skill-manager health

输出:
┌─────────────────────────────────────────────────────────┐
│               Skill 健康检查报告                         │
├─────────────────────────────────────────────────────────┤
│ 总计: 5 个 skill                                        │
│ ✅ 健康: 3                                              │
│ ⚠️  过期: 1 (yt-dlp-tool)                               │
│ ❌ 损坏: 1 (deprecated-helper)                          │
├─────────────────────────────────────────────────────────┤
│ 建议操作:                                               │
│ 1. 运行 `/skill-manager update yt-dlp-tool` 更新       │
│ 2. 运行 `/skill-manager delete deprecated-helper` 清理 │
└─────────────────────────────────────────────────────────┘
```

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| LLM 分析不准确 | 学习到错误的范式 | 人工审核 + 置信度阈值 |
| 过度进化 | evolution.json 膨胀 | 定期清理 + 重要性排序 |
| 跨平台不兼容 | 某平台功能失效 | 充分测试 + 降级方案 |
| 自动触发误判 | 不必要的进化操作 | 可配置触发阈值 + 静默模式 |

---

## 总结

本方案通过组合和扩展现有的四个 skill 组件，构建了一个具备**自主学习、持续进化、灵活管理**能力的编程智能体。核心创新点包括：

1. **双模式学习器**：不仅包装工具，还能从优秀项目中学习编程范式
2. **自动进化机制**：无需人工干预，自动从编程任务中提取经验
3. **插件化管理**：灵活启用/禁用技能，自动检测过期和问题
4. **跨平台支持**：一次开发，三平台（Claude Code、OpenCode、Cursor）可用

通过这套系统，AI 编程助手将从"静态工具"进化为"持续学习的智能体"，能够不断积累经验、适应用户习惯、保持技术栈更新。

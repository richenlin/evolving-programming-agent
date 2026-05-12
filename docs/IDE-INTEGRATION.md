# IDE 集成方案：Python 离线部署 & Skill 强制遵循

> 面向基于 VSCode + Cline 开源代码二次开发的 AI 编程 IDE，将 evolving-programming-agent 集成为核心 skill。
>
> **关键约束**：
> 1. **运行时完全离线** — 用户机器无网络，所有资源必须随 IDE 安装包分发
> 2. **集成只在 build 期** — 联网下载、版本检测、资源拉取仅在 IDE 构建流水线中执行
> 3. **完整代码集成** — IDE build 期下载本 skill 完整代码 + 便携 Python + 离线 wheel，全部打包进安装包

---

## 0. 设计目标与架构总览

### 0.1 三层时间轴

```
─────────────────────────────────────────────────────────────────────────────
[本项目 Release Pipeline]    打 tag → 多平台预构建 → 上传 GitHub Release
                                  ▼
─────────────────────────────────────────────────────────────────────────────
[IDE Build Pipeline] (在线)   ① 拉取 skill 完整代码 (git/release)
                              ② 拉取便携 Python (python-build-standalone)
                              ③ 拉取离线 wheel (vendor/)
                              ④ 调用 pack_for_ide.py 校验+组装
                              ⑤ 产物固化进 IDE 安装包
                                  ▼
─────────────────────────────────────────────────────────────────────────────
[用户机器] (离线)             ⑥ 安装 IDE
                              ⑦ 首次启动：bootstrap.py --resolve（纯本地）
                              ⑧ Skill 注入 system prompt + Tool 硬约束
                              ⑨ 全程无网络
─────────────────────────────────────────────────────────────────────────────
```

### 0.2 双层分工（重新定义）

```
┌─────────────────────────────────────────────────────────────┐
│                    IDE 项目（集成层）                        │
│  Build 期：                                                  │
│    - 拉取本项目 release（含完整代码 + Python + vendor）       │
│    - 校验 cli_protocol 兼容性                                │
│    - 资源固化进安装包                                        │
│  运行时（离线）：                                             │
│    - System Prompt 注入                                      │
│    - Tool 硬约束（evolving_agent + 编辑工具拦截）             │
│    - UI（状态栏、任务面板）                                   │
└──────────────────────┬──────────────────────────────────────┘
                       │  Build 期契约：pack-for-ide 资源包
                       │  Runtime 契约：CLI Protocol v1（纯离线）
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           本项目（运行时层 - evolving-agent）                │
│  Release 期：                                                │
│    - GitHub Actions 多平台预构建                             │
│    - 产出：evolving-agent-<ver>-<platform>.tar.gz            │
│  对 IDE build 暴露：                                         │
│    - pack_for_ide.py：一键资源组装工具                       │
│    - manifest.json：完整性校验                              │
│  对运行时暴露：                                              │
│    - bootstrap.py（detect-only，无下载逻辑）                 │
│    - run.py：CLI 入口（version / meta / task / knowledge）   │
└─────────────────────────────────────────────────────────────┘
```

### 0.3 「迅速集成」的新定义

由于运行时离线，**「迅速」不再是「重启即生效」，而是「IDE build pipeline 跟上本项目最新版的成本极低」**。

| 本项目变更类型 | IDE 跟进流程 | 时效 |
|---|---|---|
| SKILL.md 文字 / agents 文档 | IDE 重新 build → 发新 IDE 版本 → 用户更新 | **下个 IDE release 周期** |
| 新增 run.py 子命令（兼容） | 同上，IDE 代码可不动 | **下个 IDE release 周期** |
| 破坏性变更（bump cli_protocol） | IDE 代码适配 + 发新版 | **1-2 天 + 下个 IDE release** |
| **IDE build 拉取本项目新版的人力成本** | 改一行 release 版本号 | **5 分钟** |

**关键**：本项目必须把「IDE build 拉取 + 集成」做成**一行命令**，这样 IDE pipeline 升级 skill 几乎零成本。

### 0.4 演进职责分工（重要 — 维护者请先读）

> 这一节定下两个仓库各自负责什么、谁不该碰什么。后续所有改动应在这个边界内进行。
> 历史背景：v1.0.0 时期 IDE 侧曾用正则做 prompt adapter，在 v1.1.0 通过 `--mode ide`
> 把适配责任收回到本仓库，**适配只在一个地方写**。

#### 双仓库职责

| 仓库 | 角色 | 维护内容 |
|---|---|---|
| **`evolving-programming-agent`**（本项目） | **唯一适配源** | 维护 multi-agent + IDE 两份 SKILL 变体（`SKILL.md` + `SKILL.ide.md`），通过 `run.py meta --mode {default,ide}` 同时服务多种集成方。所有内容/语法适配都在本仓库做完，不要让下游做转写。 |
| **`tiantacode`**（IDE 侧） | **纯消费方** | 通过 git submodule 引用本项目，运行 `npm run skill:prepare` 拉资源、`bridge.exec(['meta','--skill-content','--mode','ide'])` 取内容。**禁止**做正则转写、内容魔改、维护"自家版本"的 SKILL。 |

#### 升级路径（黄金路径）

skill 升级到新版本时，正确的端到端流程：

```bash
# ① 本仓库（evolving-programming-agent）
#    完成改动 → CHANGELOG → bump runtime.json 版本 → tag → push
git tag -a vX.Y.Z -m "..."
git push origin main vX.Y.Z

# ② IDE 仓库（tiantacode），单条命令拉新版
cd extensions/huashan-ai-code/vendor/evolving-agent
git fetch && git checkout vX.Y.Z
cd ../../../..
git add extensions/huashan-ai-code/vendor/evolving-agent
git commit -m "chore: bump evolving-agent submodule to vX.Y.Z"

# ③ 重新 prepare 资源（自动校验 cli_protocol 兼容）
npm run skill:prepare

# ④ build → 发版
npm run build:desktop
```

只要本项目守住 cli_protocol 兼容（patch / minor 不破坏），IDE 这条路径**不需要碰任何 TS 代码**。

#### 三条铁律

1. **`evolving-programming-agent` 是单一适配源**
   - 任何针对特定集成方的内容改写（如把 `调度 @coder` 改写为 IDE tool 调用）都在本仓库新增 / 修改对应 mode 的 skill 变体（如 `SKILL.ide.md`），**而不是**在下游做。
   - 新增第三种集成方（如未来某个新 IDE）时：本仓库新增 `SKILL.<mode>.md` + 在 `run.py meta --mode` 的 choices 加新值，下游永远只是读取。

2. **`tiantacode` 不修改 skill 内容**
   - PR 评审时如果发现 IDE 侧出现「正则替换 skill 文本」「魔改 SKILL.md 复制版」这类逻辑，应当 reject 并要求把改动反推到本项目。
   - IDE 唯一允许的「适配」是包装层（如 system prompt 的 `<EXTREMELY_IMPORTANT>` 外层标签），但**不能修改 skill 主体内容**。

3. **跟进 = 一行 submodule update**
   - 只要本项目 release 时守 semver + cli_protocol 兼容承诺，IDE 升级 skill 就只是「改 submodule pointer + commit + 重新 prepare」，零代码改动。
   - 例外（破坏性变更）必须 bump 到 major / 改 cli_protocol，**且本项目 CHANGELOG 中明确列出 IDE 侧需要的对应改动**——这时 IDE 才需要写代码。

---

## 1. 第一步：本项目改造（离线优先 + Build 友好）

### 1.1 新增文件清单

```
evolving-programming-agent/
├── runtime.json                    # 【新增】运行时声明
├── scripts/
│   ├── bootstrap.py                # 【新增】纯 detect，无下载
│   ├── pack_for_ide.py             # 【新增】IDE build 期一键打包工具
│   └── run.py                      # 已有，新增 meta / version 子命令
├── .github/workflows/
│   └── release.yml                 # 【新增】多平台预构建
└── docs/
    └── IDE-INTEGRATION.md          # 当前文档
```

### 1.2 `runtime.json`：唯一可信声明

```json
{
  "skill": {
    "name": "evolving-agent",
    "version": "1.2.0",
    "skill_md": "SKILL.md",
    "agents_dir": "agents/",
    "workflows_dir": "workflows/"
  },
  "python": {
    "min_version": "3.8",
    "recommended_version": "3.11",
    "portable": {
      "source": "python-build-standalone",
      "release_tag": "20240415",
      "downloads": {
        "linux-x86_64":   "https://github.com/astral-sh/python-build-standalone/releases/download/20240415/cpython-3.11.9+20240415-x86_64-unknown-linux-gnu-install_only.tar.gz",
        "linux-aarch64":  "https://github.com/astral-sh/python-build-standalone/releases/download/20240415/cpython-3.11.9+20240415-aarch64-unknown-linux-gnu-install_only.tar.gz",
        "darwin-x86_64":  "https://github.com/astral-sh/python-build-standalone/releases/download/20240415/cpython-3.11.9+20240415-x86_64-apple-darwin-install_only.tar.gz",
        "darwin-arm64":   "https://github.com/astral-sh/python-build-standalone/releases/download/20240415/cpython-3.11.9+20240415-aarch64-apple-darwin-install_only.tar.gz",
        "windows-x86_64": "https://github.com/astral-sh/python-build-standalone/releases/download/20240415/cpython-3.11.9+20240415-x86_64-pc-windows-msvc-install_only.tar.gz"
      },
      "checksums": {
        "linux-x86_64":   "sha256:...",
        "linux-aarch64":  "sha256:...",
        "darwin-x86_64":  "sha256:...",
        "darwin-arm64":   "sha256:...",
        "windows-x86_64": "sha256:..."
      }
    }
  },
  "dependencies": {
    "required": ["PyYAML>=6.0,<7.0"],
    "optional": ["jieba>=0.42,<1.0"]
  },
  "cli_protocol": {
    "version": "v1",
    "min_ide_version": "0.5.0"
  }
}
```

### 1.3 `scripts/bootstrap.py`：运行时 detect-only（无下载）

**设计变更**：删除原方案中的 `download_portable_python` 逻辑。运行时只能 detect 已经被 IDE build 期打包好的资源。

```python
"""
bootstrap.py — 运行时 Python 解析器（纯离线，无下载）

调用方式：
    python3 bootstrap.py --resolve     # 解析 Python 路径，输出 JSON
    python3 bootstrap.py --doctor      # 诊断当前环境

输出：
    {"status":"ok","python":"/path","python_version":"3.11.9","source":"portable","skill_root":"/path"}
"""
import json, os, sys, subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNTIME_JSON = os.path.join(PROJECT_ROOT, "runtime.json")

def detect_portable_python(skill_root):
    """检测 IDE build 期打包的便携 Python（与 skill 资源同目录）"""
    bin_paths = [
        os.path.join(skill_root, ".runtime/python/bin/python3"),  # mac/linux
        os.path.join(skill_root, ".runtime/python/python.exe"),   # windows
    ]
    for p in bin_paths:
        if os.path.exists(p):
            try:
                out = subprocess.check_output(
                    [p, "-c", "import sys; print('.'.join(map(str, sys.version_info[:3])))"],
                    timeout=5
                ).decode().strip()
                return {"path": p, "version": out, "source": "portable"}
            except Exception:
                pass
    return None

def detect_system_python(min_version="3.8"):
    """方案 B fallback：用户系统 Python（仅当 IDE 未打包便携 Python 时）"""
    candidates = ["python3.13", "python3.12", "python3.11", "python3.10",
                  "python3.9", "python3.8", "python3", "python"]
    for cmd in candidates:
        try:
            out = subprocess.check_output(
                [cmd, "-c", "import sys; print('.'.join(map(str, sys.version_info[:3])))"],
                stderr=subprocess.DEVNULL, timeout=5
            ).decode().strip()
            if tuple(map(int, out.split("."))) >= tuple(map(int, min_version.split("."))):
                return {"path": cmd, "version": out, "source": "system"}
        except Exception:
            continue
    return None

def resolve():
    cfg = json.load(open(RUNTIME_JSON))
    # 优先级：IDE 打包的便携 Python > 系统 Python（兜底）
    py = detect_portable_python(PROJECT_ROOT) \
         or detect_system_python(cfg["python"]["min_version"])
    if not py:
        return {
            "status": "error",
            "code": "PYTHON_NOT_FOUND",
            "message": "No Python found. IDE installation may be corrupted."
        }
    return {
        "status": "ok",
        "python": py["path"],
        "python_version": py["version"],
        "source": py["source"],
        "skill_root": PROJECT_ROOT,
    }

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--resolve", action="store_true")
    ap.add_argument("--doctor", action="store_true")
    args = ap.parse_args()
    print(json.dumps(resolve()))
    sys.exit(0 if resolve().get("status") == "ok" else 1)
```

### 1.4 `scripts/pack_for_ide.py`：IDE Build 期一键打包工具（核心）

这是本项目对 IDE build pipeline 暴露的**核心工具**。一行命令完成「下载便携 Python + 准备 vendor + 复制 skill 代码 + 生成 manifest」。

```python
"""
pack_for_ide.py — 为 IDE build pipeline 准备完整离线资源包

仅在 IDE build 期（联网环境）调用。

调用方式：
    python pack_for_ide.py \
        --output ./build-output/evolving-agent \
        --platform darwin-arm64 \
        --include-vendor \
        --include-portable-python

产出目录结构：
    <output>/
      ├── runtime.json               # 资源清单
      ├── SKILL.md
      ├── agents/
      ├── workflows/
      ├── scripts/                   # 含 bootstrap.py / run.py
      ├── .runtime/
      │   └── python/                # 便携 Python（已展开）
      ├── vendor/                    # 离线 wheel
      │   ├── PyYAML-*.whl
      │   └── jieba-*.whl
      └── manifest.json              # 完整性校验 + 版本元数据
"""
import json, os, sys, shutil, hashlib, urllib.request, tarfile, subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def copy_skill_code(output: Path):
    """复制 skill 源码到输出目录"""
    for item in ["SKILL.md", "runtime.json", "requirements.txt",
                 "requirements-optional.txt", "agents", "workflows",
                 "scripts", "references", "skills"]:
        src = PROJECT_ROOT / item
        if not src.exists():
            continue
        dst = output / item
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            shutil.copy2(src, dst)

def download_portable_python(output: Path, platform: str):
    """下载并解压便携 Python 到 .runtime/python/"""
    cfg = json.loads((PROJECT_ROOT / "runtime.json").read_text())
    url = cfg["python"]["portable"]["downloads"].get(platform)
    if not url:
        raise RuntimeError(f"Unsupported platform: {platform}")

    target = output / ".runtime"
    target.mkdir(parents=True, exist_ok=True)
    archive = target / "python.tar.gz"
    print(f"[pack] Downloading Python for {platform}...", file=sys.stderr)
    urllib.request.urlretrieve(url, archive)

    # 校验 sha256
    expected = cfg["python"]["portable"].get("checksums", {}).get(platform, "")
    if expected.startswith("sha256:"):
        h = hashlib.sha256()
        with open(archive, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        assert h.hexdigest() == expected[7:], f"Checksum mismatch for {platform}"

    print(f"[pack] Extracting...", file=sys.stderr)
    with tarfile.open(archive) as tar:
        tar.extractall(target)
    archive.unlink()

def download_vendor_wheels(output: Path, platform: str):
    """下载离线 wheel 包（多平台兼容）"""
    vendor = output / "vendor"
    vendor.mkdir(parents=True, exist_ok=True)
    requirements = PROJECT_ROOT / "requirements.txt"
    # 平台名映射到 pip --platform
    pip_platform_map = {
        "linux-x86_64":   "manylinux2014_x86_64",
        "linux-aarch64":  "manylinux2014_aarch64",
        "darwin-x86_64":  "macosx_10_9_x86_64",
        "darwin-arm64":   "macosx_11_0_arm64",
        "windows-x86_64": "win_amd64",
    }
    pip_plat = pip_platform_map[platform]
    print(f"[pack] Downloading wheels for {pip_plat}...", file=sys.stderr)
    subprocess.check_call([
        sys.executable, "-m", "pip", "download",
        "--dest", str(vendor),
        "--platform", pip_plat,
        "--only-binary=:all:",
        "--no-deps",
        "-r", str(requirements),
    ])

def generate_manifest(output: Path, platform: str):
    """生成 manifest.json：版本 + 文件清单 + checksum"""
    cfg = json.loads((PROJECT_ROOT / "runtime.json").read_text())
    files = []
    for root, _, names in os.walk(output):
        for n in names:
            if n == "manifest.json":
                continue
            p = Path(root) / n
            rel = p.relative_to(output)
            sha = hashlib.sha256(p.read_bytes()).hexdigest()
            files.append({"path": str(rel), "sha256": sha, "size": p.stat().st_size})
    manifest = {
        "skill_version":  cfg["skill"]["version"],
        "cli_protocol":   cfg["cli_protocol"]["version"],
        "min_ide_version": cfg["cli_protocol"]["min_ide_version"],
        "platform":       platform,
        "build_time":     subprocess.check_output(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"]).decode().strip(),
        "files":          files,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2))

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    ap.add_argument("--platform", required=True,
                    choices=["linux-x86_64","linux-aarch64",
                             "darwin-x86_64","darwin-arm64","windows-x86_64"])
    ap.add_argument("--include-vendor", action="store_true", default=True)
    ap.add_argument("--include-portable-python", action="store_true", default=True)
    args = ap.parse_args()

    output = Path(args.output).resolve()
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    copy_skill_code(output)
    if args.include_vendor:
        download_vendor_wheels(output, args.platform)
    if args.include_portable_python:
        download_portable_python(output, args.platform)
    generate_manifest(output, args.platform)

    print(f"[pack] OK: {output}", file=sys.stderr)
    print(json.dumps({"status":"ok","output":str(output),
                      "platform":args.platform}))

if __name__ == "__main__":
    main()
```

### 1.5 `run.py` 新增子命令

```python
def cmd_version(args):
    """供 IDE build 期校验兼容性"""
    cfg = json.load(open(os.path.join(PROJECT_ROOT, "runtime.json")))
    print(json.dumps({
        "skill_version":   cfg["skill"]["version"],
        "cli_protocol":    cfg["cli_protocol"]["version"],
        "min_ide_version": cfg["cli_protocol"]["min_ide_version"],
    }))

def cmd_meta(args):
    """暴露 skill 内容（供 IDE build 期固化进安装包）"""
    cfg = json.load(open(os.path.join(PROJECT_ROOT, "runtime.json")))
    if args.skill_content:
        result = {
            "skill_md": open(os.path.join(PROJECT_ROOT, cfg["skill"]["skill_md"])).read(),
            "agents":   {f.name: f.read_text()
                         for f in Path(PROJECT_ROOT, "agents").glob("*.md")},
            "workflows": {f.name: f.read_text()
                          for f in Path(PROJECT_ROOT, "workflows").glob("*.md")},
        }
    else:
        result = cfg
    print(json.dumps(result, ensure_ascii=False))

def cmd_verify(args):
    """运行时校验 manifest.json 完整性（防止安装包损坏）"""
    manifest = json.load(open(os.path.join(PROJECT_ROOT, "manifest.json")))
    errors = []
    for f in manifest["files"]:
        p = os.path.join(PROJECT_ROOT, f["path"])
        if not os.path.exists(p):
            errors.append(f"missing: {f['path']}")
            continue
        actual = hashlib.sha256(open(p,"rb").read()).hexdigest()
        if actual != f["sha256"]:
            errors.append(f"checksum mismatch: {f['path']}")
    print(json.dumps({"status":"ok" if not errors else "error","errors":errors}))
```

### 1.6 `.github/workflows/release.yml`：多平台预构建（关键）

让本项目每次打 tag 时**自动产出 5 个平台的预打包资源**，IDE build pipeline 直接下载 release 资源即可，不必自己跑 `pack_for_ide.py`。

```yaml
name: Release
on:
  push:
    tags: ['v*']
jobs:
  build-package:
    strategy:
      matrix:
        include:
          - platform: linux-x86_64
            runner:   ubuntu-latest
          - platform: linux-aarch64
            runner:   ubuntu-latest
          - platform: darwin-x86_64
            runner:   macos-13
          - platform: darwin-arm64
            runner:   macos-14
          - platform: windows-x86_64
            runner:   windows-latest
    runs-on: ${{ matrix.runner }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - name: Pack for IDE
        run: |
          python scripts/pack_for_ide.py \
            --output ./dist/evolving-agent-${{ matrix.platform }} \
            --platform ${{ matrix.platform }}
      - name: Compress
        run: |
          tar -czf evolving-agent-${{ matrix.platform }}.tar.gz \
            -C ./dist evolving-agent-${{ matrix.platform }}
      - uses: softprops/action-gh-release@v2
        with:
          files: evolving-agent-${{ matrix.platform }}.tar.gz
```

**对 IDE 的承诺**：每个 release 都有 5 个 `evolving-agent-<platform>.tar.gz`，开箱即用。

### 1.7 CLI Protocol v1 契约

| 命令 | 调用时机 | 是否联网 | 用途 |
|------|---------|---------|------|
| `pack_for_ide.py --output ... --platform ...` | IDE build 期 | ✅ 需要 | 一键打包资源 |
| `run.py version` | IDE build 期 + 运行时 | ❌ 离线 | 版本兼容校验 |
| `run.py verify` | 运行时启动 | ❌ 离线 | manifest 完整性校验 |
| `bootstrap.py --resolve` | 运行时启动 | ❌ 离线 | 解析 Python 路径 |
| `run.py meta --skill-content` | IDE build 期 | ❌ 离线 | 固化 skill 内容到安装包 |
| `run.py task status --json` | 运行时 | ❌ 离线 | 任务状态机查询 |
| `run.py task transition` | 运行时 | ❌ 离线 | 状态变更 |
| `run.py knowledge trigger` | 运行时 | ❌ 离线 | 知识检索 |

---

## 2. 第二步：IDE Build Pipeline 集成

目标：在 IDE 构建流水线中**一次性**拉取本项目所有资源、校验、固化。

### 2.1 IDE 仓库目录约定

```
<your-ide>/
├── package.json
├── build/
│   ├── fetch-skill.sh              # 【关键】Build 期资源拉取脚本
│   ├── verify-skill.sh             # Build 期版本校验
│   └── pack-installer.sh           # 最终打包安装器
├── resources/
│   └── evolving-agent/             # ← Build 期由 fetch-skill.sh 填充，git ignore
│       ├── runtime.json
│       ├── SKILL.md
│       ├── agents/
│       ├── workflows/
│       ├── scripts/
│       ├── .runtime/python/        # 便携 Python
│       ├── vendor/                 # 离线 wheel
│       └── manifest.json
└── src/
    ├── runtime/PythonBridge.ts
    ├── skill/SkillLoader.ts
    ├── prompts/system.ts
    ├── tools/EvolvingAgentTool.ts
    └── tools/EditToolGuard.ts
```

`resources/evolving-agent/` 列入 `.gitignore` — **它是 build 产物，不进 IDE 仓库**。

### 2.2 `build/fetch-skill.sh`：Build 期资源拉取

```sh
#!/usr/bin/env sh
# 在 IDE build pipeline 中（联网环境）执行
# 用法: ./build/fetch-skill.sh <skill-version> <platform>
#   e.g.  ./build/fetch-skill.sh v1.2.0 darwin-arm64

set -e

SKILL_VERSION="${1:-v1.2.0}"
PLATFORM="${2:-$(uname -s | tr A-Z a-z)-$(uname -m)}"
TARGET="resources/evolving-agent"
URL="https://github.com/YOUR_ORG/evolving-programming-agent/releases/download/${SKILL_VERSION}/evolving-agent-${PLATFORM}.tar.gz"

echo "[ide-build] Fetching skill ${SKILL_VERSION} for ${PLATFORM}..."
mkdir -p "$TARGET"
curl -fsSL "$URL" | tar -xz --strip-components=1 -C "$TARGET"

echo "[ide-build] Verifying manifest..."
SKILL_VER=$(node -e "console.log(require('./$TARGET/manifest.json').skill_version)")
CLI_PROTO=$(node -e "console.log(require('./$TARGET/manifest.json').cli_protocol)")
MIN_IDE=$(node -e "console.log(require('./$TARGET/manifest.json').min_ide_version)")

echo "[ide-build] OK: skill=$SKILL_VER cli=$CLI_PROTO min_ide=$MIN_IDE"
```

执行一次完成：①下载 release 包 ②解压到 resources/ ③读 manifest 打印版本。

### 2.3 `build/verify-skill.sh`：Build 期兼容性校验

```sh
#!/usr/bin/env sh
# 在 IDE pipeline 的 verify 阶段执行
# 不通过则 build 失败
set -e
TARGET="resources/evolving-agent"
IDE_VERSION=$(node -e "console.log(require('./package.json').version)")

REQUIRED_CLI="v1"
ACTUAL_CLI=$(node -e "console.log(require('./$TARGET/manifest.json').cli_protocol)")
MIN_IDE=$(node -e "console.log(require('./$TARGET/manifest.json').min_ide_version)")

if [ "$ACTUAL_CLI" != "$REQUIRED_CLI" ]; then
  echo "ERROR: skill cli_protocol=$ACTUAL_CLI, IDE 仅支持 $REQUIRED_CLI"
  exit 1
fi

if ! node -e "
  const semver = require('semver');
  if (semver.lt('$IDE_VERSION', '$MIN_IDE')) process.exit(1);
"; then
  echo "ERROR: IDE $IDE_VERSION < skill 要求的 $MIN_IDE"
  exit 1
fi

echo "[ide-build] Compatibility OK"
```

### 2.4 IDE `package.json` 集成脚本

```json
{
  "scripts": {
    "skill:fetch":  "./build/fetch-skill.sh v1.2.0 ${PLATFORM:-darwin-arm64}",
    "skill:verify": "./build/verify-skill.sh",
    "build:prepare": "npm run skill:fetch && npm run skill:verify",
    "build":        "npm run build:prepare && electron-builder",
    "build:all-platforms": "for p in linux-x86_64 darwin-arm64 windows-x86_64; do PLATFORM=$p npm run build; done"
  }
}
```

### 2.5 升级 skill 版本的人力成本（核心收益）

```diff
-  "skill:fetch": "./build/fetch-skill.sh v1.2.0 ..."
+  "skill:fetch": "./build/fetch-skill.sh v1.3.0 ..."
```

**改一行 + 重新 build = 升级完成**。这是 IDE 跟进本项目最新版的全部成本。

---

## 3. 第三步：IDE 运行时集成（纯离线）

### 3.1 总体启动流程

```
IDE 启动（用户机器，离线）
  ├─→ PythonBridge.init()
  │     ├─→ spawn bootstrap.py --resolve   （从安装包内的 .runtime/python 解析）
  │     └─→ 缓存 pythonBin / skillRoot
  │
  ├─→ SkillLoader.load()
  │     ├─→ run.py verify       校验 manifest 完整性（防安装包损坏）
  │     ├─→ run.py version      读本地 version（不联网）
  │     ├─→ run.py meta         读取 SKILL.md/agents/workflows
  │     └─→ 缓存 skillContent
  │
  ├─→ 注册 evolving_agent tool
  ├─→ Hook 编辑工具的 pre-execute
  └─→ UI 初始化（状态栏、任务面板）

用户提问
  ├─→ buildSystemPrompt(skill, userInstructions)
  ├─→ LLM 调用工具
  │     ├─ evolving_agent → PythonBridge.exec(['task','status','--json'])
  │     └─ write_file → preEditCheck() → exec(['task','status']) → 通过则放行
  └─→ 全程无网络
```

### 3.2 `PythonBridge`：纯离线 Python 调用层

```ts
// src/runtime/PythonBridge.ts
import { spawn, spawnSync } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

export class PythonBridge {
  private pythonBin!: string;
  private skillRoot!: string;

  /** 启动时调用一次。skillResourceDir 指向 IDE 安装包内的 resources/evolving-agent */
  async init(skillResourceDir: string) {
    const bootstrap = path.join(skillResourceDir, 'scripts/bootstrap.py');
    // 用安装包内的便携 Python 启动 bootstrap
    const portablePython = this.findPortablePython(skillResourceDir);

    const result = spawnSync(portablePython, [bootstrap, '--resolve'],
                              { encoding: 'utf8' });
    const info = JSON.parse(result.stdout);
    if (info.status !== 'ok') {
      throw new Error(`Skill bootstrap failed: ${info.message} (code=${info.code})`);
    }
    this.pythonBin = info.python;
    this.skillRoot = info.skill_root;

    // 启动时校验完整性（防安装包被篡改/损坏）
    const verify = await this.exec(['verify']);
    if (verify.status !== 'ok') {
      console.warn('[skill] integrity check failed:', verify.errors);
    }
  }

  async exec(args: string[]): Promise<any> {
    return new Promise((resolve, reject) => {
      const runPy = path.join(this.skillRoot, 'scripts/run.py');
      const proc  = spawn(this.pythonBin, [runPy, ...args]);
      let out = '', err = '';
      proc.stdout.on('data', d => out += d);
      proc.stderr.on('data', d => err += d);
      proc.on('close', code => {
        if (code !== 0) return reject(new Error(err || `exit ${code}`));
        try { resolve(JSON.parse(out)); } catch { resolve(out); }
      });
    });
  }

  private findPortablePython(skillResourceDir: string): string {
    const candidates = [
      path.join(skillResourceDir, '.runtime/python/bin/python3'),
      path.join(skillResourceDir, '.runtime/python/python.exe'),
    ];
    for (const p of candidates) if (fs.existsSync(p)) return p;
    throw new Error('Portable Python not found. IDE installation corrupted.');
  }
}
```

### 3.3 `SkillLoader`：启动时一次性加载

```ts
// src/skill/SkillLoader.ts
export class SkillLoader {
  skillContent!: { skill_md: string; agents: Record<string,string>; workflows: Record<string,string> };
  version!: { skill_version: string; cli_protocol: string; min_ide_version: string };

  async load(bridge: PythonBridge, ideVersion: string) {
    // 1. 读本地 version（不联网，因为 build 期已校验过，运行时只是显示）
    this.version = await bridge.exec(['version']);

    // 2. 防御性校验：如果用户绕过 IDE 升级机制替换了 skill 资源，运行时再校验一次
    if (this.version.cli_protocol !== 'v1') {
      throw new Error(`Skill cli_protocol=${this.version.cli_protocol} 不兼容 IDE`);
    }

    // 3. 一次性加载 skill 文档（缓存到内存）
    this.skillContent = await bridge.exec(['meta', '--skill-content']);
  }
}
```

### 3.4 System Prompt 注入

```ts
// src/prompts/system.ts
export function buildSystemPrompt(skill: SkillLoader, userInstructions: string): string {
  return `
<EXTREMELY_IMPORTANT>
You have a built-in core skill: evolving-agent (v${skill.version.skill_version}).
This skill is MANDATORY for ANY coding task and CANNOT be skipped.

To execute tasks, use the \`evolving_agent\` tool.
Direct shell calls to python/run.py are FORBIDDEN — always go through the tool.
</EXTREMELY_IMPORTANT>

# Skill Document
${skill.skillContent.skill_md}

# Agent Roles
${Object.entries(skill.skillContent.agents).map(([k,v]) => `## ${k}\n${v}`).join('\n\n')}

---

${userInstructions}
`;
}
```

### 3.5 Tool 硬约束

```ts
// src/tools/EvolvingAgentTool.ts —— LLM 操作 skill 的唯一入口
export const evolvingAgentTool = {
  name: 'evolving_agent',
  description: 'MANDATORY entry for all coding tasks. Manages task state machine and knowledge base.',
  input_schema: {
    type: 'object',
    properties: {
      action: { type: 'string',
                enum: ['task_status','task_create','task_transition',
                       'knowledge_query','knowledge_store','meta'] },
      args:   { type: 'object' }
    },
    required: ['action']
  },
  async execute(input: any, ctx: { bridge: PythonBridge }) {
    const argv = mapActionToCli(input.action, input.args || {});
    return await ctx.bridge.exec(argv);
  }
};

function mapActionToCli(action: string, args: any): string[] {
  switch (action) {
    case 'task_status':     return ['task','status','--json'];
    case 'task_create':     return ['task','create','--description', args.description];
    case 'task_transition': return ['task','transition',
                                     '--task-id', args.task_id,
                                     '--status',  args.status,
                                     '--actor',   args.actor || 'coder'];
    case 'knowledge_query': return ['knowledge','trigger',
                                     '--input', args.input,
                                     '--format', args.format || 'context'];
    default: throw new Error(`Unknown action: ${action}`);
  }
}
```

```ts
// src/tools/EditToolGuard.ts —— 拦截编辑工具，物理硬约束
export async function preEditCheck(filePath: string, ctx: { bridge: PythonBridge }) {
  const status = await ctx.bridge.exec(['task','status','--json']);
  if (!status.has_active_session) {
    throw new ToolError(
      `No active task session. Call evolving_agent(action='task_create') first.`
    );
  }
  if (!status.current_task || status.current_task.status !== 'in_progress') {
    throw new ToolError(
      `Current task not in_progress. Call evolving_agent(action='task_transition', ` +
      `args={task_id:'${status.current?.id}', status:'in_progress'}) first.`
    );
  }
}

// 在 Cline 的工具注册处挂钩
['write_file','apply_diff','replace_in_file'].forEach(name => {
  const orig = tools[name].execute;
  tools[name].execute = async (input, ctx) => {
    await preEditCheck(input.path, ctx);
    return orig(input, ctx);
  };
});
```

**效果**：LLM 跳过 evolving_agent 直接调 write_file → ToolError → LLM 看到错误 → 被迫先走状态机。**离线 + 物理硬约束**双重保障。

---

## 4. 升级流转机制（Build 期）

> 实际落地（v1.1.0+）采用 git submodule 方式直接引用，**取代了**早期设想的
> 「IDE 从 GitHub Release 下载平台 tar.gz」流程。Submodule 锁定 commit hash，
> tag 只是辅助参考；这样不依赖 release artifact 在线可用，且对私有部署更友好。

### 4.1 角色与流程

```
[本项目维护者]                              evolving-programming-agent
  ① 改代码 + 更新 CHANGELOG（三栏分类）
  ② bump runtime.json 中的 skill.version
  ③ git tag -a vX.Y.Z + git push origin main vX.Y.Z
                                           ▼
[IDE 维护者]                                tiantacode
  ④ 看本项目 CHANGELOG，决定升级
  ⑤ submodule 一行升级：
        cd extensions/huashan-ai-code/vendor/evolving-agent
        git fetch && git checkout vX.Y.Z
  ⑥ 主仓库 commit submodule pointer：
        git add <submodule path>
        git commit -m "chore: bump evolving-agent to vX.Y.Z"
  ⑦ npm run skill:prepare（自动跑 verify，cli_protocol 不兼容则 build red）
  ⑧ npm run build:desktop → 出 IDE 安装包
                                           ▼
[最终用户]
  ⑨ IDE 自动更新（或手动下载）
  ⑩ 离线启动，新 skill 立即生效
```

⭐ 黄金路径：第 ⑤⑥⑦ 步合计 **5 分钟人工时间**。如果 cli_protocol 没破坏，**IDE 侧不需要改任何 TS 代码**。

#### 提醒：submodule pointer 必须能从远端访问

升级 submodule pointer 后 push 主仓库前，**确认 tag 已 push 到本项目远端**：

```bash
git ls-remote --tags origin | grep vX.Y.Z
# 必须有命中；否则其他 clone 主仓库的人执行 git submodule update --init 会失败
```

CI 中可加一步 `git ls-remote` 校验作为 release blocker。

### 4.2 本项目的发布纪律

为了让 IDE 安心升级，本项目必须保证：

1. **Semver 严格执行**
   - `1.2.x` patch：仅修 bug，IDE 可盲升
   - `1.x.0` minor：兼容增强（增字段/子命令），IDE 可盲升
   - `2.0.0` major：破坏 cli_protocol，IDE 必须适配
2. **每个 tag 自动产出 5 平台 release 资源**（GitHub Actions 已配置）
3. **CHANGELOG.md** 强制三栏分类：
   - `Skill changes`：影响 SKILL.md / agents 文档（IDE 只需重新 build）
   - `CLI changes`：run.py 子命令变化（IDE 可能需要更新 mapActionToCli）
   - `Breaking`：必须 bump cli_protocol
4. **CI 兼容性守护**：PR 修改 run.py 接口未 bump cli_protocol → CI 红
5. **runtime.json + manifest.json 是双层事实源**：源仓库（runtime.json）+ 打包后（manifest.json）

### 4.3 跟进速度分级（实测）

| 本项目变更类型 | IDE 跟进动作 | 人工时间 | 端到端 |
|---|---|---|---|
| SKILL.md / SKILL.ide.md / agents 文档调整 | `git submodule update --remote` + commit + `npm run skill:prepare` | **5 分钟** | + 1 个 IDE release 周期 |
| 新增 run.py 子命令 / 字段（兼容） | 同上；如需用新功能再加 mapActionToCli 一行 | **5–30 分钟** | + 1 个 IDE release 周期 |
| 破坏性变更（cli_protocol bump） | IDE 代码适配 + 重新发版 | **1–2 天** | + 1 个 IDE release 周期 |

> **历史对照**：v1.0.0 时期 IDE 侧维护着一份 `SkillLoader.adaptForIDE()` 用正则把
> 「调度 @coder」转写成 tool 调用，约 80 行代码 + 每次本项目改 SKILL.md 句法都可能
> 漏抓。v1.1.0 引入 `SKILL.ide.md` + `meta --mode ide` 后，IDE 侧 -54 行，**适配负担
> 完全转移到本项目**，跟进时间从「半小时盯改正则」变成「git submodule update」。

---

## 5. 验收清单

### 本项目侧

- [ ] `runtime.json` 创建，含 `python.portable.downloads` + `cli_protocol` + checksums
- [ ] `scripts/bootstrap.py` 实现 `--resolve / --doctor`（**纯 detect，无下载**）
- [ ] `scripts/pack_for_ide.py` 实现一键打包（IDE build 期专用）
- [ ] `run.py` 新增 `version` / `meta` / `verify` 子命令
- [ ] `.github/workflows/release.yml` 多平台预构建（5 个平台）
- [ ] CI 增加 cli_protocol 兼容性检查
- [ ] CHANGELOG 维护规范（三栏分类）

### IDE 侧

- [ ] git submodule 引用本项目（`extensions/huashan-ai-code/vendor/evolving-agent`），URL 指向正式 git remote 而非 file://
- [ ] `scripts-build/prepare-skill.sh`：调用 submodule 内 `pack_for_ide.py` 产出资源 + 内嵌 verify（cli_protocol + min_ide_version 兼容性校验）
- [ ] `package.json` 增加 `skill:prepare` 脚本（不再分 fetch / verify）
- [ ] `resources/evolving-agent/` 加入 `.gitignore`，submodule 路径**不要** ignore
- [ ] esbuild plugin 把资源固化到 `dist/evolving-agent/`，**注意** `fs.cpSync({verbatimSymlinks: true})` 保留便携 Python 的相对 symlink
- [ ] `PythonBridge`：仅 detect，不下载
- [ ] `SkillLoader`：启动时 verify + 调 `bridge.exec(['meta','--skill-content','--mode','ide'])` 一行加载 IDE 适配版（**不要**自己写正则转写）
- [ ] `system.ts` 把 SKILL.ide.md 内容注入 prompt，外层简单 `<EXTREMELY_IMPORTANT>` 标签即可（SKILL.ide.md 自带 `<EVOLVING_AGENT_IDE_MODE>` banner）
- [ ] `EvolvingAgentTool` + `EditToolGuard` 实现 Tool 硬约束
- [ ] `verify-pack-layout.sh` 防回归：确保便携 Python 不进任何 asar archive

### 离线场景验证

- [ ] **物理断网**测试：拔网线后 IDE 启动 + 完整跑通编程任务
- [ ] **故意删除便携 Python**：bootstrap.py 应报错 `PYTHON_NOT_FOUND`
- [ ] **故意篡改 skill 文件**：`run.py verify` 应检测到 checksum 不一致
- [ ] **LLM 跳过 evolving_agent**：直接 write_file 应被拦截并返回 ToolError
- [ ] **本项目 bump 到 vX.Y.Z**：submodule update + commit → `npm run skill:prepare` 自动校验 → build 通过
- [ ] **故意降低 IDE 版本**：低于 min_ide_version 时 `prepare-skill.sh` 内嵌的 verify 应失败

---

## 6. 关键决策回顾

| 决策点 | 选择 | 原因 |
|-------|------|------|
| 运行时是否允许联网 | **否** | 用户场景明确要求 |
| 便携 Python 在哪一层下载 | **IDE build 期** | 运行时离线 |
| 资源拉取方式 | **git submodule（实际落地）** | 锁 commit hash 比 tag 更确定；不依赖 release artifact 在线可用；私有部署友好。早期设计的 GitHub Release tar.gz 路径已不再使用 |
| skill 文档同步速度 | 跟随 IDE release 周期 | 运行时无网络，无法热更 |
| 集成升级成本目标 | **一行 `git submodule update`** | 通过 prepare-skill.sh + cli_protocol 兼容承诺实现 |
| **多平台 skill 适配源** | **本项目唯一** | v1.1.0 起新增 `SKILL.ide.md` + `meta --mode ide`；IDE 侧零正则转写。新增集成方时也在本项目加 mode，下游永远只读取 |
| Tool 拦截层级 | **IDE 主进程** | 物理硬约束，LLM 无法绕过 |
| 完整性校验 | **manifest.json + run.py verify** | 防止安装包损坏/篡改 |
| Symlink 处理 | **本项目 `shutil.copytree(symlinks=True)` + IDE `fs.cpSync({verbatimSymlinks: true})`** | python-build-standalone 含相对 symlink 链；默认行为会解引用为绝对路径，导致下游重复 copy 时 EINVAL |

---

## 7. 工作量估算

| 阶段 | 任务 | 估算 |
|------|------|------|
| **本项目** | runtime.json + bootstrap.py（detect-only） | 0.5 天 |
| | pack_for_ide.py | 1 天 |
| | run.py 新增 version/meta/verify | 0.5 天 |
| | GitHub Actions release.yml | 0.5 天 |
| | 文档 + 测试 | 1 天 |
| | **小计** | **3.5 天** |
| **IDE 侧** | build/fetch-skill.sh + verify-skill.sh | 0.5 天 |
| | PythonBridge + SkillLoader | 1 天 |
| | System prompt 注入 | 0.5 天 |
| | EvolvingAgentTool + EditToolGuard | 1 天 |
| | UI（状态栏 + 任务面板） | 1.5 天 |
| | 联调 + 离线测试 | 1.5 天 |
| | **小计** | **6 天** |
| **总计** | | **~10 人天** |

---

## 参考资料

- [python-build-standalone（Astral 维护）](https://github.com/astral-sh/python-build-standalone) — 便携 Python 发行版
- [pip download 离线打包](https://pip.pypa.io/en/stable/cli/pip_download/) — vendor wheel 准备
- [Cline 自定义指令文档](https://docs.cline.bot/features/custom-instructions) — IDE 注入参考
- [GitHub Actions Release Workflow](https://docs.github.com/en/actions/publishing-packages) — 多平台预构建
- 本项目入口：`scripts/run.py`，子命令清单见 `.opencode/references/commands.md`

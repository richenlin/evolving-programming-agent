#!/bin/bash
################################################################################
# Evolving Programming Agent - 统一安装器
#
# 功能:
#   安装 evolving-agent skill
#   创建知识数据目录
#   支持 OpenCode / Claude Code (Cursor 自动共享)
#
# 使用方法:
#   ./install.sh --all                    # 安装所有 skill
#   ./install.sh --opencode               # 仅安装到 OpenCode
#   ./install.sh --claude-code            # 仅安装到 Claude Code (Cursor 也会使用)
#   ./install.sh --skills "skill1,skill2" # 指定要安装的 skill
#   ./install.sh --china                  # 国内镜像：PyPI（清华）+ HuggingFace（hf-mirror），加速 jieba/BGE
#   ./install.sh --mirror <url>           # 使用指定 pip 镜像 URL

#   ./install.sh --dry-run                # 预览模式
#   ./install.sh --help                   # 显示完整帮助
#
# 示例:
#   ./install.sh --all --china            # 全部安装并走国内镜像（含 jieba + BGE 向量）
################################################################################

set -euo pipefail

################################################################################
# 配置常量
################################################################################

# 脚本所在目录和项目根目录
_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${_SCRIPT_DIR}/.." && pwd)"
# shellcheck source=lib/agents.sh
source "${_SCRIPT_DIR}/lib/agents.sh"
# shellcheck source=lib/mirrors.sh
source "${_SCRIPT_DIR}/lib/mirrors.sh"
# shellcheck source=lib/shared-runtime.sh
source "${_SCRIPT_DIR}/lib/shared-runtime.sh"
SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
VERSION="2.0.0"

# 技能列表
declare -a ALL_SKILLS=(
    "evolving-agent"
)

# 路径配置
OPENCODE_SKILLS_DIR="$HOME/.config/opencode/skills"
OPENCODE_COMMAND_DIR="$HOME/.config/opencode/command"
OPENCODE_AGENTS_DIR="$HOME/.config/opencode/agents"   # OpenCode 原生 agent 目录
CLAUDE_CODE_SKILLS_DIR="$HOME/.claude/skills"
CURSOR_SKILLS_DIR="$HOME/.agents/skills"              # Cursor agent skills 目录
OPENCLAW_SKILLS_DIR="$HOME/.openclaw/skills"          # OpenClaw skills 目录
HERMES_SKILLS_DIR="$HOME/.hermes/skills"              # Hermes Agent skills 目录

# 共享运行时与知识库（跨平台唯一副本，见 docs/MULTI-PLATFORM-SHARE-DESIGN.md）
# SHARED_CODEGRAPH_DIR / EVOLVING_AGENT_HOME 定义于 lib/shared-runtime.sh
SHARED_KNOWLEDGE_DIR="${SHARED_CODEGRAPH_DIR}"
GLOBAL_AGENT_ENV="${LEGACY_AGENT_ENV}"
DEFAULT_LOCAL_EMBED_MODEL="BAAI/bge-small-zh-v1.5"

# 国内 pip / HuggingFace 镜像（--china 时生效；见 scripts/lib/mirrors.sh）

# Agent 源目录（相对于 PROJECT_ROOT）
AGENTS_SRC_DIR="evolving-agent/agents"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# sudo 确认状态（全局）
sudo_confirmed=false

################################################################################
# 辅助函数
################################################################################

info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

separator() {
    echo "========================================================================"
}

# 检查是否需要 sudo 权限
needs_sudo() {
    local path="$1"
    
    # 如果路径不存在，检查父目录
    if [ ! -e "$path" ]; then
        local parent_dir=$(dirname "$path")
        if [ -d "$parent_dir" ] && [ ! -w "$parent_dir" ]; then
            return 0  # 需要 sudo
        fi
        return 1  # 不需要 sudo
    fi
    
    # 如果路径存在但不可写
    if [ ! -w "$path" ]; then
        return 0  # 需要 sudo
    fi
    
    # 检查目录内是否有不可写的文件
    if [ -d "$path" ]; then
        local non_writable=$(find "$path" -maxdepth 2 ! -writable 2>/dev/null | head -1)
        if [ -n "$non_writable" ]; then
            return 0  # 需要 sudo
        fi
    fi
    
    return 1  # 不需要 sudo
}

# 带 sudo 检测的命令执行
run_cmd() {
    local cmd="$1"
    local path="$2"
    
    if needs_sudo "$path"; then
        if [ "${sudo_confirmed:-false}" != "true" ]; then
            warn "检测到需要管理员权限来写入: $path"
            # 非交互模式：无法获取 sudo 确认，跳过
            if [ ! -t 0 ]; then
                error "非交互模式下无法获取 sudo 权限，跳过: $path"
                return 1
            fi
            echo -e "${YELLOW}某些文件/目录需要 sudo 权限才能操作${NC}"
            read -p "是否使用 sudo 继续? [y/N]: " confirm
            if [[ "$confirm" =~ ^[Yy]$ ]]; then
                sudo_confirmed=true
                # 预先获取 sudo 权限
                sudo -v
            else
                error "用户取消，跳过需要 sudo 的操作"
                return 1
            fi
        fi
        eval "sudo $cmd"
    else
        eval "$cmd"
    fi
}

# 带 sudo 检测的目录创建
ensure_dir() {
    local dir="$1"
    if [ ! -d "$dir" ]; then
        run_cmd "mkdir -p '$dir'" "$dir"
    fi
}

# 带 sudo 检测的复制（使用 rsync 或 cp）
# .venv 由共享运行时管理（lib/shared-runtime.sh），复制 skill 时始终排除
safe_copy() {
    local src="$1"
    local dst="$2"

    # 检查 rsync 是否可用
    if command -v rsync &> /dev/null; then
        # 使用 rsync（推荐，支持 --delete 清理旧文件）
        # 确保 src 以 / 结尾（rsync 要求）
        if [[ ! "$src" =~ /$ ]]; then
            src="${src}/"
        fi

        run_cmd "rsync -av --delete --exclude='.venv' '$src' '$dst'" "$dst"
    else
        # Fallback: 使用 cp
        warn "rsync 不可用，使用 cp（可能无法完全清理旧文件）"

        # 删除目标中除 .venv 外的内容
        if [ -d "$dst" ]; then
            run_cmd "find '$dst' -mindepth 1 -maxdepth 1 ! -name '.venv' -exec rm -rf {} +" "$dst"
        fi

        # 确保目标目录存在
        run_cmd "mkdir -p '$dst'" "$dst"

        # 复制源目录内容
        run_cmd "cp -r '$src'/* '$dst'/" "$dst"
    fi
}

################################################################################
# 版本文件 & Git Hook
################################################################################

# 刷新 evolving-agent/scripts/VERSION 为当前 git commit hash
update_version_file() {
    local version_file="${PROJECT_ROOT}/evolving-agent/scripts/VERSION"

    if [ "${dry_run}" = true ]; then
        info "DRY-RUN: 将刷新 evolving-agent/scripts/VERSION"
        return 0
    fi

    if git -C "${PROJECT_ROOT}" rev-parse --short HEAD > "${version_file}" 2>/dev/null; then
        success "VERSION 已更新: $(cat "${version_file}")"
    else
        warn "无法获取 git commit hash，VERSION 文件保持不变"
    fi
}

# 安装 post-commit hook，每次提交后自动更新 VERSION
# 幂等：已包含同名 marker 则跳过；已有其他 hook 内容则追加而非覆盖
install_git_hook() {
    local hook_file="${PROJECT_ROOT}/.git/hooks/post-commit"
    local marker="# evolving-agent: update VERSION"

    if [ "${dry_run}" = true ]; then
        info "DRY-RUN: 将安装 post-commit hook 到 ${hook_file}"
        return 0
    fi

    if [ ! -d "${PROJECT_ROOT}/.git/hooks" ]; then
        warn "未找到 .git/hooks 目录，跳过 hook 安装"
        return 0
    fi

    # 已包含 marker，说明本 hook 已安装，跳过
    if [ -f "${hook_file}" ] && grep -qF "${marker}" "${hook_file}"; then
        info "post-commit hook 已存在，无需重复安装"
        return 0
    fi

    # 文件不存在时写入 shebang；已存在（其他 hook）则直接追加
    if [ ! -f "${hook_file}" ]; then
        echo '#!/bin/bash' > "${hook_file}"
    fi

    cat >> "${hook_file}" << EOF

${marker}
REPO_ROOT="\$(git rev-parse --show-toplevel)"
VERSION_FILE="\$REPO_ROOT/evolving-agent/scripts/VERSION"
git rev-parse --short HEAD > "\$VERSION_FILE"
echo "[post-commit] VERSION updated: \$(cat \$VERSION_FILE)"
EOF

    chmod +x "${hook_file}"
    success "post-commit hook 已安装: ${hook_file}"
}

################################################################################
# 安装函数
################################################################################

install_to_opencode() {
    local skill_name="$1"
    local src_dir="${PROJECT_ROOT}/${skill_name}"
    local dst_dir="${OPENCODE_SKILLS_DIR}/${skill_name}"

    if [ "${dry_run}" = true ]; then
        info "DRY-RUN: 将安装 ${skill_name} 到 OpenCode"
        return 0
    fi

    ensure_dir "${OPENCODE_SKILLS_DIR}" || return 1
    
    # 如果目标已存在，先删除
    if [ -e "${dst_dir}" ]; then
        run_cmd "rm -rf '$dst_dir'" "$dst_dir" || return 1
    fi
    
    safe_copy "${src_dir}" "${dst_dir}" || return 1
    success "已安装: ${skill_name} -> ${dst_dir}"
}

install_to_claude_code() {
    local skill_name="$1"
    local src_dir="${PROJECT_ROOT}/${skill_name}"
    local dst_dir="${CLAUDE_CODE_SKILLS_DIR}/${skill_name}"

    if [ "${dry_run}" = true ]; then
        info "DRY-RUN: 将安装 ${skill_name} 到 Claude Code"
        return 0
    fi

    ensure_dir "${CLAUDE_CODE_SKILLS_DIR}" || return 1
    
    # 如果目标已存在，先删除
    if [ -e "${dst_dir}" ]; then
        run_cmd "rm -rf '$dst_dir'" "$dst_dir" || return 1
    fi
    
    safe_copy "${src_dir}" "${dst_dir}" || return 1
    success "已安装: ${skill_name} -> ${dst_dir}"
}

install_to_cursor() {
    local skill_name="$1"
    local src_dir="${PROJECT_ROOT}/${skill_name}"
    local dst_dir="${CURSOR_SKILLS_DIR}/${skill_name}"

    if [ "${dry_run}" = true ]; then
        info "DRY-RUN: 将安装 ${skill_name} 到 Cursor (~/.agents/skills/)"
        return 0
    fi

    ensure_dir "${CURSOR_SKILLS_DIR}" || return 1

    # 如果目标已存在，先删除
    if [ -e "${dst_dir}" ]; then
        run_cmd "rm -rf '$dst_dir'" "$dst_dir" || return 1
    fi

    safe_copy "${src_dir}" "${dst_dir}" || return 1
    success "已安装: ${skill_name} -> ${dst_dir}"
}

install_to_openclaw() {
    local skill_name="$1"
    local src_dir="${PROJECT_ROOT}/${skill_name}"
    local dst_dir="${OPENCLAW_SKILLS_DIR}/${skill_name}"

    if [ "${dry_run}" = true ]; then
        info "DRY-RUN: 将安装 ${skill_name} 到 OpenClaw (~/.openclaw/skills/)"
        return 0
    fi

    ensure_dir "${OPENCLAW_SKILLS_DIR}" || return 1

    # 如果目标已存在，先删除
    if [ -e "${dst_dir}" ]; then
        run_cmd "rm -rf '$dst_dir'" "$dst_dir" || return 1
    fi

    safe_copy "${src_dir}" "${dst_dir}" || return 1
    success "已安装: ${skill_name} -> ${dst_dir}"
}

install_to_hermes() {
    local skill_name="$1"
    local src_dir="${PROJECT_ROOT}/${skill_name}"
    local dst_dir="${HERMES_SKILLS_DIR}/${skill_name}"

    if [ "${dry_run}" = true ]; then
        info "DRY-RUN: 将安装 ${skill_name} 到 Hermes Agent (~/.hermes/skills/)"
        return 0
    fi

    ensure_dir "${HERMES_SKILLS_DIR}" || return 1

    if [ -e "${dst_dir}" ]; then
        run_cmd "rm -rf '$dst_dir'" "$dst_dir" || return 1
    fi

    safe_copy "${src_dir}" "${dst_dir}" || return 1
    success "已安装: ${skill_name} -> ${dst_dir}"
}

# 安装 OpenCode 原生 Agent 文件
# OpenCode 支持 ~/.config/opencode/agents/ 目录，agent 文件直接放置于此
# Claude Code 通过 Task tool spawn subagent 调度，agent 文件随 skill 复制，作为 subagent prompt
install_opencode_agents() {
    local src_dir="${PROJECT_ROOT}/${AGENTS_SRC_DIR}"
    local dst_dir="${OPENCODE_AGENTS_DIR}"

    if [ "${dry_run}" = true ]; then
        info "DRY-RUN: 将安装 agent 文件到 OpenCode agents 目录: ${dst_dir}"
        if [ -d "${src_dir}" ]; then
            for agent_file in "${src_dir}"/*.md; do
                if [ -f "${agent_file}" ]; then
                    info "  DRY-RUN: ${agent_file} -> ${dst_dir}/$(basename "${agent_file}")"
                fi
            done
        fi
        local purged
        purged=$(purge_deprecated_opencode_agents "${dst_dir}" true)
        if [ "${purged}" -gt 0 ]; then
            info "  DRY-RUN: 将清理 ${purged} 个废弃 agent 文件"
        fi
        return 0
    fi

    # 检查源目录是否存在
    if [ ! -d "${src_dir}" ]; then
        warn "Agent 目录不存在: ${src_dir}，跳过"
        return 0
    fi

    ensure_dir "${dst_dir}" || return 1

    local installed_count=0
    for agent_file in "${src_dir}"/*.md; do
        if [ -f "${agent_file}" ]; then
            local filename
            filename=$(basename "${agent_file}")
            run_cmd "cp '${agent_file}' '${dst_dir}/${filename}'" "${dst_dir}" || {
                warn "  复制 agent 文件失败: ${filename}"
                continue
            }
            success "  已安装 agent: ${filename} -> ${dst_dir}/"
            installed_count=$((installed_count + 1))
        fi
    done

    if [ "${installed_count}" -eq 0 ]; then
        warn "  未找到任何 agent 文件 (*.md) 在 ${src_dir}"
    else
        success "已安装 ${installed_count} 个 agent 文件到 OpenCode"
    fi

    local purged
    purged=$(purge_deprecated_opencode_agents "${dst_dir}" false)
    if [ "${purged}" -gt 0 ]; then
        success "  已清理 ${purged} 个废弃 agent 文件"
    fi
}

# 安装 OpenCode 命令文件
install_opencode_commands() {
    local src_dir="${PROJECT_ROOT}/evolving-agent/command"
    local dst_dir="${OPENCODE_COMMAND_DIR}"

    if [ "${dry_run}" = true ]; then
        info "DRY-RUN: 将安装命令文件到 ${dst_dir}"
        return 0
    fi

    # 检查源目录是否存在
    if [ ! -d "${src_dir}" ]; then
        warn "命令目录不存在: ${src_dir}"
        return 0
    fi

    ensure_dir "${dst_dir}" || return 1

    # 复制所有 .md 命令文件
    for cmd_file in "${src_dir}"/*.md; do
        if [ -f "${cmd_file}" ]; then
            local filename=$(basename "${cmd_file}")
            run_cmd "cp '${cmd_file}' '${dst_dir}/${filename}'" "${dst_dir}" || {
                warn "复制命令文件失败: ${filename}"
                continue
            }
            success "已安装命令: ${filename} -> ${dst_dir}/"
        fi
    done
}

# 创建 CodeGraph 全局知识目录（SQLite knowledge.db 在首次写入时初始化）
setup_knowledge_dir() {
    local knowledge_dir="$1"
    
    if [ "${dry_run}" = true ]; then
        info "DRY-RUN: 将创建 CodeGraph 知识目录 ${knowledge_dir}"
        return 0
    fi
    
    ensure_dir "${knowledge_dir}" || return 1
    
    success "CodeGraph 知识目录已创建: ${knowledge_dir}"
}

# write_global_agent_env — 见 lib/shared-runtime.sh write_shared_config_env

_is_windows_shell() {
    case "$(uname -s 2>/dev/null)" in
        MINGW*|MSYS*|CYGWIN*|Windows_NT*) return 0 ;;
    esac
    [ "${OS:-}" = "Windows_NT" ] && return 0
    return 1
}

# 为 Python 脚本设置可执行权限（Unix/macOS；排除 .venv 避免扫描 site-packages）
set_python_executable() {
    local skills_base_dir="$1"

    if _is_windows_shell; then
        info "Windows 环境，跳过 Python 可执行权限设置"
        return 0
    fi

    info "设置 Python 脚本可执行权限..."

    local skill_name skill_dir py_count
    for skill_name in "${ALL_SKILLS[@]}"; do
        skill_dir="${skills_base_dir}/${skill_name}"
        [ -d "${skill_dir}" ] || continue

        py_count=0
        while IFS= read -r py_file; do
            [ -n "${py_file}" ] || continue
            chmod +x "${py_file}" 2>/dev/null || warn "  设置权限失败: ${py_file}"
            py_count=$((py_count + 1))
        done <<EOF
$(find "${skill_dir}" \
    \( -path '*/.venv/*' -o -path '*/.venv' -o -path '*/__pycache__/*' \) -prune \
    -o -name '*.py' -type f -print 2>/dev/null)
EOF

        if [ "${py_count}" -gt 0 ]; then
            success "  ${skill_name}: ${py_count} 个 Python 脚本已设置可执行权限"
        fi
    done
}

################################################################################
# Python 虚拟环境 — 多平台共享（见 lib/shared-runtime.sh）
################################################################################

VENV_SKILL="evolving-agent"

################################################################################
# 主流程
################################################################################

show_help() {
    cat << EOF
Evolving Programming Agent - 统一安装器 v${VERSION}

用法:
    $SCRIPT_NAME [选项]

选项:
    --all                   安装所有 skill 到全部平台 (推荐)
    --opencode              仅安装到 OpenCode
    --claude-code           仅安装到 Claude Code
    --cursor                仅安装到 Cursor (~/.agents/skills/)
    --openclaw              仅安装到 OpenClaw (~/.openclaw/skills/)
    --hermes                仅安装到 Hermes Agent (~/.hermes/skills/)
    --skills <list>         指定要安装的 skill (逗号分隔)
    --china                 国内镜像加速：PyPI + HF 镜像 + 禁用 XET + ModelScope BGE 预下载
    --mirror <url>          指定 PyPI 镜像 URL（不自动设置 HF；可配合 HF_ENDPOINT 环境变量）
    --status                显示共享运行时状态（venv / KB / 平台链接）
    --migrate-shared        仅迁移/链接共享运行时并清理旧 venv（不重装 skill）
    --dry-run               预览模式，不实际执行
    --help                  显示此帮助信息

示例:
    $SCRIPT_NAME --all
    $SCRIPT_NAME --all --china          # 推荐国内用户：pip + HF 镜像 + BGE 预下载
    $SCRIPT_NAME --opencode
    $SCRIPT_NAME --dry-run --all

环境变量:
    PIP_INDEX_URL           PyPI 镜像（优先于 --china）
    HF_ENDPOINT             HuggingFace 镜像（--china 默认 https://hf-mirror.com）
    HF_HUB_DISABLE_XET      --china 设为 1，避免大文件走 cas-bridge.xethub.hf.co
    EVOLVE_USE_CN_MIRROR=1  等价于 --china（便于 CI / setup_venv.sh）
    EVOLVING_AGENT_HOME     共享运行时根目录（默认 ~/.local/share/evolving-agent）

安装路径:
    Shared Runtime:      ${EVOLVING_AGENT_HOME:-~/.local/share/evolving-agent}/
    Shared Knowledge:    ${EVOLVING_AGENT_HOME:-~/.local/share/evolving-agent}/codegraph/
    Legacy KB symlink:   ~/.config/opencode/codegraph → 上述目录

说明:
    - Cursor 使用独立的 agent skills 目录 (~/.agents/skills/)，与 Claude Code 分开管理
    - OpenCode 安装时会同时安装命令文件 (如 /evolve) 和 agent 文件
    - Claude Code 通过 Task tool spawn subagent 调度，agent 文件作为 subagent prompt
    - OpenClaw 通过 sessions_spawn() 函数调度 subagent，agent 文件作为 subagent prompt
    - Hermes Agent 通过 delegate_task 工具调度 subagent，agent 文件作为 subagent prompt
    - 知识数据存储在独立目录，与 skill 代码分离

架构说明 :
    evolving-agent/         核心 skill，包含以下目录:
    ├── agents/              多 agent 角色定义 (coder/reviewer)
    ├── workflows/           编程工作流 (full-mode/simple-mode/consult-mode)
    ├── references/          参考文档 (知识库/GitHub学习/审查清单/schema)
    ├── templates/           任务模板 (feature_list.json/progress.txt)
    ├── command/             命令入口 (/evolve)
    └── scripts/
        ├── codegraph/         项目图谱 + 知识归纳（scan/context/extract）
        ├── core/              状态机 + 原子写入 + 集中配置
        └── knowledge/         四级检索 + 生命周期 + dashboard（CodeGraph SQLite）

多 Agent 模型配置:
    orchestrator: （SKILL.md 主进程，继承平台模型）
    coder:        zai-coding-plan/glm-5    (代码执行)
    reviewer:     opencode-go/minimax-m3  (代码审查)

    知识归纳/检索: codegraph 脚本（extract/context/scan）

Python 虚拟环境（多平台共享）:
    - 唯一 venv: ${EVOLVING_AGENT_HOME:-~/.local/share/evolving-agent}/runtime/.venv/
    - 各平台 skill 目录下 .venv 为指向上述目录的 symlink
    - install 会自动清理重复的旧 venv 与 .venv.legacy.* 备份

更多信息: https://github.com/richenlin/evolving-programming-agent
EOF
}

main() {
    local install_opencode=false
    local install_claude_code=false
    local install_cursor=false
    local install_openclaw=false
    local install_hermes=false
    local skills_to_install=("${ALL_SKILLS[@]}")
    local dry_run=false
    local show_status=false
    local migrate_shared=false

    if [ "${EVOLVE_USE_CN_MIRROR:-}" = "1" ]; then
        apply_china_mirrors
    fi

    while [[ $# -gt 0 ]]; do
        case $1 in
            --all)
                install_opencode=true
                install_claude_code=true
                install_cursor=true
                install_openclaw=true
                install_hermes=true
                shift
                ;;
            --opencode)
                install_opencode=true
                shift
                ;;
            --claude-code)
                install_claude_code=true
                shift
                ;;
            --cursor)
                install_cursor=true
                shift
                ;;
            --openclaw)
                install_openclaw=true
                shift
                ;;
            --hermes)
                install_hermes=true
                shift
                ;;
            --skills)
                shift
                IFS=',' read -ra skills_to_install <<< "$1"
                shift
                ;;
            --china)
                apply_china_mirrors
                shift
                ;;
            --mirror)
                shift
                if [ -z "${1:-}" ]; then
                    error "请提供 --mirror 的 URL，例如: --mirror https://pypi.tuna.tsinghua.edu.cn/simple"
                    exit 1
                fi
                PIP_INDEX_URL="$1"
                export PIP_INDEX_URL
                shift
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            --status)
                show_status=true
                shift
                ;;
            --migrate-shared)
                migrate_shared=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done

    export_mirror_env

    if [ "$show_status" = true ]; then
        show_shared_runtime_status
        exit 0
    fi

    if [ "$migrate_shared" = true ]; then
        _run_shared_runtime_migration || exit 1
        exit 0
    fi

    # 如果没有指定平台
    if [ "$install_opencode" = false ] && [ "$install_claude_code" = false ] && [ "$install_cursor" = false ] && [ "$install_openclaw" = false ] && [ "$install_hermes" = false ]; then
        # 非交互模式（CI/管道/无 TTY）：默认安装全部
        if [ ! -t 0 ]; then
            warn "未指定平台且 stdin 非 TTY，默认 --all"
            install_opencode=true
            install_claude_code=true
            install_cursor=true
            install_openclaw=true
            install_hermes=true
        else
            separator
            info "选择要安装的平台:"
            info "1) OpenCode          (~/.config/opencode/skills/)"
            info "2) Claude Code       (~/.claude/skills/)"
            info "3) Cursor            (~/.agents/skills/)"
            info "4) OpenClaw          (~/.openclaw/skills/)"
            info "5) Hermes Agent      (~/.hermes/skills/)"
            info "6) 全部安装"
            separator
            read -p "请选择 [1-6]: " choice
            case $choice in
                1) install_opencode=true ;;
                2) install_claude_code=true ;;
                3) install_cursor=true ;;
                4) install_openclaw=true ;;
                5) install_hermes=true ;;
                6)
                    install_opencode=true
                    install_claude_code=true
                    install_cursor=true
                    install_openclaw=true
                    install_hermes=true
                    ;;
                *)
                    error "无效选择"
                    exit 1
                    ;;
            esac
        fi
    fi

    if [ "${dry_run}" = true ]; then
        warn "DRY-RUN 模式：不会实际执行任何操作"
    fi

    # 刷新 VERSION 文件（确保安装的是当前 commit 的版本）
    separator
    info "刷新版本文件..."
    update_version_file

    separator
    info "开始安装 skill 组件..."
    info "架构: evolving-agent (核心)"
    separator

    # 遍历要安装的 skill
    for skill_name in "${skills_to_install[@]}"; do
        # Trim whitespace
        skill_name=$(echo "$skill_name" | xargs)

        info "处理: ${skill_name}"

        if [ ! -d "${PROJECT_ROOT}/${skill_name}" ]; then
            warn "跳过 ${skill_name} (目录不存在)"
            continue
        fi

        # 安装到各个平台
        if [ "$install_opencode" = true ]; then
            install_to_opencode "$skill_name"
        fi

        if [ "$install_claude_code" = true ]; then
            install_to_claude_code "$skill_name"
        fi

        if [ "$install_cursor" = true ]; then
            install_to_cursor "$skill_name"
        fi

        if [ "$install_openclaw" = true ]; then
            install_to_openclaw "$skill_name"
        fi

        if [ "$install_hermes" = true ]; then
            install_to_hermes "$skill_name"
        fi
    done

    # 安装 OpenCode 命令文件
    if [ "$install_opencode" = true ]; then
        separator
        info "安装 OpenCode 命令文件..."
        install_opencode_commands
    fi

    # 安装 OpenCode Agent 文件（仅 OpenCode 支持原生 agent 系统）
    if [ "$install_opencode" = true ]; then
        separator
        info "安装 OpenCode Agent 文件..."
        info "  (Claude Code 通过 Task tool spawn subagent，agent 文件已随 skill 复制)"
        install_opencode_agents
    fi

    # 共享运行时 + 全局知识库（唯一副本）
    separator
    info "配置多平台共享运行时..."
    setup_knowledge_dir "${SHARED_CODEGRAPH_DIR}"
    if [ "${dry_run}" = true ]; then
        info "DRY-RUN: ensure_shared_runtime + link platform .venv symlinks + cleanup"
    else
        ensure_shared_runtime || warn "共享运行时设置失败"
        link_selected_platform_venvs \
            "$install_opencode" "$install_claude_code" "$install_cursor" \
            "$install_openclaw" "$install_hermes"
        cleanup_old_resources
    fi

    # 设置 Python 脚本可执行权限
    if [ "${dry_run}" = true ]; then
        separator
        info "DRY-RUN: 将为 .py 文件设置可执行权限"
    else
        separator
        if [ "$install_opencode" = true ]; then
            set_python_executable "${OPENCODE_SKILLS_DIR}"
        fi
        if [ "$install_claude_code" = true ]; then
            set_python_executable "${CLAUDE_CODE_SKILLS_DIR}"
        fi
        if [ "$install_cursor" = true ]; then
            set_python_executable "${CURSOR_SKILLS_DIR}"
        fi
        if [ "$install_openclaw" = true ]; then
            set_python_executable "${OPENCLAW_SKILLS_DIR}"
        fi
        if [ "$install_hermes" = true ]; then
            set_python_executable "${HERMES_SKILLS_DIR}"
        fi
    fi

    # 安装 post-commit hook，后续每次提交自动同步 VERSION
    separator
    info "安装 git post-commit hook..."
    install_git_hook

    separator
    success "安装完成！"
    separator

    if [ "$dry_run" = false ]; then
        info "建议重启相应的 IDE/CLI 以使更改生效"
        echo ""
        
        if [ "$install_opencode" = true ]; then
            info "OpenCode 安装路径:"
            info "  - Skills:    ${OPENCODE_SKILLS_DIR}/"
            info "  - Agents:    ${OPENCODE_AGENTS_DIR}/"
            info "               (coder/reviewer + codegraph scripts)"
            info "  - Commands:  ${OPENCODE_COMMAND_DIR}/"
            echo ""
        fi
        
        if [ "$install_claude_code" = true ]; then
            info "Claude Code 安装路径:"
            info "  - Skills:    ${CLAUDE_CODE_SKILLS_DIR}/"
            info "  - 说明: Claude Code 通过 Task tool spawn subagent 调度（agent 文件在 skill 内作为 prompt）"
            echo ""
        fi

        if [ "$install_cursor" = true ]; then
            info "Cursor 安装路径:"
            info "  - Skills:    ${CURSOR_SKILLS_DIR}/"
            info "  - 说明: Cursor agent skills 目录，通过 Task tool spawn subagent 调度"
            echo ""
        fi

        if [ "$install_openclaw" = true ]; then
            info "OpenClaw 安装路径:"
            info "  - Skills:    ${OPENCLAW_SKILLS_DIR}/"
            info "  - 说明: OpenClaw skills 目录，通过 sessions_spawn() 调度 subagent"
            echo ""
        fi

        if [ "$install_hermes" = true ]; then
            info "Hermes Agent 安装路径:"
            info "  - Skills:    ${HERMES_SKILLS_DIR}/"
            info "  - 说明: Hermes Agent skills 目录，通过 delegate_task 调度 subagent"
            echo ""
        fi
        
        info "共享运行时: ${EVOLVING_AGENT_HOME}/"
        info "  venv:     ${SHARED_VENV}"
        info "  知识库:   ${SHARED_CODEGRAPH_DIR}/"
        info "  配置:     ${SHARED_CONFIG_ENV}"
        info "各平台 .venv → 上述共享 venv（symlink）"
        echo ""
        info "查看状态: ${SCRIPT_NAME} --status"
        echo ""
        
        info "虚拟环境: ${SHARED_VENV}（多平台共享）"
        echo ""
        
        warn "⚠️  模型配置提示（重要）"
        echo ""
        info "Agent 文件中已内置默认模型配置，但需要配置 API key 才能使用："
        echo ""
        info "1. 复制模板文件:"
        info "   cp ${PROJECT_ROOT}/opencode.json.template ~/.config/opencode/opencode.json"
        echo ""
        info "2. 编辑并填入 API key:"
        info "   - OpenCode Go / MiniMax M3（用于 reviewer 角色，见 docs/MODEL-CONFIG.md）"
        info "   - 智谱 AI key (用于其他角色的 GLM-5)"
        echo ""
        info "3. 查看详细配置指南:"
        info "   cat ${PROJECT_ROOT}/docs/MODEL-CONFIG.md"
        echo ""
        info "或使用其他模型替代，参考: ${PROJECT_ROOT}/opencode.json.template"
    fi
}

# 执行主函数
main "$@"

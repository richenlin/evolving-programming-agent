#!/bin/bash
################################################################################
# Evolving Programming Agent - 统一安装器
#
# 功能:
#   安装所有 skill 组件
#   支持 OpenCode / Claude Code (Cursor 自动共享)
#   支持批量安装
#
# 使用方法:
#   ./install.sh --all                    # 安装所有 skill
#   ./install.sh --opencode             # 仅安装到 OpenCode
#   ./install.sh --claude-code          # 仅安装到 Claude Code (Cursor 也会使用)
#   ./install.sh --skills "skill1,skill2" # 指定要安装的 skill
#   ./install.sh --dry-run              # 预览模式
################################################################################

set -euo pipefail

################################################################################
# 配置常量
################################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
VERSION="1.0.0"

# 技能列表
declare -a ALL_SKILLS=(
    "github-to-skills"
    "skill-manager"
    "evolving-agent"
    "programming-assistant"
)

# 路径配置
OPENCODE_SKILLS_DIR="$HOME/.config/opencode/skill"
CLAUDE_CODE_SKILLS_DIR="$HOME/.claude/skills"
# Cursor 新版本会自动读取 ~/.claude/skills/，无需单独安装

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

        run_cmd "rsync -av --delete '$src' '$dst'" "$dst"
    else
        # Fallback: 使用 cp
        warn "rsync 不可用，使用 cp（可能无法完全清理旧文件）"

        # 先删除目标目录（如果有 sudo 权限）
        if [ -d "$dst" ]; then
            run_cmd "rm -rf '$dst'" "$dst"
        fi

        # 重新创建目标目录
        run_cmd "mkdir -p '$dst'" "$dst"

        # 复制源目录内容
        run_cmd "cp -r '$src'/* '$dst'/" "$dst"
    fi
}

################################################################################
# 安装函数
################################################################################

install_to_opencode() {
    local skill_name="$1"
    local src_dir="${SCRIPT_DIR}/${skill_name}"
    local dst_dir="${OPENCODE_SKILLS_DIR}/${skill_name}"

    if [ "${dry_run}" = true ]; then
        info "DRY-RUN: 将安装 ${skill_name} 到 OpenCode"
        if skill_needs_venv "${src_dir}"; then
            info "DRY-RUN:   将创建虚拟环境: ${dst_dir}/.venv"
            info "DRY-RUN:   将修复 Python 路径"
        fi
        return 0
    fi

    ensure_dir "${OPENCODE_SKILLS_DIR}" || return 1
    
    # 如果目标已存在，先删除
    if [ -e "${dst_dir}" ]; then
        run_cmd "rm -rf '$dst_dir'" "$dst_dir" || return 1
    fi
    
    safe_copy "${src_dir}" "${dst_dir}" || return 1
    success "已安装: ${skill_name} -> ${dst_dir}"
    
    # 设置虚拟环境并修复 Python 路径
    setup_venv "${dst_dir}" "${skill_name}" || warn "  虚拟环境设置失败"
    fix_python_paths "${dst_dir}" "${skill_name}" || warn "  Python 路径修复失败"
}

install_to_claude_code() {
    local skill_name="$1"
    local src_dir="${SCRIPT_DIR}/${skill_name}"
    local dst_dir="${CLAUDE_CODE_SKILLS_DIR}/${skill_name}"

    if [ "${dry_run}" = true ]; then
        info "DRY-RUN: 将安装 ${skill_name} 到 Claude Code"
        if skill_needs_venv "${src_dir}"; then
            info "DRY-RUN:   将创建虚拟环境: ${dst_dir}/.venv"
            info "DRY-RUN:   将修复 Python 路径"
        fi
        return 0
    fi

    ensure_dir "${CLAUDE_CODE_SKILLS_DIR}" || return 1
    
    # 如果目标已存在，先删除
    if [ -e "${dst_dir}" ]; then
        run_cmd "rm -rf '$dst_dir'" "$dst_dir" || return 1
    fi
    
    safe_copy "${src_dir}" "${dst_dir}" || return 1
    success "已安装: ${skill_name} -> ${dst_dir}"
    
    # 设置虚拟环境并修复 Python 路径
    setup_venv "${dst_dir}" "${skill_name}" || warn "  虚拟环境设置失败"
    fix_python_paths "${dst_dir}" "${skill_name}" || warn "  Python 路径修复失败"
}

################################################################################
# Python 虚拟环境管理
################################################################################

# 检查 skill 是否需要 Python 虚拟环境
# 通过检查是否有 scripts/*.py 文件来判断
skill_needs_venv() {
    local skill_dir="$1"
    
    # 检查是否有 Python 脚本
    if ls "${skill_dir}"/scripts/*.py &> /dev/null 2>&1; then
        return 0  # 需要 venv
    fi
    
    return 1  # 不需要 venv
}

# 设置 Python 虚拟环境
setup_venv() {
    local skill_dir="$1"
    local skill_name="$2"
    local venv_dir="${skill_dir}/.venv"
    
    # 检查是否需要 venv
    if ! skill_needs_venv "${skill_dir}"; then
        info "  跳过 venv (${skill_name} 没有 Python 脚本)"
        return 0
    fi
    
    info "  设置 Python 虚拟环境: ${venv_dir}"
    
    # 创建虚拟环境（如果不存在）
    if [ ! -d "${venv_dir}" ]; then
        run_cmd "python3 -m venv '${venv_dir}'" "${venv_dir}" || {
            error "  创建虚拟环境失败"
            return 1
        }
    fi
    
    # 升级 pip 并安装依赖
    run_cmd "'${venv_dir}/bin/pip' install --upgrade pip -q" "${venv_dir}" || {
        warn "  pip 升级失败，继续安装依赖..."
    }
    
    run_cmd "'${venv_dir}/bin/pip' install 'PyYAML>=6.0,<7.0' -q" "${venv_dir}" || {
        error "  安装 PyYAML 失败"
        return 1
    }
    
    success "  虚拟环境就绪: ${venv_dir}"
    return 0
}

# 修复 SKILL.md 中的 Python 路径
# 将 `python scripts/...` 或 `python3 scripts/...` 替换为使用 ~ 的路径
fix_python_paths() {
    local skill_dir="$1"
    local skill_name="$2"
    local venv_python="${skill_dir}/.venv/bin/python"
    
    # 将路径中的 $HOME 替换为 ~，使路径更通用
    local venv_python_display="${venv_python/#$HOME/\~}"
    
    # 检查是否需要修复
    if ! skill_needs_venv "${skill_dir}"; then
        return 0
    fi
    
    # 检查 venv python 是否存在
    if [ ! -f "${venv_python}" ]; then
        warn "  venv python 不存在，跳过路径修复"
        return 0
    fi
    
    info "  修复 Python 路径..."
    
    # 查找所有 .md 文件并替换 python 命令
    # 使用 perl 替代 sed，因为 macOS sed 行为不一致
    local md_files=$(find "${skill_dir}" -name "*.md" -type f 2>/dev/null)
    
    for md_file in ${md_files}; do
        if [ -f "${md_file}" ]; then
            # 替换模式:
            # 1. `python3 scripts/` -> `{venv_python_display} scripts/`
            # 2. `python scripts/` -> `{venv_python_display} scripts/`
            # 使用 perl 进行原地替换（跨平台兼容）
            if command -v perl &> /dev/null; then
                perl -i -pe "s|python3? scripts/|${venv_python_display} scripts/|g" "${md_file}" 2>/dev/null || true
            else
                # Fallback: 使用临时文件
                local tmp_file=$(mktemp)
                sed "s|python3\{0,1\} scripts/|${venv_python_display} scripts/|g" "${md_file}" > "${tmp_file}" && \
                    mv "${tmp_file}" "${md_file}"
            fi
        fi
    done
    
    success "  Python 路径已修复"
    return 0
}

################################################################################
# 主流程
################################################################################

show_help() {
    cat << EOF
Evolving Programming Agent - 统一安装器 v${VERSION}

用法:
    $SCRIPT_NAME [选项]

选项:
    --all                   安装所有 skill (推荐)
    --opencode              仅安装到 OpenCode
    --claude-code           仅安装到 Claude Code
    --skills <list>         指定要安装的 skill (逗号分隔)
    --dry-run               预览模式，不实际执行
    --help                  显示此帮助信息

示例:
    $SCRIPT_NAME --all
    $SCRIPT_NAME --opencode --skills "github-to-skills,skill-manager"
    $SCRIPT_NAME --dry-run --all

安装路径:
    OpenCode:    ${OPENCODE_SKILLS_DIR}
    Claude Code: ${CLAUDE_CODE_SKILLS_DIR}

说明:
    - Cursor 和 Claude Code 共享相同的 skills 目录 (~/.claude/skills/)
    - 安装到 Claude Code 后，Cursor 会自动识别这些 skills

Python 虚拟环境:
    安装器会自动为包含 Python 脚本的 skill 创建独立的虚拟环境:
    - 虚拟环境位置: {skill_dir}/.venv/
    - 自动安装依赖: PyYAML>=6.0,<7.0
    - 自动修复 SKILL.md 中的 Python 路径为绝对路径
    - 这确保 skill 使用正确的 Python 环境，不受系统 Python 影响

更多信息: https://github.com/Khazix-Skills/evolving-programming-agent
EOF
}

main() {
    local install_opencode=false
    local install_claude_code=false
    local skills_to_install=("${ALL_SKILLS[@]}")
    local dry_run=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --all)
                install_opencode=true
                install_claude_code=true
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
            --skills)
                shift
                IFS=',' read -ra skills_to_install <<< "$1"
                shift
                ;;
            --dry-run)
                dry_run=true
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

    # 如果没有指定平台，询问用户
    if [ "$install_opencode" = false ] && [ "$install_claude_code" = false ]; then
        separator
        info "选择要安装的平台:"
        info "1) OpenCode"
        info "2) Claude Code (Cursor 也会自动使用这些 skills)"
        info "3) 全部安装"
        separator
        read -p "请选择 [1-3]: " choice
        case $choice in
            1) install_opencode=true ;;
            2) install_claude_code=true ;;
            3)
                install_opencode=true
                install_claude_code=true
                ;;
            *)
                error "无效选择"
                exit 1
                ;;
        esac
    fi

    if [ "${dry_run}" = true ]; then
        warn "DRY-RUN 模式：不会实际执行任何操作"
    fi

    separator
    info "开始安装 skill 组件..."
    separator

    # 遍历要安装的 skill
    for skill_name in "${skills_to_install[@]}"; do
        # Trim whitespace
        skill_name=$(echo "$skill_name" | xargs)

        info "处理: ${skill_name}"

        if [ ! -d "${SCRIPT_DIR}/${skill_name}" ]; then
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
    done

    separator
    success "安装完成！"
    separator

    if [ "$dry_run" = false ]; then
        info "建议重启相应的 IDE/CLI 以使更改生效"
        if [ "$install_claude_code" = true ]; then
            info "  - Claude Code 和 Cursor 都会自动识别新安装的 skills"
        fi
    fi
}

# 执行主函数
main "$@"

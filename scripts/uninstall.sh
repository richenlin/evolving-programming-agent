#!/bin/bash
################################################################################
# Evolving Programming Agent - 统一卸载器
#
# 功能:
#   卸载所有 skill 组件
#   支持 OpenCode / Claude Code / Cursor
#   支持选择性卸载
#
# 使用方法:
#   ./uninstall.sh --all                     # 卸载所有 skill
#   ./uninstall.sh --opencode               # 仅卸载 OpenCode skill
#   ./uninstall.sh --claude-code            # 仅卸载 Claude Code skill
#   ./uninstall.sh --cursor                 # 仅卸载 Cursor skill
#   ./uninstall.sh --skills "skill1,skill2" # 指定要卸载的 skill
#   ./uninstall.sh --dry-run                # 预览模式
################################################################################

set -euo pipefail

################################################################################
# 配置常量
################################################################################

# 脚本所在目录和项目根目录
_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${_SCRIPT_DIR}/.." && pwd)"
SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
VERSION="1.0.0"

# 技能列表
declare -a ALL_SKILLS=(
    "github-to-skills"
    "skill-manager"
    "evolving-agent"
    "programming-assistant"
)

# 共享 venv 所在的 skill
VENV_SKILL="evolving-agent"

# 路径配置
OPENCODE_SKILLS_DIR="$HOME/.config/opencode/skill"
CLAUDE_CODE_SKILLS_DIR="$HOME/.claude/skills"
CURSOR_RULES_DIR="$HOME/.cursor/rules"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

################################################################################
# 卸载函数
################################################################################

uninstall_from_opencode() {
    local skill_name="$1"
    local skill_dir="${OPENCODE_SKILLS_DIR}/${skill_name}"

    if [ ! -d "${skill_dir}" ]; then
        warn "OpenCode: ${skill_name} 未安装"
        return 0
    fi

    if [ "${DRY_RUN}" = true ]; then
        info "DRY-RUN: 将从 OpenCode 卸载 ${skill_name}"
        # 如果是 venv 所在的 skill，提示会清理虚拟环境
        if [ "${skill_name}" = "${VENV_SKILL}" ] && [ -d "${skill_dir}/.venv" ]; then
            info "DRY-RUN:   将清理共享虚拟环境: ${skill_dir}/.venv"
        fi
        return 0
    fi

    # 如果是 venv 所在的 skill，提示正在清理虚拟环境
    if [ "${skill_name}" = "${VENV_SKILL}" ] && [ -d "${skill_dir}/.venv" ]; then
        info "  清理共享虚拟环境: ${skill_dir}/.venv"
    fi

    rm -rf "${skill_dir}"
    success "已卸载 (OpenCode): ${skill_name}"
}

uninstall_from_claude_code() {
    local skill_name="$1"
    local skill_dir="${CLAUDE_CODE_SKILLS_DIR}/${skill_name}"

    if [ ! -d "${skill_dir}" ]; then
        warn "Claude Code: ${skill_name} 未安装"
        return 0
    fi

    if [ "${DRY_RUN}" = true ]; then
        info "DRY-RUN: 将从 Claude Code 卸载 ${skill_name}"
        # 如果是 venv 所在的 skill，提示会清理虚拟环境
        if [ "${skill_name}" = "${VENV_SKILL}" ] && [ -d "${skill_dir}/.venv" ]; then
            info "DRY-RUN:   将清理共享虚拟环境: ${skill_dir}/.venv"
        fi
        return 0
    fi

    # 如果是 venv 所在的 skill，提示正在清理虚拟环境
    if [ "${skill_name}" = "${VENV_SKILL}" ] && [ -d "${skill_dir}/.venv" ]; then
        info "  清理共享虚拟环境: ${skill_dir}/.venv"
    fi

    rm -rf "${skill_dir}"
    success "已卸载 (Claude Code): ${skill_name}"
}

uninstall_from_cursor() {
    local skill_name="$1"
    local rule_file="${CURSOR_RULES_DIR}/${skill_name}.md"

    if [ ! -f "${rule_file}" ]; then
        warn "Cursor: ${skill_name} 未安装"
        return 0
    fi

    if [ "${DRY_RUN}" = true ]; then
        info "DRY-RUN: 将从 Cursor 卸载 ${skill_name}"
        return 0
    fi

    rm -f "${rule_file}"
    success "已卸载 (Cursor): ${skill_name}"
}

################################################################################
# 主流程
################################################################################

show_help() {
    cat << EOF
Evolving Programming Agent - 统一卸载器 v${VERSION}

用法:
    $SCRIPT_NAME [选项]

选项:
    --all                   卸载所有 skill
    --opencode              仅从 OpenCode 卸载
    --claude-code           仅从 Claude Code 卸载
    --cursor                仅从 Cursor 卸载
    --skills <list>         指定要卸载的 skill (逗号分隔)
    --dry-run               预览模式，不实际执行
    --help                  显示此帮助信息

示例:
    $SCRIPT_NAME --all
    $SCRIPT_NAME --opencode --skills "github-to-skills,skill-manager"
    $SCRIPT_NAME --dry-run --all

卸载路径:
    OpenCode:    ${OPENCODE_SKILLS_DIR}
    Claude Code: ${CLAUDE_CODE_SKILLS_DIR}
    Cursor:      ${CURSOR_RULES_DIR}

更多信息: https://github.com/Khazix-Skills/evolving-programming-agent
EOF
}

main() {
    local uninstall_opencode=false
    local uninstall_claude_code=false
    local uninstall_cursor=false
    local skills_to_uninstall=("${ALL_SKILLS[@]}")
    local DRY_RUN=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --all)
                uninstall_opencode=true
                uninstall_claude_code=true
                uninstall_cursor=true
                shift
                ;;
            --opencode)
                uninstall_opencode=true
                shift
                ;;
            --claude-code)
                uninstall_claude_code=true
                shift
                ;;
            --cursor)
                uninstall_cursor=true
                shift
                ;;
            --skills)
                shift
                IFS=',' read -ra skills_to_uninstall <<< "$1"
                shift
                ;;
            --dry-run)
                DRY_RUN=true
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

    if [ "${DRY_RUN}" = true ]; then
        warn "DRY-RUN 模式：不会实际执行任何操作"
    fi

    separator
    info "开始卸载 skill 组件..."
    separator

    # 遍历要卸载的 skill
    for skill_name in "${skills_to_uninstall[@]}"; do
        # Trim whitespace
        skill_name=$(echo "$skill_name" | xargs)

        info "处理: ${skill_name}"

        # 卸载各个平台
        if [ "$uninstall_opencode" = true ]; then
            uninstall_from_opencode "$skill_name"
        fi

        if [ "$uninstall_claude_code" = true ]; then
            uninstall_from_claude_code "$skill_name"
        fi

        if [ "$uninstall_cursor" = true ]; then
            uninstall_from_cursor "$skill_name"
        fi
    done

    separator
    success "卸载完成！"
    separator
}

# 执行主函数
main "$@"

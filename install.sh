#!/bin/bash
################################################################################
# Evolving Programming Agent - 统一安装器
#
# 功能:
#   安装所有 skill 组件
#   支持 OpenCode / Claude Code / Cursor
#   支持批量安装
#
# 使用方法:
#   ./install.sh --all                    # 安装所有 skill
#   ./install.sh --opencode             # 仅安装到 OpenCode
#   ./install.sh --claude-code          # 仅安装到 Claude Code
#   ./install.sh --cursor               # 仅安装到 Cursor
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
    "skill-evolution-manager"
    "programming-assistant"
)

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
# 安装函数
################################################################################

install_to_opencode() {
    local skill_name="$1"
    local src_dir="${SCRIPT_DIR}/${skill_name}"
    local dst_dir="${OPENCODE_SKILLS_DIR}/${skill_name}"

    if [ "$DRY_RUN" = true ]; then
        info "DRY-RUN: 将安装 ${skill_name} 到 OpenCode"
        return 0
    fi

    mkdir -p "${OPENCODE_SKILLS_DIR}"
    cp -r "${src_dir}" "${dst_dir}"
    success "已安装: ${skill_name} -> ${dst_dir}"
}

install_to_claude_code() {
    local skill_name="$1"
    local src_dir="${SCRIPT_DIR}/${skill_name}"
    local dst_dir="${CLAUDE_CODE_SKILLS_DIR}/${skill_name}"

    if [ "$DRY_RUN" = true ]; then
        info "DRY-RUN: 将安装 ${skill_name} 到 Claude Code"
        return 0
    fi

    mkdir -p "${CLAUDE_CODE_SKILLS_DIR}"
    cp -r "${src_dir}" "${dst_dir}"
    success "已安装: ${skill_name} -> ${dst_dir}"
}

install_to_cursor() {
    local skill_name="$1"
    local src_dir="${SCRIPT_DIR}/${skill_name}"
    local dst_dir="${CURSOR_RULES_DIR}/${skill_name}.md"

    if [ "$DRY_RUN" = true ]; then
        info "DRY-RUN: 将安装 ${skill_name} 到 Cursor"
        return 0
    fi

    mkdir -p "${CURSOR_RULES_DIR}"

    # 移除 frontmatter 后复制到 Cursor
    awk '/^---$/ { skip++; next; } skip == 1 { next; } { print }' "${src_dir}/SKILL.md" > "${dst_dir}"
    success "已安装: ${skill_name} -> ${dst_dir}"
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
    --cursor                仅安装到 Cursor
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
    Cursor:      ${CURSOR_RULES_DIR}

更多信息: https://github.com/Khazix-Skills/evolving-programming-agent
EOF
}

main() {
    local install_opencode=false
    local install_claude_code=false
    local install_cursor=false
    local skills_to_install=("${ALL_SKILLS[@]}")
    local DRY_RUN=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --all)
                install_opencode=true
                install_claude_code=true
                install_cursor=true
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
    if [ "$install_opencode" = false ] && [ "$install_claude_code" = false ] && [ "$install_cursor" = false ]; then
        separator
        info "选择要安装的平台:"
        info "1) OpenCode"
        info "2) Claude Code"
        info "3) Cursor"
        info "4) 全部安装"
        separator
        read -p "请选择 [1-4]: " choice
        case $choice in
            1) install_opencode=true ;;
            2) install_claude_code=true ;;
            3) install_cursor=true ;;
            4)
                install_opencode=true
                install_claude_code=true
                install_cursor=true
                ;;
            *)
                error "无效选择"
                exit 1
                ;;
        esac
    fi

    if [ "$dry_run" = true ]; then
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

        if [ "$install_cursor" = true ]; then
            install_to_cursor "$skill_name"
        fi
    done

    separator
    success "安装完成！"
    separator

    if [ "$dry_run" = false ]; then
        info "建议重启相应的 IDE/CLI 以使更改生效"
    fi
}

# 执行主函数
main "$@"

#!/bin/bash
################################################################################
# 自动为所有配置的 Skill 设置虚拟环境
#
# 用法:
#   ./scripts/setup_venv.sh
################################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

separator() {
    echo "========================================================================"
}

# 路径配置
PLATFORMS=(
    "$HOME/.config/opencode/skill"
    "$HOME/.claude/skills"
)

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

setup_skill_venv() {
    local skill_dir="$1"
    
    if [ ! -d "${skill_dir}" ]; then
        warn "跳过: ${skill_dir} (目录不存在)"
        return
    fi
    
    local venv_dir="${skill_dir}/.venv"
    local skill_name=$(basename "${skill_dir}")
    
    info "处理 ${skill_name}..."
    
    if [ -d "${venv_dir}" ]; then
        info "  虚拟环境已存在"
    else
        info "  创建虚拟环境..."
        python3 -m venv "${venv_dir}"
    fi
    
    info "  安装依赖..."
    "${venv_dir}/bin/pip" install --upgrade pip
    "${venv_dir}/bin/pip" install 'PyYAML>=6.0,<7.0'
    
    local skill_md="${skill_dir}/SKILL.md"
    if [ -f "${skill_md}" ]; then
        info "  修正 Python 路径..."
        local temp_file=$(mktemp)
        sed -E "s|(python3? )(${skill_dir}/scripts/)|\\${venv_dir}/bin/python |g" "${skill_md}" > "${temp_file}"
        mv "${temp_file}" "${skill_md}"
        success "  Python 路径已修正"
    else
        warn "  SKILL.md 不存在: ${skill_md}"
    fi
}

main() {
    separator
    info "为所有 Skill 设置 Python 虚拟环境"
    separator
    
    local count=0
    for platform in "${PLATFORMS[@]}"; do
        if [ -d "${platform}" ]; then
            for skill_dir in "${platform}"/*; do
                if [ -d "${skill_dir}" ] && [ "$(basename "${skill_dir}")" != ".venv" ]; then
                    setup_skill_venv "${skill_dir}"
                    ((count++))
                fi
            done
        fi
    done
    
    separator
    success "完成！已为 ${count} 个 Skill 配置虚拟环境"
    separator
    echo ""
    echo "现在 Skill 将使用独立的 Python 环境，无需手动配置。"
    echo "每个 Skill 的虚拟环境位于: skill_dir/.venv/"
}

main "$@"

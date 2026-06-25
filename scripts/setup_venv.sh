#!/bin/bash
################################################################################
# 自动为所有配置的 Skill 设置虚拟环境
#
# 用法:
#   ./scripts/setup_venv.sh
#   ./scripts/setup_venv.sh --china          # PyPI（清华）+ HuggingFace（hf-mirror）
#   EVOLVE_USE_CN_MIRROR=1 ./scripts/setup_venv.sh
################################################################################

set -euo pipefail

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_DIR="$(cd "${_SCRIPT_DIR}/.." && pwd)"
# shellcheck source=lib/mirrors.sh
source "${_SCRIPT_DIR}/lib/mirrors.sh"

DEFAULT_LOCAL_EMBED_MODEL="${DEFAULT_LOCAL_EMBED_MODEL:-BAAI/bge-small-zh-v1.5}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

separator() {
    echo "========================================================================"
}

# 路径配置
PLATFORMS=(
    "$HOME/.config/opencode/skills"
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
    local skill_name
    skill_name=$(basename "${skill_dir}")
    
    info "处理 ${skill_name}..."
    
    if [ -d "${venv_dir}" ]; then
        info "  虚拟环境已存在"
    else
        info "  创建虚拟环境..."
        python3 -m venv "${venv_dir}"
    fi
    
    export_mirror_env
    local pip_index_opts
    pip_index_opts=$(pip_extra_index)
    local mirror_info
    mirror_info=$(mirror_status_line)
    if [ -n "${mirror_info}" ]; then
        info "  镜像: ${mirror_info}"
    fi
    
    info "  安装必需依赖..."
    # shellcheck disable=SC2086
    "${venv_dir}/bin/pip" install ${pip_index_opts} --upgrade pip -q
    # shellcheck disable=SC2086
    "${venv_dir}/bin/pip" install ${pip_index_opts} 'PyYAML>=6.0,<7.0' -q
    
    local optional_req="${SCRIPT_DIR}/requirements-optional.txt"
    if [ -f "${optional_req}" ]; then
        info "  安装/更新可选依赖（jieba、tree-sitter、sentence-transformers / BGE）..."
        # shellcheck disable=SC2086
        if ! "${venv_dir}/bin/pip" install ${pip_index_opts} -r "${optional_req}"; then
            warn "  部分可选依赖安装失败，核心功能不受影响"
        elif "${venv_dir}/bin/pip" show sentence-transformers >/dev/null 2>&1; then
            install_modelscope_cn "${venv_dir}/bin/pip" ${pip_index_opts} || \
                warn "  ModelScope 未安装，BGE 将走 HF 镜像（已禁用 XET）"
            info "  预下载 BGE 中文向量模型（${DEFAULT_LOCAL_EMBED_MODEL}）..."
            if prewarm_bge_model "${venv_dir}/bin/python" "${DEFAULT_LOCAL_EMBED_MODEL}"; then
                success "  BGE 模型已缓存"
            else
                warn "  模型预下载跳过（建议 setup_venv.sh --china）"
            fi
        fi
    fi
    
    local skill_md="${skill_dir}/SKILL.md"
    if [ -f "${skill_md}" ]; then
        info "  修正 Python 路径..."
        local temp_file
        temp_file=$(mktemp)
        sed -E "s|(python3? )(${skill_dir}/scripts/)|${venv_dir}/bin/python |g" "${skill_md}" > "${temp_file}"
        mv "${temp_file}" "${skill_md}"
        success "  Python 路径已修正"
    else
        warn "  SKILL.md 不存在: ${skill_md}"
    fi
}

main() {
    if [ "${EVOLVE_USE_CN_MIRROR:-}" = "1" ]; then
        apply_china_mirrors
    fi

    while [[ $# -gt 0 ]]; do
        case $1 in
            --china)
                apply_china_mirrors
                shift
                ;;
            --mirror)
                shift
                if [ -z "${1:-}" ]; then
                    error "请提供 --mirror 的 URL"
                    exit 1
                fi
                PIP_INDEX_URL="$1"
                export PIP_INDEX_URL
                shift
                ;;
            --help|-h)
                echo "用法: $0 [--china] [--mirror <pypi-url>]"
                exit 0
                ;;
            *)
                error "未知选项: $1"
                exit 1
                ;;
        esac
    done

    export_mirror_env

    separator
    info "为所有 Skill 设置 Python 虚拟环境"
    separator
    
    local count=0
    for platform in "${PLATFORMS[@]}"; do
        if [ -d "${platform}" ]; then
            for skill_dir in "${platform}"/*; do
                if [ -d "${skill_dir}" ] && [ "$(basename "${skill_dir}")" != ".venv" ]; then
                    setup_skill_venv "${skill_dir}"
                    ((count++)) || true
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
    echo "国内用户推荐: ./scripts/setup_venv.sh --china"
}

main "$@"

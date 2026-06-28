#!/bin/bash
# Shared domestic mirror settings for pip + HuggingFace (BGE / sentence-transformers).
#
# Usage (from install.sh / setup_venv.sh):
#   source "${SCRIPT_DIR}/lib/mirrors.sh"
#   apply_china_mirrors          # sets PIP_INDEX_URL + HF_ENDPOINT if unset
#   export_mirror_env            # export current mirror vars for child processes

# PyPI — 清华源（可用 PIP_INDEX_URL 覆盖）
PIP_INDEX_URL_DEFAULT_CN="${PIP_INDEX_URL_DEFAULT_CN:-https://pypi.tuna.tsinghua.edu.cn/simple}"

# HuggingFace 模型下载 — hf-mirror（BAAI/bge-small-zh-v1.5 等）
HF_ENDPOINT_DEFAULT_CN="${HF_ENDPOINT_DEFAULT_CN:-https://hf-mirror.com}"

# 国内镜像：禁用 XET，避免大文件走 cas-bridge.xethub.hf.co（境外 CDN，易超时）
HF_HUB_DISABLE_XET_CN="${HF_HUB_DISABLE_XET_CN:-1}"

apply_china_mirrors() {
    if [ -z "${PIP_INDEX_URL:-}" ]; then
        PIP_INDEX_URL="${PIP_INDEX_URL_DEFAULT_CN}"
    fi
    if [ -z "${HF_ENDPOINT:-}" ]; then
        HF_ENDPOINT="${HF_ENDPOINT_DEFAULT_CN}"
    fi
    if [ -z "${HF_HUB_DISABLE_XET:-}" ] && [ "${HF_HUB_DISABLE_XET_CN}" = "1" ]; then
        HF_HUB_DISABLE_XET=1
    fi
    export PIP_INDEX_URL HF_ENDPOINT HF_HUB_DISABLE_XET
    export EVOLVE_USE_CN_MIRROR=1
}

export_mirror_env() {
    [ -n "${PIP_INDEX_URL:-}" ] && export PIP_INDEX_URL
    [ -n "${HF_ENDPOINT:-}" ] && export HF_ENDPOINT
    [ -n "${HF_HUB_DISABLE_XET:-}" ] && export HF_HUB_DISABLE_XET
    if [ "${EVOLVE_USE_CN_MIRROR:-}" = "1" ]; then
        export EVOLVE_USE_CN_MIRROR
    fi
}

# 输出 pip 额外参数：-i <url> [--prefer-binary]
pip_extra_index() {
    if [ -n "${PIP_INDEX_URL:-}" ]; then
        echo "-i ${PIP_INDEX_URL} --prefer-binary"
    else
        echo ""
    fi
}

mirror_status_line() {
    local parts=()
    [ -n "${PIP_INDEX_URL:-}" ] && parts+=("PyPI=${PIP_INDEX_URL}")
    [ -n "${HF_ENDPOINT:-}" ] && parts+=("HF=${HF_ENDPOINT}")
    [ "${HF_HUB_DISABLE_XET:-}" = "1" ] && parts+=("XET=off")
    if [ "${#parts[@]}" -gt 0 ]; then
        echo "${parts[*]}"
    fi
}

china_mirror_active() {
    [ "${EVOLVE_USE_CN_MIRROR:-}" = "1" ] || [[ "${HF_ENDPOINT:-}" == *hf-mirror* ]]
}

# 国内镜像激活时安装 ModelScope（BGE 大文件走国内 CDN，避免 cas-bridge 超时）
install_modelscope_cn() {
    local python_bin="$1"
    shift
    local pip_install_opts="$*"

    if ! china_mirror_active; then
        return 0
    fi

    if "${python_bin}" -m pip show modelscope >/dev/null 2>&1; then
        return 0
    fi

    echo "  安装 ModelScope（国内 BGE 模型 CDN）..."
    # shellcheck disable=SC2086
    "${python_bin}" -m pip install ${pip_install_opts} 'modelscope>=1.9,<2.0' -q
}

# 安装 requirements-optional.txt 后预下载 BGE（需 sentence-transformers 已装好）
prewarm_bge_model() {
    local python_bin="$1"
    local model_id="${2:-BAAI/bge-small-zh-v1.5}"
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    if [ ! -x "${python_bin}" ]; then
        return 1
    fi

    export_mirror_env
    "${python_bin}" "${script_dir}/prewarm_bge.py" "${model_id}"
}

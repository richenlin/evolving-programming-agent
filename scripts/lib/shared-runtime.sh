#!/bin/bash
# Multi-platform shared runtime: one venv, one global KB, one model cache.
# Sourced by install.sh / setup_venv.sh (requires info/warn/error from caller).

# shellcheck disable=SC2034
VENV_SKILL="${VENV_SKILL:-evolving-agent}"

_default_evolving_agent_home() {
    if [ -n "${XDG_DATA_HOME:-}" ]; then
        echo "${XDG_DATA_HOME}/evolving-agent"
    else
        echo "${HOME}/.local/share/evolving-agent"
    fi
}

EVOLVING_AGENT_HOME="${EVOLVING_AGENT_HOME:-$(_default_evolving_agent_home)}"
SHARED_VENV="${EVOLVING_AGENT_HOME}/runtime/.venv"
SHARED_VENV_PYTHON="${SHARED_VENV}/bin/python"
SHARED_CODEGRAPH_DIR="${EVOLVING_AGENT_HOME}/codegraph"
SHARED_CONFIG_ENV="${EVOLVING_AGENT_HOME}/config/env"
SHARED_MANIFEST="${EVOLVING_AGENT_HOME}/install-manifest.json"
LEGACY_CODEGRAPH_DIR="${HOME}/.config/opencode/codegraph"
LEGACY_AGENT_ENV="${HOME}/.config/opencode/evolving-agent.env"
HF_HOME_SHARED="${EVOLVING_AGENT_HOME}/cache/huggingface"
MODELSCOPE_CACHE_SHARED="${EVOLVING_AGENT_HOME}/cache/modelscope"

# platform_key:skills_base_dir
ALL_PLATFORM_SKILL_BASES=(
    "opencode:${HOME}/.config/opencode/skills"
    "claude-code:${HOME}/.claude/skills"
    "cursor:${HOME}/.agents/skills"
    "openclaw:${HOME}/.openclaw/skills"
    "hermes:${HOME}/.hermes/skills"
)

_platform_venv_path() {
    local skills_base="$1"
    echo "${skills_base}/${VENV_SKILL}/.venv"
}

_init_agent_home_dirs() {
    mkdir -p \
        "${EVOLVING_AGENT_HOME}/runtime" \
        "${EVOLVING_AGENT_HOME}/cache/huggingface" \
        "${EVOLVING_AGENT_HOME}/cache/modelscope" \
        "${EVOLVING_AGENT_HOME}/codegraph" \
        "${EVOLVING_AGENT_HOME}/config"
}

_shared_venv_healthy() {
    [ -f "${SHARED_VENV}/pyvenv.cfg" ] && _venv_pip_works "${SHARED_VENV}"
}

# pip 必须通过 python -m pip 调用（venv 目录迁移后 bin/pip shebang 会失效）
_venv_pip_works() {
    local venv_dir="${1:-${SHARED_VENV}}"
    local py="${venv_dir}/bin/python"
    [ -x "${py}" ] || return 1
    "${py}" -m pip --version >/dev/null 2>&1
}

# venv 被 mv 到新路径后，修复 pyvenv.cfg 与 bin/* shebang
_fixup_relocated_venv() {
    local venv_dir="${1:-${SHARED_VENV}}"
    local py="${venv_dir}/bin/python"

    if _venv_pip_works "${venv_dir}"; then
        return 0
    fi

    if [ "${dry_run:-false}" = true ]; then
        info "DRY-RUN: 将修复迁移后的 venv: ${venv_dir}"
        return 0
    fi

    info "修复迁移后的 venv 路径（shebang / pyvenv.cfg）: ${venv_dir}"

    if python3 -m venv --upgrade "${venv_dir}" 2>/dev/null; then
        if _venv_pip_works "${venv_dir}"; then
            success "  venv --upgrade 完成"
            return 0
        fi
    fi

    if [ -x "${py}" ]; then
        "${py}" -m ensurepip --upgrade 2>/dev/null || true
        if _venv_pip_works "${venv_dir}"; then
            success "  ensurepip 修复完成"
            return 0
        fi
    fi

    warn "  无法原地修复 venv，将重建共享环境"
    rm -rf "${venv_dir}"
    python3 -m venv "${venv_dir}" || return 1
    if _venv_pip_works "${venv_dir}"; then
        success "  共享 venv 已重建（依赖将在下一步重装）"
        return 0
    fi
    return 1
}

# --- migration ---

migrate_legacy_codegraph() {
    if [ "${dry_run:-false}" = true ]; then
        if [ -d "${LEGACY_CODEGRAPH_DIR}" ] && [ ! -L "${LEGACY_CODEGRAPH_DIR}" ]; then
            info "DRY-RUN: 将迁移 ${LEGACY_CODEGRAPH_DIR} → ${SHARED_CODEGRAPH_DIR}"
        fi
        return 0
    fi

    if [ -L "${LEGACY_CODEGRAPH_DIR}" ]; then
        return 0
    fi

    if [ -d "${LEGACY_CODEGRAPH_DIR}" ]; then
        local has_files=false
        if [ -n "$(ls -A "${LEGACY_CODEGRAPH_DIR}" 2>/dev/null)" ]; then
            has_files=true
            info "迁移全局知识库: ${LEGACY_CODEGRAPH_DIR} → ${SHARED_CODEGRAPH_DIR}"
            mkdir -p "${SHARED_CODEGRAPH_DIR}"
            for item in "${LEGACY_CODEGRAPH_DIR}"/*; do
                [ -e "${item}" ] || continue
                local base
                base=$(basename "${item}")
                if [ ! -e "${SHARED_CODEGRAPH_DIR}/${base}" ]; then
                    mv "${item}" "${SHARED_CODEGRAPH_DIR}/"
                fi
            done
        fi
        rm -rf "${LEGACY_CODEGRAPH_DIR}"
        ln -sfn "${SHARED_CODEGRAPH_DIR}" "${LEGACY_CODEGRAPH_DIR}"
        if [ "${has_files}" = true ]; then
            success "全局知识库已迁入 ${SHARED_CODEGRAPH_DIR}（旧路径为 symlink）"
        fi
    elif [ ! -e "${LEGACY_CODEGRAPH_DIR}" ]; then
        mkdir -p "$(dirname "${LEGACY_CODEGRAPH_DIR}")"
        ln -sfn "${SHARED_CODEGRAPH_DIR}" "${LEGACY_CODEGRAPH_DIR}"
    fi
}

_venv_score() {
    local venv_dir="$1"
    local score=0
    [ -f "${venv_dir}/pyvenv.cfg" ] && score=$((score + 10))
    [ -x "${venv_dir}/bin/python" ] && score=$((score + 5))
    if [ -x "${venv_dir}/bin/python" ]; then
        "${venv_dir}/bin/python" -m pip show PyYAML >/dev/null 2>&1 && score=$((score + 3))
        "${venv_dir}/bin/python" -m pip show sentence-transformers >/dev/null 2>&1 && score=$((score + 5))
    fi
    if [ -d "${venv_dir}" ]; then
        local mtime
        mtime=$(stat -f "%m" "${venv_dir}" 2>/dev/null || stat -c "%Y" "${venv_dir}" 2>/dev/null || echo 0)
        score=$((score + mtime / 1000000))
    fi
    echo "${score}"
}

migrate_best_legacy_venv() {
    if _shared_venv_healthy; then
        return 0
    fi

    local best_path="" best_score=0
    local entry key skills_base venv_path score
    for entry in "${ALL_PLATFORM_SKILL_BASES[@]}"; do
        key="${entry%%:*}"
        skills_base="${entry#*:}"
        venv_path=$(_platform_venv_path "${skills_base}")
        if [ -d "${venv_path}" ] && [ ! -L "${venv_path}" ]; then
            score=$(_venv_score "${venv_path}")
            if [ "${score}" -gt "${best_score}" ]; then
                best_score=${score}
                best_path="${venv_path}"
            fi
        fi
    done

    if [ -z "${best_path}" ]; then
        return 0
    fi

    if [ "${dry_run:-false}" = true ]; then
        info "DRY-RUN: 将迁移最佳旧 venv ${best_path} → ${SHARED_VENV}"
        return 0
    fi

    info "迁移共享 venv: ${best_path} → ${SHARED_VENV}"
    mkdir -p "${EVOLVING_AGENT_HOME}/runtime"
    mv "${best_path}" "${SHARED_VENV}"
    _fixup_relocated_venv "${SHARED_VENV}" || {
        error "迁移后 venv 修复失败"
        return 1
    }
    success "已迁入共享 venv（来源: ${best_path}）"
}

# --- shared venv install ---

ensure_shared_venv() {
    local pip_index_opts
    pip_index_opts=$(pip_extra_index)

    export_mirror_env
    export HF_HOME="${HF_HOME:-${HF_HOME_SHARED}}"
    export MODELSCOPE_CACHE="${MODELSCOPE_CACHE:-${MODELSCOPE_CACHE_SHARED}}"

    local mirror_info
    mirror_info=$(mirror_status_line)
    info "共享 Python 运行时: ${SHARED_VENV}"
    if [ -n "${mirror_info}" ]; then
        info "  镜像: ${mirror_info}"
    fi
    info "  HF_HOME=${HF_HOME}"
    info "  MODELSCOPE_CACHE=${MODELSCOPE_CACHE}"

    if [ "${dry_run:-false}" = true ]; then
        info "DRY-RUN: 将创建/更新共享 venv 与可选依赖"
        return 0
    fi

    if ! _shared_venv_healthy; then
        if [ -d "${SHARED_VENV}" ]; then
            _fixup_relocated_venv "${SHARED_VENV}" || {
                error "共享 venv 无法修复"
                return 1
            }
        else
            python3 -m venv "${SHARED_VENV}" || {
                error "创建共享虚拟环境失败: ${SHARED_VENV}"
                return 1
            }
        fi
    fi

    local py="${SHARED_VENV_PYTHON}"
    local pip_install_opts="${pip_index_opts}"

    if ! "${py}" -m pip show PyYAML >/dev/null 2>&1; then
        # shellcheck disable=SC2086
        "${py}" -m pip install ${pip_install_opts} --upgrade pip -q || warn "pip 升级失败，继续..."
        # shellcheck disable=SC2086
        "${py}" -m pip install ${pip_install_opts} 'PyYAML>=6.0,<7.0' -q || {
            error "安装 PyYAML 失败"
            return 1
        }
    fi

    local optional_req="${PROJECT_ROOT}/requirements-optional.txt"
    if [ -f "${optional_req}" ]; then
        info "  安装/更新可选依赖（共享 venv，仅一次）..."
        # shellcheck disable=SC2086
        if ! "${py}" -m pip install ${pip_install_opts} -r "${optional_req}"; then
            warn "  可选依赖安装失败，将回退 hash-trick 向量"
        elif "${py}" -m pip show sentence-transformers >/dev/null 2>&1; then
            install_modelscope_cn "${py}" ${pip_install_opts} || \
                warn "  ModelScope 未安装，BGE 将走 HF 镜像"
            info "  预下载 BGE（${DEFAULT_LOCAL_EMBED_MODEL}）..."
            if prewarm_bge_model "${py}" "${DEFAULT_LOCAL_EMBED_MODEL}"; then
                success "  BGE 模型已缓存"
            else
                warn "  模型预下载跳过（建议 install.sh --china）"
            fi
        fi
    fi

    ln -sf "${SHARED_VENV_PYTHON}" "${EVOLVING_AGENT_HOME}/runtime/python"
    # shellcheck disable=SC2086
    "${py}" -m pip freeze > "${EVOLVING_AGENT_HOME}/runtime/requirements.lock" 2>/dev/null || true

    success "共享虚拟环境就绪: ${SHARED_VENV}"
    return 0
}

link_platform_venv() {
    local skills_base="$1"
    local platform_key="${2:-unknown}"
    local skill_dir="${skills_base}/${VENV_SKILL}"
    local link_path="${skill_dir}/.venv"

    if [ ! -d "${skill_dir}" ]; then
        warn "  跳过 venv 链接（目录不存在）: ${skill_dir}"
        return 0
    fi

    if [ "${dry_run:-false}" = true ]; then
        info "DRY-RUN: ${link_path} → ${SHARED_VENV}"
        return 0
    fi

    if [ -L "${link_path}" ]; then
        local target
        target=$(readlink "${link_path}" 2>/dev/null || true)
        if [ "${target}" = "${SHARED_VENV}" ] || [ "$(cd "$(dirname "${link_path}")" && cd "${target}" 2>/dev/null && pwd -P)" = "$(cd "${SHARED_VENV}" && pwd -P)" ]; then
            return 0
        fi
        rm -f "${link_path}"
    elif [ -d "${link_path}" ]; then
        local real_shared
        real_shared=$(cd "${SHARED_VENV}" 2>/dev/null && pwd -P || echo "")
        local real_link
        real_link=$(cd "${link_path}" 2>/dev/null && pwd -P || echo "")
        if [ -n "${real_shared}" ] && [ "${real_shared}" = "${real_link}" ]; then
            return 0
        fi
        local backup="${skill_dir}/.venv.legacy.${platform_key}.$(date +%Y%m%d%H%M%S)"
        info "  备份旧 venv: ${link_path} → ${backup}"
        mv "${link_path}" "${backup}"
    fi

    ln -sfn "${SHARED_VENV}" "${link_path}"
    success "  ${platform_key}: .venv → 共享运行时"
}

write_shared_config_env() {
    if [ "${dry_run:-false}" = true ]; then
        info "DRY-RUN: 将写入 ${SHARED_CONFIG_ENV}"
        return 0
    fi

    _init_agent_home_dirs
    cat > "${SHARED_CONFIG_ENV}" << EOF
# Generated by evolving-agent install.sh — shared runtime defaults
# Override: export VAR=... in shell, or add to \$PROJECT/.opencode/.agent_config

EVOLVING_AGENT_HOME=${EVOLVING_AGENT_HOME}
EVOLVING_AGENT_VENV=${SHARED_VENV}
VENV_PYTHON=${EVOLVING_AGENT_HOME}/runtime/python
CODEGRAPH_LOCAL_EMBED_MODEL=${DEFAULT_LOCAL_EMBED_MODEL}
CODEGRAPH_DIR=${SHARED_CODEGRAPH_DIR}
KNOWLEDGE_BASE_PATH=${SHARED_CODEGRAPH_DIR}
HF_HOME=${HF_HOME_SHARED}
MODELSCOPE_CACHE=${MODELSCOPE_CACHE_SHARED}
$( [ -n "${HF_ENDPOINT:-}" ] && echo "HF_ENDPOINT=${HF_ENDPOINT}" )
$( [ -n "${HF_HUB_DISABLE_XET:-}" ] && echo "HF_HUB_DISABLE_XET=${HF_HUB_DISABLE_XET}" )
$( [ "${EVOLVE_USE_CN_MIRROR:-}" = "1" ] && echo "EVOLVE_USE_CN_MIRROR=1" )
EOF

    mkdir -p "$(dirname "${LEGACY_AGENT_ENV}")"
    ln -sfn "${SHARED_CONFIG_ENV}" "${LEGACY_AGENT_ENV}"
    success "全局配置: ${SHARED_CONFIG_ENV}（${LEGACY_AGENT_ENV} → symlink）"
}

write_install_manifest() {
    local linked_platforms="${1:-}"

    if [ "${dry_run:-false}" = true ]; then
        return 0
    fi

    local skill_version=""
    if [ -f "${PROJECT_ROOT}/evolving-agent/scripts/VERSION" ]; then
        skill_version=$(tr -d '[:space:]' < "${PROJECT_ROOT}/evolving-agent/scripts/VERSION")
    fi

    python3 - "${SHARED_MANIFEST}" "${EVOLVING_AGENT_HOME}" "${SHARED_VENV}" \
        "${SHARED_CODEGRAPH_DIR}" "${HF_HOME_SHARED}" "${MODELSCOPE_CACHE_SHARED}" \
        "${DEFAULT_LOCAL_EMBED_MODEL}" "${skill_version}" "${linked_platforms}" <<'PY'
import json, sys
from datetime import datetime, timezone

path, home, venv, cg, hf, ms, model, version, platforms_csv = sys.argv[1:10]
platforms = [p.strip() for p in platforms_csv.split(",") if p.strip()]
data = {
    "version": 1,
    "agent_home": home,
    "shared_venv": venv,
    "skill_version": version,
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "platforms": {p: {"linked_at": datetime.now(timezone.utc).isoformat()} for p in platforms},
    "cache": {
        "hf_home": hf,
        "modelscope": ms,
        "bge_model": model,
    },
}
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
PY
}

# --- cleanup old duplicated resources ---

cleanup_legacy_venv_backups() {
    local skill_dir backup removed=0
    for entry in "${ALL_PLATFORM_SKILL_BASES[@]}"; do
        skill_dir="${entry#*:}/${VENV_SKILL}"
        [ -d "${skill_dir}" ] || continue
        for backup in "${skill_dir}"/.venv.legacy.*; do
            [ -e "${backup}" ] || continue
            if _shared_venv_healthy; then
                if [ "${dry_run:-false}" = true ]; then
                    info "DRY-RUN: 将删除旧 venv 备份 ${backup}"
                else
                    info "清理旧 venv 备份: ${backup}"
                    rm -rf "${backup}"
                fi
                removed=$((removed + 1))
            fi
        done
    done
    if [ "${removed}" -gt 0 ] && [ "${dry_run:-false}" != true ]; then
        success "已清理 ${removed} 个旧 venv 备份"
    fi
}

cleanup_duplicate_platform_venvs() {
    if ! _shared_venv_healthy; then
        return 0
    fi
    local entry skills_base venv_path real_shared real_venv
    real_shared=$(cd "${SHARED_VENV}" && pwd -P 2>/dev/null || echo "")
    [ -n "${real_shared}" ] || return 0

    for entry in "${ALL_PLATFORM_SKILL_BASES[@]}"; do
        skills_base="${entry#*:}"
        venv_path=$(_platform_venv_path "${skills_base}")
        if [ -d "${venv_path}" ] && [ ! -L "${venv_path}" ]; then
            real_venv=$(cd "${venv_path}" && pwd -P 2>/dev/null || echo "")
            if [ "${real_venv}" = "${real_shared}" ]; then
                continue
            fi
            if [ "${dry_run:-false}" = true ]; then
                info "DRY-RUN: 将删除重复 venv ${venv_path} 并改为 symlink"
            else
                warn "删除重复 venv 目录: ${venv_path}"
                rm -rf "${venv_path}"
                ln -sfn "${SHARED_VENV}" "${venv_path}"
            fi
        fi
    done
}

cleanup_empty_legacy_knowledge_dirs() {
    local legacy_dir
    for legacy_dir in \
        "${HOME}/.config/opencode/knowledge" \
        "${HOME}/.claude/knowledge"; do
        if [ -d "${legacy_dir}" ] && [ ! -L "${legacy_dir}" ]; then
            if [ -z "$(ls -A "${legacy_dir}" 2>/dev/null)" ]; then
                if [ "${dry_run:-false}" = true ]; then
                    info "DRY-RUN: 将删除空目录 ${legacy_dir}"
                else
                    rmdir "${legacy_dir}" 2>/dev/null && info "已删除空旧知识目录: ${legacy_dir}"
                fi
            fi
        fi
    done
}

cleanup_old_resources() {
    info "清理旧资源（重复 venv / 空目录 / 备份）..."
    cleanup_duplicate_platform_venvs
    cleanup_legacy_venv_backups
    cleanup_empty_legacy_knowledge_dirs
    migrate_legacy_codegraph
}

# --- orchestration ---

_collect_linked_platform_keys() {
    local keys=()
    local entry key skills_base
    for entry in "${ALL_PLATFORM_SKILL_BASES[@]}"; do
        key="${entry%%:*}"
        skills_base="${entry#*:}"
        if [ -d "${skills_base}/${VENV_SKILL}" ]; then
            keys+=("${key}")
        fi
    done
    local IFS=,
    echo "${keys[*]}"
}

ensure_shared_runtime() {
    _init_agent_home_dirs
    migrate_legacy_codegraph
    migrate_best_legacy_venv
    ensure_shared_venv || return 1
    write_shared_config_env
    write_install_manifest "$(_collect_linked_platform_keys)"
}

link_all_installed_platform_venvs() {
    local entry key skills_base
    for entry in "${ALL_PLATFORM_SKILL_BASES[@]}"; do
        key="${entry%%:*}"
        skills_base="${entry#*:}"
        if [ -d "${skills_base}/${VENV_SKILL}" ]; then
            link_platform_venv "${skills_base}" "${key}"
        fi
    done
}

link_selected_platform_venvs() {
    local install_opencode="${1:-false}"
    local install_claude_code="${2:-false}"
    local install_cursor="${3:-false}"
    local install_openclaw="${4:-false}"
    local install_hermes="${5:-false}"

    [ "${install_opencode}" = true ] && link_platform_venv "${HOME}/.config/opencode/skills" "opencode"
    [ "${install_claude_code}" = true ] && link_platform_venv "${HOME}/.claude/skills" "claude-code"
    [ "${install_cursor}" = true ] && link_platform_venv "${HOME}/.agents/skills" "cursor"
    [ "${install_openclaw}" = true ] && link_platform_venv "${HOME}/.openclaw/skills" "openclaw"
    [ "${install_hermes}" = true ] && link_platform_venv "${HOME}/.hermes/skills" "hermes"
    write_install_manifest "$(_collect_linked_platform_keys)"
}

_run_shared_runtime_migration() {
    separator() { echo "========================================================================"; }
    separator
    info "多平台共享运行时迁移"
    separator
    _init_agent_home_dirs
    migrate_legacy_codegraph
    migrate_best_legacy_venv
    ensure_shared_venv || return 1
    write_shared_config_env
    link_all_installed_platform_venvs
    cleanup_old_resources
    separator
    success "共享运行时迁移完成"
    show_shared_runtime_status
}

_dir_size_human() {
    local path="$1"
    if [ -e "${path}" ]; then
        du -sh "${path}" 2>/dev/null | awk '{print $1}'
    else
        echo "-"
    fi
}

show_shared_runtime_status() {
    separator() { echo "========================================================================"; }
    separator
    info "Evolving Agent 共享运行时状态"
    separator
    echo "EVOLVING_AGENT_HOME: ${EVOLVING_AGENT_HOME}"
    echo "Shared venv:         $(_dir_size_human "${SHARED_VENV}")  ${SHARED_VENV}"
    echo "HF cache:            $(_dir_size_human "${HF_HOME_SHARED}")  ${HF_HOME_SHARED}"
    echo "Global KB:           $(_dir_size_human "${SHARED_CODEGRAPH_DIR}")  ${SHARED_CODEGRAPH_DIR}"
    echo "Config:              ${SHARED_CONFIG_ENV}"
    if [ -f "${SHARED_MANIFEST}" ]; then
        echo "Manifest:            ${SHARED_MANIFEST}"
    fi
    echo ""
    info "平台 venv 链接:"
    local entry key skills_base venv_path
    for entry in "${ALL_PLATFORM_SKILL_BASES[@]}"; do
        key="${entry%%:*}"
        skills_base="${entry#*:}"
        venv_path=$(_platform_venv_path "${skills_base}")
        if [ -e "${venv_path}" ]; then
            if [ -L "${venv_path}" ]; then
                echo "  ${key}: symlink → $(readlink "${venv_path}")"
            elif [ -d "${venv_path}" ]; then
                echo "  ${key}: DUPLICATE dir $(_dir_size_human "${venv_path}") (应迁移为 symlink)"
            fi
        else
            echo "  ${key}: (未安装)"
        fi
    done
    local legacy_count=0
    for entry in "${ALL_PLATFORM_SKILL_BASES[@]}"; do
        for backup in "${entry#*:}/${VENV_SKILL}"/.venv.legacy.*; do
            [ -e "${backup}" ] || continue
            legacy_count=$((legacy_count + 1))
        done
    done
    if [ "${legacy_count}" -gt 0 ]; then
        warn "Legacy venv 备份: ${legacy_count} 个（下次 install 将清理）"
    else
        echo "Legacy venv 备份:    none"
    fi
    separator
}

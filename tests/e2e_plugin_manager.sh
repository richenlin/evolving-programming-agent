#!/bin/bash
################################################################################
# 端到端测试 - 插件管理
#
# 测试 enable/disable/health 的完整流程
################################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 测试目录
TEST_SKILLS_DIR="/tmp/test-skills-evolution"

echo "=========================================="
echo "端到端测试: 插件管理"
echo "=========================================="
echo

# 清理旧的测试目录
if [ -d "${TEST_SKILLS_DIR}" ]; then
    rm -rf "${TEST_SKILLS_DIR}"
fi

# 创建测试 skill
mkdir -p "${TEST_SKILLS_DIR}/test-skill"
cat > "${TEST_SKILLS_DIR}/test-skill/SKILL.md" << 'EOF'
---
name: test-skill
---
# Test Skill
EOF

# 步骤 1: 禁用 skill
echo "步骤 1: 禁用 skill..."
cd "${SCRIPT_DIR}/../skill-manager/scripts"
python toggle_skill.py --disable test-skill --skills-dir "${TEST_SKILLS_DIR}"

if [ ! -d "${TEST_SKILLS_DIR}/.disabled/test-skill" ]; then
    echo "✗ 禁用失败: test-skill 未在 .disabled 中"
    exit 1
else
    echo "✓ 禁用成功"
fi

# 步骤 2: 验证技能被禁用
if [ -d "${TEST_SKILLS_DIR}/test-skill" ]; then
    echo "✗ 验证失败: test-skill 仍在主目录"
    exit 1
else
    echo "✓ 验证通过: test-skill 已移出主目录"
fi

# 步骤 3: 启用 skill
echo "步骤 2: 启用 skill..."
python toggle_skill.py --enable test-skill --skills-dir "${TEST_SKILLS_DIR}"

if [ ! -d "${TEST_SKILLS_DIR}/test-skill" ]; then
    echo "✗ 启用失败: test-skill 未在主目录"
    exit 1
else
    echo "✓ 启用成功"
fi

# 步骤 4: 验证技能被启用
if [ -d "${TEST_SKILLS_DIR}/.disabled/test-skill" ]; then
    echo "✗ 验证失败: test-skill 仍在 .disabled 中"
    exit 1
else
    echo "✓ 验证通过: test-skill 已移回主目录"
fi

# 步骤 5: 健康检查
echo "步骤 3: 健康检查..."
python health_check.py --skills-dir "${TEST_SKILLS_DIR}" --format table

# 清理
rm -rf "${TEST_SKILLS_DIR}"

echo
echo "=========================================="
echo "✓ 插件管理测试通过"
echo "=========================================="
echo

exit 0

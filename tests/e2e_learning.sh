#!/bin/bash
################################################################################
# 端到端测试 - 学习流程
#
# 测试 GitHub URL → 学习 → 生成 addon 的完整流程
################################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "端到端测试: 学习流程"
echo "=========================================="
echo

# 测试仓库
TEST_REPO="https://github.com/alan2207/bulletproof-react"

# 步骤 1: fetch_github_info.py
echo "步骤 1: 获取仓库信息..."
FETCH_OUTPUT=$(cd "${SCRIPT_DIR}/../github-to-skills/scripts" && python fetch_github_info.py "${TEST_REPO}")

if echo "$FETCH_OUTPUT" | grep -q '"name"'; then
    echo "✓ fetch_github_info.py 成功"
    echo "  仓库名称: $(echo "$FETCH_OUTPUT" | grep -o '"name": "[^"]*"' | cut -d'"' -f4)"
else
    echo "✗ fetch_github_info.py 失败"
    echo "$FETCH_OUTPUT"
    exit 1
fi

# 步骤 2: extract_patterns.py
echo
echo "步骤 2: 提取编程范式..."
EXTRACT_OUTPUT=$(cd "${SCRIPT_DIR}/../github-to-skills/scripts" && echo "$FETCH_OUTPUT" | python extract_patterns.py)

if echo "$EXTRACT_OUTPUT" | grep -q "type: knowledge-addon"; then
    echo "✓ extract_patterns.py 成功"
    echo "  生成 knowledge-addon 格式"
else
    echo "✗ extract_patterns.py 失败"
    exit 1
fi

# 步骤 3: 验证输出格式
echo
echo "步骤 3: 验证输出格式..."

# 检查必要的字段
REQUIRED_FIELDS=(
    "type: knowledge-addon"
    "target_skill: programming-assistant"
    "source_repo:"
    "source_hash:"
    "## 项目架构"
    "## 代码规范"
    "## 技术栈"
    "## 最佳实践"
)

ALL_PASS=true
for field in "${REQUIRED_FIELDS[@]}"; do
    if echo "$EXTRACT_OUTPUT" | grep -q "$field"; then
        echo "  ✓ 找到: $field"
    else
        echo "  ✗ 缺少: $field"
        ALL_PASS=false
    fi
done

if [ "$ALL_PASS" = true ]; then
    echo
    echo "=========================================="
    echo "✓ 学习流程测试通过"
    echo "=========================================="
    exit 0
else
    echo
    echo "=========================================="
    echo "✗ 学习流程测试失败"
    echo "=========================================="
    exit 1
fi

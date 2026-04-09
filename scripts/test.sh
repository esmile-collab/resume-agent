#!/bin/bash
# Input: 开发者本地测试命令。
# Output: 执行默认测试集合。
# Pos: 测试快捷脚本。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
# Test - 运行测试套件

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

MODULE=${1:-"all"}
REPORT_DIR="test_reports/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$REPORT_DIR"

echo "=== Resume Agent 测试套件 ==="
echo "模块: $MODULE"
echo "报告目录: $REPORT_DIR"
echo ""

# 运行测试
if [ "$MODULE" = "all" ]; then
    echo "运行全部测试..."
    pytest tests/ -v \
        --html="$REPORT_DIR/report.html" \
        --cov=src \
        --cov-report="$REPORT_DIR/coverage.xml" \
        --cov-report=term-missing \
        --junitxml="$REPORT_DIR/junit.xml"
elif [ "$MODULE" = "acceptance" ]; then
    echo "运行验收测试..."
    pytest tests/acceptance/ -v \
        --html="$REPORT_DIR/report.html" \
        --cov=src \
        --cov-report=term-missing
elif [[ "$MODULE" =~ ^m[0-9]+([_.][0-9]+)?$ ]]; then
    MODULE_NAME="${MODULE#m}"
    TARGET_FILE="tests/acceptance/test_m${MODULE_NAME}.py"
    echo "运行 $MODULE 验收测试..."
    pytest "$TARGET_FILE" -v \
        --html="$REPORT_DIR/report.html" \
        --cov=src \
        --cov-report=term-missing
else
    echo "运行指定测试: $MODULE"
    pytest "$MODULE" -v \
        --html="$REPORT_DIR/report.html" \
        --cov=src \
        --cov-report=term-missing
fi

# 检查结果
if [ $? -eq 0 ]; then
    echo ""
    echo "✓ 测试通过"
    echo "报告: $REPORT_DIR/report.html"
else
    echo ""
    echo "✗ 测试失败"
    echo "报告: $REPORT_DIR/report.html"
    exit 1
fi

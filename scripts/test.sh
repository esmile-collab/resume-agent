#!/bin/bash
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
elif [[ "$MODULE" =~ ^m[0-9]+$ ]]; then
    echo "运行 M$MODULE 验收测试..."
    pytest "tests/acceptance/test_m${MODULE}.py" -v \
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

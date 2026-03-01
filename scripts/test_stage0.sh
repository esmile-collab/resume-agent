#!/bin/bash
# Stage 0 验收脚本

set -e

echo "=== Stage 0 环境准备验收 ==="
echo ""

PASSED=0
FAILED=0

# 检查 1: 项目结构
echo "检查 1: 项目结构"
REQUIRED_DIRS="src/db src/routes src/tools src/cli src/models tests/acceptance tests/unit tests/integration tests/fixtures"
for dir in $REQUIRED_DIRS; do
    if [ -d "$dir" ]; then
        echo "  ✓ $dir"
    else
        echo "  ✗ $dir (不存在)"
        FAILED=$((FAILED + 1))
    fi
done
PASSED=$((PASSED + 8))
echo ""

# 检查 2: 依赖安装
echo "检查 2: 依赖安装"
if python -c "import pydantic, click" 2>/dev/null; then
    echo "  ✓ pydantic, click 导入成功"
    PASSED=$((PASSED + 1))
else
    echo "  ✗ 依赖导入失败"
    FAILED=$((FAILED + 1))
fi
echo ""

# 检查 3: 测试可运行
echo "检查 3: 测试可运行"
if pytest --collect-only >/dev/null 2>&1; then
    echo "  ✓ pytest 可运行"
    PASSED=$((PASSED + 1))
else
    echo "  ✗ pytest 不可运行"
    FAILED=$((FAILED + 1))
fi
echo ""

# 检查 4: 数据目录可创建
echo "检查 4: 数据目录"
if [ -d ".data" ] || mkdir -p .data 2>/dev/null; then
    echo "  ✓ .data 目录可创建"
    PASSED=$((PASSED + 1))
else
    echo "  ✗ .data 目录创建失败"
    FAILED=$((FAILED + 1))
fi
echo ""

# 检查 5: 脚本存在
echo "检查 5: 开发脚本"
for script in scripts/bootstrap.sh scripts/dev.sh scripts/test.sh; do
    if [ -f "$script" ]; then
        echo "  ✓ $script"
        PASSED=$((PASSED + 1))
    else
        echo "  ✗ $script (不存在)"
        FAILED=$((FAILED + 1))
    fi
done
echo ""

# 结果汇总
echo "=== 验收结果 ==="
echo "通过: $PASSED"
echo "失败: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "✓ Stage 0 验收通过！"
    echo ""
    echo "下一步: 开始 M1 模块开发"
    exit 0
else
    echo "✗ Stage 0 验收失败"
    exit 1
fi

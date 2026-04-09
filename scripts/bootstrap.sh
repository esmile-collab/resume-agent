#!/bin/bash
# Input: 开发者手动执行和本地环境初始化流程。
# Output: 搭建基础开发环境。
# Pos: 环境初始化脚本。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
# Bootstrap - 初始化开发环境

set -e

echo "=== Resume Agent Bootstrap ==="

# 检查 Python 版本
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo "Python 版本: $PYTHON_VERSION"

# 检查是否 >=3.11
MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || [ "$MAJOR" -eq 3 -a "$MINOR" -lt 11 ]; then
    echo "✗ Python 版本过低，需要 >= 3.11"
    exit 1
fi

echo "✓ Python 版本满足要求"

# 创建数据目录
mkdir -p .data
echo "✓ 数据目录已创建: .data/"

# 安装依赖
echo "安装项目依赖..."
pip install --upgrade pip
pip install -e .
echo "✓ 依赖安装完成"

# 安装开发依赖
echo "安装开发依赖..."
pip install pytest pytest-cov pytest-html pytest-asyncio black mypy
echo "✓ 开发依赖安装完成"

# 验证安装
echo ""
echo "=== 验证安装 ==="
python -c "import click, pydantic; print('✓ 依赖导入成功')"
pytest --version >/dev/null 2>&1 && echo "✓ pytest 已安装"

# 运行 hello flow 测试
echo ""
echo "=== 运行 Hello Flow 测试 ==="
python -c "
import sys
sys.path.insert(0, 'src')
from db import models
print('✓ 模块导入成功')
print('')
print('Bootstrap 完成！')
print('可以运行: ./scripts/dev.sh 开始开发')
"

echo ""
echo "=== Bootstrap 完成 ==="

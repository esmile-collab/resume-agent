#!/bin/bash
# Input: 本地开发者与 shell 环境。
# Output: 启动开发态工作流。
# Pos: 开发辅助脚本。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
# Dev - 开发模式启动

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=== Resume Agent Dev Mode ==="

# 激活虚拟环境（如果存在）
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✓ 虚拟环境已激活"
fi

# 显示当前 Python 环境
echo "Python: $(python --version)"
echo "工作目录: $PROJECT_ROOT"

# 检查数据目录
if [ ! -d ".data" ]; then
    echo "⚠ 数据目录不存在，运行 bootstrap..."
    ./scripts/bootstrap.sh
fi

echo ""
echo "可用命令:"
echo "  - resume_agent project init --name <name>     创建项目"
echo "  - resume_agent project list                   列出项目"
echo "  - pytest tests/ -v                           运行测试"
echo ""
echo "开发模式就绪！"

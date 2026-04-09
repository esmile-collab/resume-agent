# Input: Python 基础镜像、仓库源码和启动命令。
# Output: 提供可构建的后端容器镜像。
# Pos: 根目录部署文件。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
# 用于 Render / Railway / Fly.io 部署
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制代码
COPY pyproject.toml README.md ./
COPY src/ ./src/

# 安装 Python 依赖
RUN pip install --no-cache-dir -e .

# 创建数据目录
RUN mkdir -p /app/.data/artifacts

# 初始化数据库
RUN resume_agent init-db || true

ENV PORT=8000
ENV HOST=0.0.0.0

EXPOSE 8000

CMD ["resume_agent", "serve", "--host", "0.0.0.0", "--port", "8000"]

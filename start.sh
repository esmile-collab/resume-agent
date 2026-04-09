#!/bin/bash
# Input: 本地 shell 环境、前后端端口与虚拟环境状态。
# Output: 一键启动前后端并初始化数据库。
# Pos: 根目录本地启动入口。
# Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODE="${1:-all}"

if [ -f "${ROOT_DIR}/.env" ]; then
  set -a
  . "${ROOT_DIR}/.env"
  set +a
fi

BACKEND_HOST="${RESUME_AGENT_HOST:-127.0.0.1}"
BACKEND_PORT="${RESUME_AGENT_PORT:-8000}"
FRONTEND_HOST="${RESUME_AGENT_FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${RESUME_AGENT_FRONTEND_PORT:-5173}"
VITE_API_BASE_URL="${VITE_API_BASE_URL:-http://${BACKEND_HOST}:${BACKEND_PORT}}"

resolve_venv_python() {
  local candidates=()
  while IFS= read -r candidate; do
    candidates+=("${candidate}")
  done < <(find "${ROOT_DIR}/.venv/bin" -maxdepth 1 -type f -name 'python3.*' | sort -V)

  if [ "${#candidates[@]}" -gt 0 ]; then
    printf '%s\n' "${candidates[-1]}"
    return
  fi
  if [ -x "${ROOT_DIR}/.venv/bin/python3" ]; then
    printf '%s\n' "${ROOT_DIR}/.venv/bin/python3"
    return
  fi
  if [ -x "${ROOT_DIR}/.venv/bin/python" ]; then
    printf '%s\n' "${ROOT_DIR}/.venv/bin/python"
  fi
}

PYTHON_BIN="$(resolve_venv_python)"
if [ ! -x "${PYTHON_BIN}" ]; then
  if ! command -v python3 >/dev/null 2>&1; then
    echo "未找到 python3，无法自动创建虚拟环境。"
    exit 1
  fi
  echo "创建虚拟环境..."
  python3 -m venv "${ROOT_DIR}/.venv"
  PYTHON_BIN="$(resolve_venv_python)"
fi

RESUME_AGENT_BIN="${ROOT_DIR}/.venv/bin/resume_agent"
if [ ! -x "${RESUME_AGENT_BIN}" ]; then
  echo "安装后端依赖..."
  "${PYTHON_BIN}" -m pip install -e "${ROOT_DIR}"
fi

if ! command -v npm >/dev/null 2>&1; then
  if [ "${MODE}" = "frontend" ] || [ "${MODE}" = "all" ]; then
    echo "未找到 npm，无法启动前端。"
    exit 1
  fi
fi

if [ "${MODE}" = "frontend" ] || [ "${MODE}" = "all" ]; then
  if [ ! -d "${ROOT_DIR}/frontend/node_modules" ]; then
    echo "安装前端依赖..."
    (cd "${ROOT_DIR}/frontend" && npm install)
  fi
fi

echo "初始化数据库..."
"${RESUME_AGENT_BIN}" init-db >/dev/null

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  if [ -n "${BACKEND_PID}" ]; then
    kill "${BACKEND_PID}" >/dev/null 2>&1 || true
  fi
  if [ -n "${FRONTEND_PID}" ]; then
    kill "${FRONTEND_PID}" >/dev/null 2>&1 || true
  fi
}

trap cleanup INT TERM EXIT

if [ "${MODE}" = "backend" ] || [ "${MODE}" = "all" ]; then
  echo "启动后端: http://${BACKEND_HOST}:${BACKEND_PORT}"
  "${RESUME_AGENT_BIN}" serve --host "${BACKEND_HOST}" --port "${BACKEND_PORT}" --reload &
  BACKEND_PID=$!
fi

if [ "${MODE}" = "frontend" ] || [ "${MODE}" = "all" ]; then
  echo "启动前端: http://${FRONTEND_HOST}:${FRONTEND_PORT}"
  export VITE_API_BASE_URL
  (
    cd "${ROOT_DIR}/frontend"
    npm run dev -- --host "${FRONTEND_HOST}" --port "${FRONTEND_PORT}"
  ) &
  FRONTEND_PID=$!
fi

echo ""
echo "运行模式: ${MODE}"
echo "后端地址: http://${BACKEND_HOST}:${BACKEND_PORT}"
if [ "${MODE}" = "frontend" ] || [ "${MODE}" = "all" ]; then
  echo "前端地址: http://${FRONTEND_HOST}:${FRONTEND_PORT}"
  echo "前端 API: ${VITE_API_BASE_URL}"
fi
echo "按 Ctrl+C 停止服务"

wait

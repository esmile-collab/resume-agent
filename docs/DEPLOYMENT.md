<!--
Input: 当前系统边界、运行方式与文档索引。
Output: 输出文档《部署指南》的说明内容。
Pos: 仓库级说明文档。
Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
-->
# 部署指南

当前推荐部署形态：

1. 前端：Vercel
2. 后端：Render
3. 持久化：Render Disk 挂载 `.data/`

## 1. 后端部署到 Render

核心要求：

1. `buildCommand`：`pip install -e .`
2. `startCommand`：`sh -c "resume_agent init-db && resume_agent serve --host 0.0.0.0 --port $PORT"`
3. 挂载可写磁盘到 `/opt/render/project/.data`

建议环境变量：

```bash
PORT=8000
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
LLM_MODEL=claude-3.5-sonnet
```

## 2. 前端部署到 Vercel

前端构建前需要指定后端地址：

```bash
VITE_API_BASE_URL=https://your-render-service.onrender.com
```

本地验证构建：

```bash
cd frontend
npm install
npm run build
```

## 3. 上线前检查

1. `resume_agent serve` 能在本地启动。
2. `python -m pytest tests/acceptance tests/unit/test_fractal_docs.py` 通过。
3. 前端 `npm run build` 通过。
4. Render 实例具备可写 `.data/` 目录。
5. 后端 `/health` 可访问。

## 4. 当前限制

1. 当前持久化依赖本地磁盘，不适合多实例共享写入。
2. 免费 Render 有冷启动，首次请求会慢。
3. 评分器如果依赖外部 LLM，需要同步配置对应 API Key。

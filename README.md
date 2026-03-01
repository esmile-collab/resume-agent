# Resume Agent

智能简历优化系统 - 基于 Agent 的简历 JD 匹配与优化工具。

## 项目结构

```
.
├── src/                # 源代码
│   ├── db/            # 数据库层
│   ├── routes/        # 路由层
│   ├── tools/         # 工具模块
│   └── cli/           # 命令行接口
├── tests/             # 测试
├── docs/              # 文档
└── config/            # 配置文件
```

## 安装

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -e .
```

## 开发

参见 [docs/开发快速开始.md](docs/开发快速开始.md)

## 文档

- [开发流程规范](docs/开发流程规范.md)
- [模块验收标准](docs/模块验收标准.md)
- [测试与回滚机制](docs/测试与回滚机制.md)

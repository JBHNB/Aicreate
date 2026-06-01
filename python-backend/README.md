# AI 爆款文章创作器 - Python 后端

基于 FastAPI，与编程导航「Spring AI + 多 Agent」教程 Python 版对齐。

## 本地运行

1. 复制 `.env.example` 为 `.env` 并填写 MySQL、Redis 等配置。
2. 可选：在 `.env` 中配置 **`DASHSCOPE_API_KEY`**（阿里云百炼），则 `POST /api/passage/generate` 会调用通义千问；不配则为占位正文。
3. 执行 `sql/create_table.sql` 初始化数据库；再执行 `sql/passage_table.sql` 创建创作记录表。
4. 安装依赖并启动（无 `uv` 时用 `pip install -e .`）：

```bash
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8567
```

5. 接口文档：<http://localhost:8567/docs>；SSE 演示：`GET /api/passage/stream/demo`（需登录 Cookie）。

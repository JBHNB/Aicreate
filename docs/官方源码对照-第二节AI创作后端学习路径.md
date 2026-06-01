# 对照官方源码：第二节「AI 核心创作流程 · 后端」学习路径

官方仓库：<https://github.com/yuyuanweb/ai-passage-creator>（编程导航配套开源，含 Java / Go / **Python**）。

Python 后端目录：**`python-backend/`**。第二节讲的核心能力在这里都能找到对应代码。

---

## 一、官方实现整体在干什么（先建立心智模型）

1. 用户提交 **选题** → 后端创建 **`task_id`**（文章任务），写入 **`article` 表**，并检查 VIP 配额等。  
2. **`asyncio.create_task`** 后台跑 **阶段 1**：多智能体生成 **标题方案**。  
3. 前端连 **`GET /api/article/progress/{task_id}`**，拿到 **SSE**；后端用 **`asyncio.Queue`** 往连接里 **推送进度/片段**。  
4. 用户 **确认标题** → 触发 **阶段 2**（大纲）；**确认大纲** → 触发 **阶段 3**（正文 + 配图分析 + 配图 + 合并）。  
5. **`ArticleAgentOrchestrator`** 按阶段调用 **Title / Outline / Content / ImageAnalyzer / 配图与合并**；具体 LLM 调用在 **`article_agent_service.py`** 与各 **`agent/agents/*.py`**。

你本地练习仓库里的 **`passage` 一次生成**是 **简化版**：没有 `task_id` 多阶段、没有完整 `article` 状态机，但 **DashScope / SSE 思路**可对齐。

---

## 二、建议阅读顺序（打开 GitHub 网页或 clone 到本地跟读）

| 顺序 | 路径 | 学什么 |
|------|------|--------|
| 1 | [`app/routers/article.py`](https://github.com/yuyuanweb/ai-passage-creator/blob/main/python-backend/app/routers/article.py) | HTTP 入口：`/create` 创建任务 + `create_task` 启异步；`/progress/{task_id}` 挂 SSE；确认标题/大纲等接口 |
| 2 | [`app/managers/sse_manager.py`](https://github.com/yuyuanweb/ai-passage-creator/blob/main/python-backend/app/managers/sse_manager.py) | **`asyncio.Queue` + `StreamingResponse`**，教程里「SSE + Queue」的直接对应 |
| 3 | [`app/services/article_async_service.py`](https://github.com/yuyuanweb/ai-passage-creator/blob/main/python-backend/app/services/article_async_service.py) | **phase1 / phase2 / phase3** 异步任务怎么串起来 |
| 4 | [`app/agent/orchestrator.py`](https://github.com/yuyuanweb/ai-passage-creator/blob/main/python-backend/app/agent/orchestrator.py) | **多智能体编排**：各阶段调哪个 Agent |
| 5 | [`app/services/article_agent_service.py`](https://github.com/yuyuanweb/ai-passage-creator/blob/main/python-backend/app/services/article_agent_service.py) | **核心业务**：状态、调模型、写库、往 SSE 发消息（文件较长，分段读） |
| 6 | [`app/agent/agents/`](https://github.com/yuyuanweb/ai-passage-creator/tree/main/python-backend/app/agent/agents) | 每个 Agent 一个文件：`title_generator`、`outline_generator` 等 |
| 7 | [`sql/`](https://github.com/yuyuanweb/ai-passage-creator/tree/main/sql) | **`article` 表结构**、状态字段与教程一致 |

---

## 三、和你当前仓库 `aicreate/python-backend` 的对应关系

| 官方仓库 | 你的练习仓库（简化） |
|----------|----------------------|
| `article` + `task_id` + 多阶段 | `passage` 表 + **单次** `generate` |
| `sse_manager` + `/progress/{task_id}` | `GET /api/passage/stream/demo`（演示向） |
| `article_agent_service` + `agent/*` | `utils/llm.py` **单次**补全正文 |
| OpenAI 兼容 + DashScope | 已在 `.env` 用 **`DASHSCOPE_API_KEY`** 对齐思路 |

进阶路线：先把官方 **`sse_manager.py`** 读懂 → 再在本地把「演示 SSE」 upgrade 成「按 task 推送」；再借鉴 **`orchestrator`** 拆 **多步 Agent**。

---

## 四、本地如何把官方代码放进 Cursor 对照

在项目外（或子目录）克隆只读对照：

```bash
git clone --depth 1 https://github.com/yuyuanweb/ai-passage-creator.git
```

用 Cursor 同时打开 **`aicreate`** 与 **`ai-passage-creator/python-backend`**，左右对照 **`article.py`** 与你的 **`passage.py`**。

---

## 五、依赖与环境

官方 **`python-backend/pyproject.toml`**、**`.env.example`** 比练习项目多（COS、Pexels、Stripe 等）。**第二节精读**可先看 **`article` + `agent` + `managers`**，其它服务目录可放到后面章节再读。

---

*文档仅做学习路径索引；版权与更新以官方仓库为准。*

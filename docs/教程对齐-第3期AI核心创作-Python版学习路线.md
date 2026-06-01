# 教程对齐：第 3 期「AI 核心创作流程 · 后端」（Python 版学习路线）

**官方小节链接（编程导航 · Python 第二节）：**  
<https://www.codefather.cn/course/2031299079576838146/section/2031347715568394242>

你已完成 [第 1 小节：项目初始化 + 用户模块](https://www.codefather.cn/course/2031299079576838146/section/2031347765681938433) 对应的 **Python 全栈基础**（用户、Session、前后端联调等）。

编程导航课程大纲里，**紧接着的一期**是：

> **第 3 期：AI 核心创作流程 · 后端**  
> Spring AI Alibaba 入门、智能体 1～5、**SSE 流式推送**、**异步任务**、**文章管理接口（CRUD）** 等。

本站为 **Spring / Java 主教程**；本仓库走 **FastAPI + Python**，不必安装 Spring AI，但**业务目标与顺序**建议与大纲一致，便于对照视频与笔记。

---

## 一、Java 教程名词 → Python 常见替代

| 教程（Java） | Python / 本仓库思路 |
|--------------|---------------------|
| Spring AI Alibaba、多智能体 | **LangChain / LangGraph**、或自研「多步函数 + 状态 dict」；先从 **单模型 HTTP 调用** 再演进 |
| `SseEmitter`（SSE） | FastAPI **`StreamingResponse`** + `text/event-stream`，或 **Starlette `EventSourceResponse`** |
| `@Async` + 线程池 | **`asyncio.create_task`**、`BackgroundTasks`、或 **Celery / ARQ**（重任务再上队列） |
| MyBatis / JPA | 当前：**`databases` + SQLAlchemy Core 表对象**（`Passage.__table__`） |
| 文章实体 CRUD | **`PassageService` + `passage` 路由**：生成、查、列表、**更新、软删** |
| 通义 / DashScope | **`httpx` 调兼容接口** `app/utils/llm.py`，`.env` 中 `DASHSCOPE_API_KEY` |
| SSE 入门 | **`GET /api/passage/stream/demo`**（`StreamingResponse` + `text/event-stream`） |

---

## 二、本仓库已落地的「第 3 期前半」对照

| 教程要点 | 本仓库实现 |
|----------|------------|
| 文章 CRUD | `POST/GET` 见 `passage` 路由；`POST /api/passage/update`、`POST /api/passage/delete` |
| 单次大模型生成正文 | 配置 **`DASHSCOPE_API_KEY`** 后，`POST /api/passage/generate` 走百炼兼容接口；未配置则占位文案 |
| SSE 流式（入门） | **`GET /api/passage/stream/demo`**（需登录），前端可用 `EventSource` 连 `/api/passage/stream/demo` |

环境变量见 **`python-backend/.env.example`**：`DASHSCOPE_API_KEY`、`LLM_MODEL`（默认 `qwen-turbo`）。

---

## 三、第 3 期建议学习顺序（Python 版）

1. **文章域模型与权限**（已部分完成）  
   - 表 `passage`：`userId` 归属、`isDelete` 软删。  
   - 所有写操作必须带 **`current_user.id`**，与登录态绑定。

2. **文章管理 CRUD 补全**（与教程「文章管理接口」对齐）— **已完成**  
   - 创建：`POST /api/passage/generate`（可选真实模型）。  
   - 读：`GET /api/passage/get`、`GET /api/passage/list`。  
   - 改：`POST /api/passage/update`。  
   - 删：`POST /api/passage/delete`（软删）。

3. **接入大模型（最小闭环）**— **已完成（可选 Key）**  
   - 见 **`app/utils/llm.py`**、`resolve_generated_content`；依赖 **`httpx`**。

4. **SSE 流式推送（入门）**— **演示接口已完成**  
   - **`GET /api/passage/stream/demo`**；下一步（对照教程）：把 **模型流式 token** 接到 SSE，替代固定分块。

5. **多智能体编排（简化版）**  
   - 教程里 5 个 Agent：标题 / 大纲 / 正文 / 配图分析 / 配图执行。  
   - Python 可先做成 **同一服务内多个 async 函数顺序调用**，共享一个 **context dict**（选题、选定标题、大纲、正文），最后再落库。

6. **异步长任务（可选进阶）**  
   - 生成耗时长时：**先返回 taskId**，轮询或 WebSocket/SSE 通知完成；与教程 `@Async` 思想一致。

---

## 四、你需要自备的教程材料

- **付费小节正文**在官网需登录查看；若你像第 2 期一样导出 **Markdown / 截图**，可发我或放进 `uploads/`，我能按小节逐段对齐到本仓库实现。  
- 公开页可参考：[课程总览](https://www.codefather.cn/course/2031299079576838146) 中的 **学习大纲 → 第 3 期** 标题与能力描述。

---

## 五、与本仓库文档的关系

- 《前后端联调与实现技术总结.md》：Cookie、Redis、`Depends`、代理、统一 `code/data/message`。  
- 本文：**按官方期数**，标出 Python 下一阶段的**学习顺序与对标点**。

---

## 六、练习检查清单（第 3 期前半）

- [ ] Swagger `/docs` 中：登录 → 带 Cookie 调 `POST /passage/generate`。  
- [ ] 配置 `DASHSCOPE_API_KEY` 后再次生成，正文应为模型输出（失败则回退占位）。  
- [ ] `GET /passage/list`、`update`、`delete` 行为正确。  
- [ ] 浏览器或 curl 访问 **`GET /api/passage/stream/demo`**（需 Cookie）：能收到多条 `data:` 行并以 `[DONE]` 结束。  
- [ ] 理解：**`userId` 只来自 `require_login`**。

下一步（对齐教程深度）：**流式调用模型 + 多阶段状态字段**；可将教程第 3 期 Markdown 导出后继续逐段实现。

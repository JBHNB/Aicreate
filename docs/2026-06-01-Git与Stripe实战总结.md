# 2026-06-01 实践总结：GitHub 上传与 Stripe VIP 支付

本文档记录 2026 年 6 月 1 日在本项目（[JBHNB/Aicreate](https://github.com/JBHNB/Aicreate)）上的实战学习要点，对照官方教程仓库 [yuyuanweb/ai-passage-creator](https://github.com/yuyuanweb/ai-passage-creator)。

---

## 1. 把本地项目上传到 GitHub

### 1.1 整体流程

```
GitHub 创建空仓库 → 本地 git init → 配置 .gitignore → commit → 关联 remote → push
```

### 1.2 根目录 `.gitignore`（必做）

项目根目录需有 `.gitignore`，避免上传体积大或敏感文件：

| 必须忽略 | 原因 |
|----------|------|
| `.conda/`、`.venv/` | 本地 Python 环境，体积巨大 |
| `node_modules/` | 前端依赖，可 `npm install` 重装 |
| `.env` | 含 API Key、数据库密码 |
| `__pycache__/` | Python 缓存 |

### 1.3 首次上传命令

```powershell
cd D:\agi_code\aicreate
git init
git add .
git commit -m "Initial commit: AI article creation project"
git remote add origin https://github.com/JBHNB/Aicreate.git
git branch -M main
git push -u origin main
```

### 1.4 日常更新 GitHub

改完代码后：

```powershell
git add .
git commit -m "简要说明这次改了什么"
git push
```

**注意：** `.env` 已在 `.gitignore` 中，不会被提交；切勿把密钥推上 GitHub。

---

## 2. Git 常用操作

### 2.1 改错了怎么还原

| 状态 | 命令 |
|------|------|
| 改了文件，还没 commit | `git restore .` |
| 已 add，还没 commit | `git restore --staged .` 然后 `git restore .` |
| 已 commit，还没 push | `git reset --soft HEAD~1`（保留代码）或 `git reset --hard HEAD~1`（丢弃改动） |
| 已 push | 用 `git revert <commit>` 更安全 |

### 2.2 查看状态

```powershell
git status          # 哪些文件改了
git log --oneline   # 提交历史
git diff            # 具体改动内容
```

---

## 3. 对照官方源码继续开发

官方仓库 [ai-passage-creator](https://github.com/yuyuanweb/ai-passage-creator) 提供 Java / Go / Python 三种后端；**本仓库采用 Python 后端 + Vue 3 前端**。

### 3.1 本地进度（截至 2026-06-01）

| 模块 | 状态 |
|------|------|
| 多 Agent 创作（标题→大纲→正文→配图） | ✅ |
| SSE 流式 + 三栏创作 UI | ✅ |
| 用户登录 / 鉴权 / 文章管理 / 导出 | ✅ |
| Stripe 支付后端 | ✅ |
| VIP 购买前端（`/vip` 页面） | ✅ 已接入 |
| Reviewer 审核、任务 resume | ✅ 本地扩展 |
| 统计页 ECharts、Docker 全栈部署 | ⏳ 待做 |

### 3.2 参考目录

```
aicreate/
├── python-backend/       # 主后端（FastAPI）
├── frontend/             # 主前端（Vue 3）
├── docs/                 # 文档
└── reference-official/   # 官方源码对照（只读参考）
```

---

## 4. Stripe VIP 支付完整链路

### 4.1 两个不同的环节

| 环节 | 需要什么 | 没配置时 |
|------|----------|----------|
| **创建支付链接、跳转 Stripe 付款** | `STRIPE_API_KEY` | 点「立即升级」报错「Stripe API Key 未配置」 |
| **付款成功后自动升 VIP** | **Webhook 回调** | 钱付了，但账号仍是普通用户 |

### 4.2 `.env` 配置项

```env
STRIPE_API_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_SUCCESS_URL=http://localhost:5173/vip?success=true
STRIPE_CANCEL_URL=http://localhost:5173/vip?cancelled=true
```

改 `.env` 后**必须重启后端**，否则读不到新配置。

### 4.3 为什么需要 Stripe CLI（本地开发）

Stripe 服务器访问不到 `localhost`，本地开发时用 CLI 做「桥」：

```powershell
stripe login
stripe listen --forward-to localhost:8569/api/webhook/stripe
```

终端会输出 `whsec_...`，复制到 `.env` 的 `STRIPE_WEBHOOK_SECRET`，再重启后端。

**本地开发需同时运行三个进程：**

1. 后端 `uvicorn`
2. 前端 `npm run dev`
3. `stripe listen`（保持不关）

### 4.4 Windows 安装 Stripe CLI

1. 从 [stripe/stripe-cli releases](https://github.com/stripe/stripe-cli/releases) 下载 **`stripe_*_windows_x86_64.zip`**
2. 解压得到 `stripe.exe`
3. 把**包含 stripe.exe 的目录**加入系统 **`Path`** 变量（不是新建一个叫 `stripe` 的变量）
4. **完全退出并重启 Cursor**，新终端才能识别 `stripe` 命令

临时用法（不改 PATH）：

```powershell
D:\stripe_1.42.1_windows_x86_64\stripe.exe listen --forward-to localhost:8569/api/webhook/stripe
```

### 4.5 测试支付

1. 登录普通用户，打开 `http://localhost:5173/vip`
2. 点「立即升级」→ 跳转 Stripe
3. 测试卡号：`4242 4242 4242 4242`，任意未来日期和 CVC
4. 支付成功跳回 `/vip?success=true`

---

## 5. 如何判断账号已是 VIP

### 5.1 看页面

| 位置 | VIP 表现 |
|------|----------|
| 顶部导航 | 显示 **「VIP」**（不是「升级 VIP」） |
| `/vip` 页 | 按钮为「您已是永久会员」 |
| 创作页 | 右侧「VIP 会员 · 无限次」；AI 生图、SVG 可勾选 |

### 5.2 看接口（F12 → Network）

请求 `GET /api/user/get/login`，响应中：

```json
"userRole": "vip"
```

### 5.3 查数据库

```sql
SELECT userAccount, userRole, vipTime, quota FROM user WHERE userAccount = '你的账号';

SELECT status, createTime FROM payment_record
WHERE userId = (SELECT id FROM user WHERE userAccount = '你的账号')
ORDER BY createTime DESC;
```

| 字段 | VIP 成功时 |
|------|------------|
| `user.userRole` | `vip` |
| `user.vipTime` | 有值 |
| `payment_record.status` | `SUCCEEDED` |

---

## 6. 今天踩过的坑与修复

### 6.1 改了 `.env` 但 Stripe 仍报「未配置」

**原因：** 后端启动时一次性读取配置，改 `.env` 后不重启无效。

**处理：** Ctrl+C 停 uvicorn，重新启动。

---

### 6.2 付了钱但页面仍显示「升级 VIP」

**原因有两层：**

1. **Webhook 处理 bug**：Stripe 的 `metadata` 不是普通 dict，不能用 `.get()`，导致 `checkout.session.completed` 处理失败，数据库 `userRole` 未更新。
   - 修复文件：`python-backend/app/services/payment_service.py`（增加 `_stripe_field` 辅助函数）

2. **Redis Session 未刷新**：支付只更新了 MySQL，`GET /api/user/get/login` 仍从 Session 读旧的 `userRole: user`。
   - 修复文件：`python-backend/app/deps.py`（每次请求从数据库刷新用户信息并写回 Session）

**处理：** 重启后端后刷新页面（或重新登录）即可。

---

### 6.3 PATH 加了 stripe 目录仍找不到命令

**常见错误：** 新建了名为 `stripe` 的环境变量，而不是编辑 **`Path`** 变量。

**处理：** 在 `Path` 里新增一行目录路径；改完后**完全退出 Cursor 再打开**。

---

### 6.4 `payment_record` 全是 PENDING

说明创建了支付会话，但 Webhook 未成功处理。检查：

- `stripe listen` 是否在运行
- `STRIPE_WEBHOOK_SECRET` 是否与 `listen` 输出一致
- 后端是否已重启并加载修复后的代码

---

## 7. 本次代码变更摘要

| 提交 / 改动 | 内容 |
|-------------|------|
| 接入 VIP 会员页 | `frontend/src/pages/VipPage.vue`、`api/payment.ts`、路由 `/vip`、Header「升级 VIP」 |
| Stripe Webhook 修复 | `payment_service.py` 正确读取 Stripe metadata |
| Session 刷新 | `deps.py` 每次请求同步数据库最新 userRole |
| 启动日志 | `main.py` 打印 stripe_key / webhook 是否已配置 |

---

## 8. 后续可继续做的

1. **统计页 ECharts 可视化** — 对照官方 `StatisticsPage.vue`
2. **Docker 全栈部署** — 对照官方 `Dockerfile` + `docker-compose.yml`
3. **首页 UI** — 对照官方营销风首页

---

## 9. 相关文档

| 文档 | 说明 |
|------|------|
| [从零开发手册.md](./从零开发手册.md) | 项目全貌、环境、日常开发 |
| [前端命令手册.md](./前端命令手册.md) | 端口、npm 命令 |
| 官方 [STRIPE_SETUP.md](https://github.com/yuyuanweb/ai-passage-creator/blob/main/STRIPE_SETUP.md) | Stripe 官方配置说明 |
| 官方 [VIP_FEATURES.md](https://github.com/yuyuanweb/ai-passage-creator/blob/main/VIP_FEATURES.md) | VIP 权益说明 |

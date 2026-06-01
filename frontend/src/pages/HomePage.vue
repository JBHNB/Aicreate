<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { RouterLink, useRouter } from 'vue-router'

import { useLoginUserStore } from '@/stores/loginUser'

const router = useRouter()
const loginUserStore = useLoginUserStore()
const { loginUser } = storeToRefs(loginUserStore)

const docsUrl = 'http://127.0.0.1:8567/docs'

const features = [
  {
    key: 'user',
    title: '用户模块',
    desc: '注册、登录、Session 与角色权限；管理员可进入用户管理。',
    action: '去登录',
    path: '/user/login',
    secondary: { label: '注册', path: '/user/register' },
  },
  {
    key: 'api',
    title: '接口文档',
    desc: 'FastAPI 自动生成的 OpenAPI / Swagger，联调与自测接口。',
    action: '打开文档',
    external: docsUrl,
  },
  {
    key: 'data',
    title: '数据持久化',
    desc: 'MySQL 存储业务数据，Redis 管理会话；与教程后端栈一致。',
    action: '了解项目',
    path: '/about',
  },
] as const
</script>

<template>
  <div class="home">
    <section class="hero">
      <p class="hero-tag">项目模板</p>
      <h1 class="hero-title">FastAPI + Vue 全栈项目初始化</h1>
      <p class="hero-sub">
        AI 爆款文章创作器 · 与编程导航「Spring AI + 多 Agent」教程流程对齐（后端为 Python 版）
      </p>
    </section>

    <a-card class="welcome-card" :bordered="false">
      <div class="welcome-inner">
        <h2 class="welcome-title">欢迎使用</h2>
        <p v-if="!loginUser" class="welcome-desc">
          请先注册或登录，再使用 AI 创作与我的文章等功能。
        </p>
        <p v-else class="welcome-desc">
          你好，<strong>{{ loginUserStore.displayName() }}</strong>，可以开始创作或查看历史文章。
        </p>

        <a-space v-if="!loginUser" size="middle" wrap class="welcome-actions">
          <a-button type="primary" size="large" @click="router.push('/user/login')">登录</a-button>
          <a-button size="large" @click="router.push('/user/register')">注册</a-button>
        </a-space>
        <a-space v-else size="middle" wrap class="welcome-actions">
          <a-button type="primary" size="large" @click="router.push('/article/create')">
            多阶段 AI 创作
          </a-button>
          <a-button size="large" @click="router.push('/article/list')">创作历史</a-button>
          <a-button size="large" @click="router.push('/passage/my')">简易文章</a-button>
        </a-space>

        <a-collapse v-if="loginUser" ghost class="account-collapse">
          <a-collapse-panel key="1" header="当前账号信息">
            <a-descriptions bordered size="small" :column="1">
              <a-descriptions-item label="显示名">
                {{ loginUserStore.displayName() }}
              </a-descriptions-item>
              <a-descriptions-item label="登录账号">
                {{ loginUser!.userAccount }}
              </a-descriptions-item>
              <a-descriptions-item label="用户 ID">{{ loginUser!.id }}</a-descriptions-item>
              <a-descriptions-item label="角色">{{ loginUser!.userRole }}</a-descriptions-item>
            </a-descriptions>
          </a-collapse-panel>
        </a-collapse>
      </div>
    </a-card>

    <a-row :gutter="[20, 20]" class="feature-row">
      <a-col :xs="24" :sm="24" :md="8" v-for="item in features" :key="item.key">
        <a-card class="feature-card" hoverable>
          <div class="feature-icon" aria-hidden="true">
            <span v-if="item.key === 'user'">👤</span>
            <span v-else-if="item.key === 'api'">📄</span>
            <span v-else>💾</span>
          </div>
          <h3 class="feature-title">{{ item.title }}</h3>
          <p class="feature-desc">{{ item.desc }}</p>
          <div class="feature-footer">
            <template v-if="item.key === 'user'">
              <RouterLink class="feature-link" :to="item.path">{{ item.action }}</RouterLink>
              <span class="dot">·</span>
              <RouterLink
                v-if="'secondary' in item && item.secondary"
                class="feature-link"
                :to="item.secondary.path"
              >
                {{ item.secondary.label }}
              </RouterLink>
            </template>
            <a
              v-else-if="'external' in item && item.external"
              :href="item.external"
              target="_blank"
              rel="noopener noreferrer"
              class="feature-link"
            >
              {{ item.action }}
            </a>
            <RouterLink v-else class="feature-link" :to="item.path">{{ item.action }}</RouterLink>
          </div>
        </a-card>
      </a-col>
    </a-row>

    <p class="foot-note">
      生成 TS 接口：先启动后端，在项目根执行 <code>npm run openapi2ts</code>，输出在
      <code>src/services</code>。
    </p>
  </div>
</template>

<style scoped>
.home {
  max-width: 960px;
  margin: 0 auto;
}

.hero {
  text-align: center;
  padding: 28px 16px 20px;
  margin: -8px -16px 20px;
  border-radius: 12px;
  background: linear-gradient(180deg, #f0f5ff 0%, #fafafa 100%);
  border: 1px solid #e6f0ff;
}

.hero-tag {
  margin: 0 0 8px;
  font-size: 13px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #1677ff;
  font-weight: 600;
}

.hero-title {
  margin: 0 0 10px;
  font-size: 1.65rem;
  font-weight: 700;
  color: rgba(0, 0, 0, 0.88);
  line-height: 1.35;
}

.hero-sub {
  margin: 0;
  font-size: 14px;
  color: rgba(0, 0, 0, 0.55);
  max-width: 560px;
  margin-left: auto;
  margin-right: auto;
  line-height: 1.6;
}

.welcome-card {
  margin-bottom: 28px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.welcome-inner {
  text-align: center;
  padding: 8px 8px 4px;
}

.welcome-title {
  margin: 0 0 12px;
  font-size: 1.35rem;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.88);
}

.welcome-desc {
  margin: 0 0 20px;
  color: rgba(0, 0, 0, 0.55);
  font-size: 14px;
  line-height: 1.6;
}

.welcome-actions {
  justify-content: center;
}

.account-collapse {
  margin-top: 20px;
  text-align: left;
  max-width: 480px;
  margin-left: auto;
  margin-right: auto;
}

.feature-row {
  margin-bottom: 24px;
}

.feature-card {
  height: 100%;
  min-height: 220px;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
}

.feature-icon {
  font-size: 2rem;
  line-height: 1;
  margin-bottom: 12px;
}

.feature-title {
  margin: 0 0 10px;
  font-size: 1.05rem;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.88);
}

.feature-desc {
  margin: 0 0 16px;
  flex: 1;
  font-size: 13px;
  color: rgba(0, 0, 0, 0.55);
  line-height: 1.55;
}

.feature-footer {
  margin-top: auto;
  padding-top: 4px;
}

.feature-link {
  color: #1677ff;
  font-weight: 500;
  font-size: 14px;
}

.feature-link:hover {
  color: #4096ff;
}

.dot {
  margin: 0 6px;
  color: rgba(0, 0, 0, 0.25);
}

.foot-note {
  text-align: center;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  margin: 0;
  line-height: 1.6;
}

.foot-note code {
  font-size: 12px;
}
</style>

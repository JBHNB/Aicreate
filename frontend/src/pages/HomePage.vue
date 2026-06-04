<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import {
  ClockCircleOutlined,
  EditOutlined,
  FileTextOutlined,
  OrderedListOutlined,
  PictureOutlined,
  RightOutlined,
  RocketOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons-vue'

import { listArticle } from '@/api/article'
import { useLoginUserStore } from '@/stores/loginUser'
import type { ArticleVO } from '@/types/article'

const router = useRouter()
const loginUserStore = useLoginUserStore()

const topic = ref('')
const recentArticles = ref<ArticleVO[]>([])
const loadingArticles = ref(false)

const features = [
  {
    icon: FileTextOutlined,
    title: '智能生成标题',
    description: 'AI 自动分析选题，生成吸引眼球的爆款标题',
    color: '#22C55E',
  },
  {
    icon: OrderedListOutlined,
    title: '自动生成大纲',
    description: '智能规划文章结构，确保逻辑清晰完整',
    color: '#3B82F6',
  },
  {
    icon: EditOutlined,
    title: '流式生成正文',
    description: '实时展示创作过程，体验打字机般的流畅输出',
    color: '#8B5CF6',
  },
  {
    icon: PictureOutlined,
    title: '智能配图',
    description: '多种配图策略自动选择，图文并茂',
    color: '#F59E0B',
  },
  {
    icon: ThunderboltOutlined,
    title: '快速高效',
    description: '5-10 分钟完成全文创作，效率提升 10 倍',
    color: '#EF4444',
  },
  {
    icon: ClockCircleOutlined,
    title: '历史管理',
    description: '随时查看和管理所有创作记录，支持导出',
    color: '#06B6D4',
  },
] as const

function goToCreate() {
  if (topic.value.trim()) {
    router.push({ path: '/article/create', query: { topic: topic.value.trim() } })
  } else {
    router.push('/article/create')
  }
}

function goToList() {
  router.push('/article/list')
}

function viewArticle(article: ArticleVO) {
  router.push(`/article/${article.taskId}`)
}

function formatTime(time?: string) {
  if (!time) return '--'
  return dayjs(time).format('MM-DD HH:mm')
}

function statusLabel(status: string) {
  if (status === 'COMPLETED') return '已完成'
  if (status === 'PROCESSING') return '生成中'
  if (status === 'FAILED') return '失败'
  return '等待中'
}

function statusClass(status: string) {
  if (status === 'COMPLETED') return 'status-completed'
  if (status === 'PROCESSING') return 'status-processing'
  if (status === 'FAILED') return 'status-failed'
  return 'status-pending'
}

async function loadRecentArticles() {
  if (!loginUserStore.loginUser?.id) return
  loadingArticles.value = true
  try {
    const page = await listArticle({ current: 1, pageSize: 6 })
    recentArticles.value = page.records || []
  } catch (error) {
    console.error('加载文章失败:', error)
  } finally {
    loadingArticles.value = false
  }
}

onMounted(() => {
  void loadRecentArticles()
})
</script>

<template>
  <div id="homePage" class="home-page">
    <!-- Hero -->
    <section class="hero-section">
      <div class="hero-bg" aria-hidden="true" />
      <div class="container">
        <div class="hero-badge">
          <RocketOutlined />
          AI 驱动的内容创作平台
        </div>
        <h1 class="hero-title">AI 爆款文章创作器</h1>
        <p class="hero-subtitle">让每个人都能写出 10 万+ 阅读量的文章</p>

        <div class="input-wrapper">
          <a-input
            v-model:value="topic"
            class="topic-input"
            placeholder="输入你想创作的主题，例如：2026 年 AI 如何改变职场"
            size="large"
            @press-enter="goToCreate"
          >
            <template #prefix>
              <EditOutlined class="input-icon" />
            </template>
          </a-input>
          <a-button type="primary" class="cta-btn" size="large" @click="goToCreate">
            <RocketOutlined />
            开始创作
          </a-button>
        </div>
        <p class="hero-tips">工作总结、心得体会、演讲稿、分析报告… 一键生成</p>
      </div>
    </section>

    <!-- Features -->
    <section class="features-section">
      <div class="container">
        <div class="section-header">
          <span class="section-badge">核心能力</span>
          <h2 class="section-title">专业人士的一站式 AI 写作工具</h2>
          <p class="section-subtitle">强大的 AI 能力，让创作变得简单高效</p>
        </div>
        <div class="features-grid">
          <div
            v-for="feature in features"
            :key="feature.title"
            class="feature-card"
            @click="goToCreate"
          >
            <div
              class="feature-icon-wrapper"
              :style="{ background: `${feature.color}15` }"
            >
              <component :is="feature.icon" class="feature-icon" :style="{ color: feature.color }" />
            </div>
            <div class="feature-content">
              <h3 class="feature-title">{{ feature.title }}</h3>
              <p class="feature-description">{{ feature.description }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Recent articles -->
    <section v-if="loginUserStore.loginUser?.id" class="articles-section">
      <div class="container">
        <div class="section-header-row">
          <div>
            <h2 class="section-title-sm">最近创作</h2>
            <p class="section-subtitle-sm">查看您最近创作的文章</p>
          </div>
          <a-button type="link" class="view-all-btn" @click="goToList">
            查看全部
            <RightOutlined />
          </a-button>
        </div>

        <a-spin :spinning="loadingArticles">
          <div v-if="recentArticles.length" class="articles-grid">
            <div
              v-for="article in recentArticles"
              :key="article.taskId"
              class="article-card"
              @click="viewArticle(article)"
            >
              <div class="article-cover">
                <img
                  v-if="article.coverImage"
                  :src="article.coverImage"
                  :alt="article.mainTitle || article.topic"
                />
                <div v-else class="cover-placeholder">
                  <FileTextOutlined />
                </div>
              </div>
              <div class="article-info">
                <h3 class="article-title">{{ article.mainTitle || article.topic }}</h3>
                <div class="article-meta">
                  <span class="article-time">
                    <ClockCircleOutlined />
                    {{ formatTime(article.createTime) }}
                  </span>
                  <span class="article-status" :class="statusClass(article.status)">
                    {{ statusLabel(article.status) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          <a-empty v-else description="暂无创作记录，去写一篇吧" />
        </a-spin>
      </div>
    </section>
  </div>
</template>

<style scoped lang="scss">
.home-page {
  width: 100%;
  margin: 0;
  padding: 0;
  min-height: calc(100vh - 64px);
  background: var(--color-background);
}

.hero-section {
  position: relative;
  padding: 80px 20px 100px;
  text-align: center;
  overflow: hidden;
}

.hero-bg {
  position: absolute;
  inset: 0;
  background: var(--gradient-hero);
  z-index: 0;
}

.container {
  position: relative;
  z-index: 1;
  max-width: 900px;
  margin: 0 auto;
}

.features-section .container,
.articles-section .container {
  max-width: 1100px;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.2);
  border-radius: var(--radius-full);
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 24px;
  color: var(--color-primary-dark);
}

.hero-title {
  font-size: 52px;
  font-weight: 700;
  margin: 0 0 16px;
  letter-spacing: -1.5px;
  line-height: 1.1;
  background: linear-gradient(135deg, var(--color-primary-dark) 0%, var(--color-primary) 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.hero-subtitle {
  font-size: 20px;
  margin: 0 0 40px;
  color: var(--color-text-secondary);
}

.input-wrapper {
  display: flex;
  gap: 12px;
  max-width: 700px;
  margin: 0 auto 20px;
  padding: 8px;
  background: white;
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--color-border);
}

.topic-input {
  flex: 1;
  border: none !important;
  box-shadow: none !important;
  font-size: 16px;
  background: transparent !important;
}

.input-icon {
  color: var(--color-text-muted);
}

.cta-btn {
  height: 52px !important;
  padding: 0 32px !important;
  font-weight: 600 !important;
  border-radius: var(--radius-lg) !important;
  background: var(--gradient-primary) !important;
  border: none !important;
  box-shadow: var(--shadow-green) !important;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}

.hero-tips {
  font-size: 14px;
  color: var(--color-text-muted);
  margin: 0;
}

.features-section {
  padding: 80px 20px;
  background: var(--color-background-secondary);
}

.section-header {
  text-align: center;
  margin-bottom: 48px;
}

.section-badge {
  display: inline-block;
  padding: 6px 14px;
  background: rgba(34, 197, 94, 0.1);
  border-radius: var(--radius-full);
  font-size: 13px;
  font-weight: 600;
  color: var(--color-primary-dark);
  margin-bottom: 16px;
}

.section-title {
  font-size: 32px;
  font-weight: 700;
  margin: 0 0 12px;
  color: var(--color-text);
}

.section-subtitle {
  font-size: 16px;
  color: var(--color-text-secondary);
  margin: 0;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.feature-card {
  background: white;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  padding: 24px;
  display: flex;
  gap: 16px;
  align-items: flex-start;
  transition: all var(--transition-normal);
  cursor: pointer;

  &:hover {
    border-color: var(--color-primary-light);
    box-shadow: var(--shadow-card-hover);
    transform: translateY(-2px);
  }
}

.feature-icon-wrapper {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  flex-shrink: 0;
}

.feature-icon {
  font-size: 22px;
}

.feature-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 6px;
  color: var(--color-text);
}

.feature-description {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 1.5;
}

.articles-section {
  padding: 60px 20px 80px;
}

.section-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.section-title-sm {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 4px;
  color: var(--color-text);
}

.section-subtitle-sm {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
}

.view-all-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--color-primary);
  font-weight: 500;
  padding: 0;
}

.articles-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.article-card {
  background: white;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  overflow: hidden;
  transition: all var(--transition-normal);
  cursor: pointer;

  &:hover {
    border-color: var(--color-primary-light);
    box-shadow: var(--shadow-card-hover);
    transform: translateY(-2px);
  }
}

.article-cover {
  height: 140px;
  background: var(--color-background-tertiary);
  overflow: hidden;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  color: var(--color-text-muted);
}

.article-info {
  padding: 16px;
}

.article-title {
  font-size: 15px;
  font-weight: 600;
  margin: 0 0 12px;
  color: var(--color-text);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.article-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.article-time {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--color-text-muted);
}

.article-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-weight: 500;

  &.status-completed {
    background: rgba(34, 197, 94, 0.1);
    color: var(--color-primary-dark);
  }

  &.status-processing {
    background: rgba(59, 130, 246, 0.1);
    color: #2563eb;
  }

  &.status-failed {
    background: rgba(239, 68, 68, 0.1);
    color: #dc2626;
  }

  &.status-pending {
    background: var(--color-background-tertiary);
    color: var(--color-text-muted);
  }
}

@media (max-width: 992px) {
  .features-grid,
  .articles-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .hero-section {
    padding: 60px 16px 80px;
  }

  .hero-title {
    font-size: 36px;
  }

  .input-wrapper {
    flex-direction: column;
    padding: 12px;
  }

  .cta-btn {
    width: 100%;
    justify-content: center;
  }

  .features-grid,
  .articles-grid {
    grid-template-columns: 1fr;
  }

  .section-header-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>

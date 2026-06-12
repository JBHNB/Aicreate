<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  ArrowLeftOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined,
  DownloadOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  LoadingOutlined,
  OrderedListOutlined,
  PictureOutlined,
  RedoOutlined,
} from '@ant-design/icons-vue'
import dayjs from 'dayjs'

import { getArticle, getExecutionLogs } from '@/api/article'
import { AGENT_DISPLAY_NAME_MAP } from '@/constants/article'
import type { Agent3InputData, AgentExecutionStats, ArticleVO } from '@/types/article'
import {
  exportArticleVo,
  getStatusTagColor,
  getStatusText,
  markdownToHtml,
} from '@/utils/article'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const article = ref<ArticleVO | null>(null)
const executionStats = ref<AgentExecutionStats | null>(null)
const showExecutionLogs = ref(true)

function getAgentDisplayName(agentName: string) {
  return AGENT_DISPLAY_NAME_MAP[agentName] || agentName
}

async function loadArticle() {
  const taskId = route.params.taskId as string
  if (!taskId) {
    message.error('任务 ID 不存在')
    return
  }

  loading.value = true
  try {
    article.value = await getArticle(taskId)
    try {
      executionStats.value = await getExecutionLogs(taskId)
    } catch {
      executionStats.value = null
    }
  } catch (e) {
    message.error((e as Error).message || '加载失败')
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push('/article/list')
}

function exportMarkdown() {
  if (!article.value) return
  exportArticleVo(article.value)
  message.success('导出成功')
}

function handleRetry() {
  if (!article.value) return
  Modal.confirm({
    title: '重新创作',
    content: `将使用选题「${article.value.topic}」进入创作页，是否继续？`,
    onOk: () => {
      router.push({
        path: '/article/create',
        query: { topic: article.value?.topic || '' },
      })
    },
  })
}

function formatDate(date: string) {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

const renderedContent = () => {
  const a = article.value
  if (!a) return ''
  const md = a.fullContent || a.content || ''
  return markdownToHtml(md)
}

const agent3Rag = computed(() => {
  const log = executionStats.value?.logs?.find(
    (item) => item.agentName === 'agent3_generate_content',
  )
  if (!log?.inputData) return null
  try {
    return JSON.parse(log.inputData) as Agent3InputData
  } catch {
    return null
  }
})

onMounted(() => {
  void loadArticle()
})
</script>

<template>
  <div class="article-detail-page">
    <div class="toolbar">
      <a-button @click="goBack">
        <template #icon><ArrowLeftOutlined /></template>
        返回列表
      </a-button>
      <a-space>
        <a-button v-if="article?.status === 'FAILED'" type="primary" danger @click="handleRetry">
          <template #icon><RedoOutlined /></template>
          重新创作
        </a-button>
        <a-button
          v-if="article?.status === 'COMPLETED'"
          type="primary"
          @click="exportMarkdown"
        >
          <template #icon><DownloadOutlined /></template>
          导出 Markdown
        </a-button>
        <a-button
          v-if="article && article.status === 'PROCESSING'"
          type="default"
          @click="router.push('/article/create')"
        >
          打开创作页继续
        </a-button>
      </a-space>
    </div>

    <a-spin :spinning="loading">
      <a-card v-if="article" :bordered="false" class="detail-card">
        <div class="title-block">
          <h1>{{ article.mainTitle || article.topic }}</h1>
          <p v-if="article.subTitle" class="sub">{{ article.subTitle }}</p>
          <a-space>
            <a-tag :color="getStatusTagColor(article.status)">
              {{ getStatusText(article.status) }}
            </a-tag>
            <span class="meta">创建于 {{ formatDate(article.createTime) }}</span>
            <span v-if="article.phase" class="meta">阶段：{{ article.phase }}</span>
          </a-space>
          <a-alert
            v-if="article.errorMessage"
            type="error"
            :message="article.errorMessage"
            show-icon
            style="margin-top: 12px"
          />
        </div>

        <a-divider />

        <div v-if="agent3Rag !== null" class="rag-section">
          <h2><DatabaseOutlined /> 参考资料命中（RAG）</h2>
          <a-alert
            v-if="(agent3Rag.retrievalHitCount ?? 0) === 0"
            type="warning"
            show-icon
            message="未命中系统知识库"
            description="Agent3 生成正文时未检索到相关资料，内容完全由模型根据选题与大纲生成。"
          />
          <template v-else>
            <p class="rag-summary">
              共命中 <strong>{{ agent3Rag.retrievalHitCount }}</strong> 条片段，已注入 Agent3 写作 Prompt
            </p>
            <div
              v-for="(source, index) in agent3Rag.retrievalSources"
              :key="`${source.documentId}-${source.chunkIndex}-${index}`"
              class="rag-item"
            >
              <div class="rag-item-title">{{ source.title }}</div>
              <div class="rag-item-meta">
                分块 #{{ source.chunkIndex + 1 }} · 相似度 {{ source.score.toFixed(2) }}
              </div>
            </div>
          </template>
          <a-divider />
        </div>

        <div
          v-if="executionStats?.logs?.length"
          class="logs-section"
        >
          <div class="section-head" @click="showExecutionLogs = !showExecutionLogs">
            <h2>
              <ClockCircleOutlined />
              智能体执行日志
              <a-tag size="small">{{ executionStats.overallStatus }}</a-tag>
            </h2>
            <span class="toggle">{{ showExecutionLogs ? '收起' : '展开' }}</span>
          </div>
          <div v-show="showExecutionLogs" class="stats-row">
            <span>总耗时 {{ executionStats.totalDurationMs }}ms</span>
            <span>智能体 {{ executionStats.agentCount }} 个</span>
          </div>
          <div v-show="showExecutionLogs" class="timeline">
            <div
              v-for="log in executionStats.logs"
              :key="log.id"
              class="timeline-item"
            >
              <CheckCircleOutlined v-if="log.status === 'SUCCESS'" class="ok" />
              <CloseCircleOutlined v-else-if="log.status === 'FAILED'" class="fail" />
              <LoadingOutlined v-else class="run" />
              <div class="timeline-body">
                <div class="row">
                  <strong>{{ getAgentDisplayName(log.agentName) }}</strong>
                  <span>{{ log.durationMs ?? 0 }}ms</span>
                </div>
                <div class="time">{{ formatDate(log.startTime) }}</div>
                <div v-if="log.errorMessage" class="err">{{ log.errorMessage }}</div>
              </div>
            </div>
          </div>
          <a-divider />
        </div>

        <div v-if="article.outline?.length" class="outline-section">
          <h2><OrderedListOutlined /> 文章大纲</h2>
          <div v-for="item in article.outline" :key="item.section" class="outline-item">
            <div class="outline-title">{{ item.section }}. {{ item.title }}</div>
            <ul>
              <li v-for="(p, i) in item.points" :key="i">{{ p }}</li>
            </ul>
          </div>
          <a-divider />
        </div>

        <div v-if="article.fullContent || article.content" class="content-section">
          <h2><FileTextOutlined /> {{ article.fullContent ? '完整图文' : '文章正文' }}</h2>
          <div class="article-md" v-html="renderedContent()" />
        </div>

        <div
          v-if="!article.fullContent && article.images?.length"
          class="images-section"
        >
          <h2><PictureOutlined /> 配图</h2>
          <div class="images-grid">
            <div v-for="img in article.images" :key="img.position" class="image-card">
              <img :src="img.url" :alt="img.description || ''" loading="lazy" />
              <div class="cap">
                <a-tag>{{ img.method }}</a-tag>
                <span>{{ img.keywords || img.description }}</span>
              </div>
            </div>
          </div>
        </div>
      </a-card>
    </a-spin>
  </div>
</template>

<style scoped>
.article-detail-page {
  max-width: 960px;
  margin: 0 auto;
}
.toolbar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}
.detail-card {
  border-radius: 8px;
}
.title-block h1 {
  margin: 0 0 8px;
  font-size: 26px;
}
.title-block .sub {
  color: rgba(0, 0, 0, 0.55);
  margin: 0 0 12px;
}
.meta {
  color: rgba(0, 0, 0, 0.45);
  font-size: 13px;
}
.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  user-select: none;
}
.section-head h2 {
  margin: 0;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.stats-row {
  display: flex;
  gap: 24px;
  margin: 12px 0;
  font-size: 13px;
  color: rgba(0, 0, 0, 0.55);
}
.timeline-item {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}
.timeline-item .ok {
  color: #52c41a;
}
.timeline-item .fail {
  color: #ff4d4f;
}
.timeline-item .run {
  color: #1677ff;
}
.timeline-body {
  flex: 1;
  background: #fafafa;
  border-radius: 6px;
  padding: 10px 12px;
}
.timeline-body .row {
  display: flex;
  justify-content: space-between;
}
.timeline-body .time {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
}
.timeline-body .err {
  margin-top: 6px;
  font-size: 12px;
  color: #ff4d4f;
}
.outline-item {
  margin-bottom: 12px;
  padding: 12px;
  background: #fafafa;
  border-radius: 6px;
}
.outline-title {
  font-weight: 600;
  margin-bottom: 6px;
}
.content-section h2,
.outline-section h2,
.images-section h2,
.rag-section h2 {
  font-size: 16px;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.rag-summary {
  margin: 0 0 12px;
  color: rgba(0, 0, 0, 0.65);
}
.rag-item {
  padding: 10px 12px;
  margin-bottom: 8px;
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  border-radius: 6px;
}
.rag-item-title {
  font-weight: 500;
  margin-bottom: 4px;
}
.rag-item-meta {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
}
.images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}
.image-card img {
  width: 100%;
  height: 140px;
  object-fit: cover;
  border-radius: 6px;
}
.image-card .cap {
  margin-top: 6px;
  font-size: 12px;
  display: flex;
  gap: 8px;
  align-items: center;
}
.article-md :deep(h2) {
  font-size: 20px;
  margin: 24px 0 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}
.article-md :deep(p) {
  line-height: 1.8;
  margin-bottom: 12px;
}
.article-md :deep(img) {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 16px auto;
  border-radius: 6px;
}
</style>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { PlusOutlined, SearchOutlined } from '@ant-design/icons-vue'
import dayjs, { type Dayjs } from 'dayjs'

import { deleteArticle, getArticle, listArticle } from '@/api/article'
import { exportArticleVo, getStatusText } from '@/utils/article'
import type { ArticleVO } from '@/types/article'

const router = useRouter()

const searchKeyword = ref('')
const dateRange = ref<[Dayjs, Dayjs] | null>(null)
const statusFilter = ref<string>('')

const columns = [
  { title: '选题', dataIndex: 'topic', key: 'topic', width: 140, ellipsis: true },
  { title: '标题', key: 'title', width: 220, ellipsis: true },
  { title: '状态', key: 'status', width: 96, align: 'center' as const },
  { title: '创建时间', key: 'createTime', width: 158 },
  { title: '操作', key: 'action', width: 200, fixed: 'right' as const },
]

const loading = ref(false)
const dataSource = ref<ArticleVO[]>([])
const pagination = ref({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条`,
})

async function loadData() {
  loading.value = true
  try {
    const pageData = await listArticle({
      current: pagination.value.current,
      pageSize: pagination.value.pageSize,
      status: statusFilter.value || undefined,
      topic: searchKeyword.value.trim() || undefined,
    })

    let records = pageData.records || []

    if (searchKeyword.value.trim() && !statusFilter.value) {
      const kw = searchKeyword.value.trim().toLowerCase()
      records = records.filter(
        (item) =>
          item.mainTitle?.toLowerCase().includes(kw) ||
          item.topic?.toLowerCase().includes(kw) ||
          item.subTitle?.toLowerCase().includes(kw),
      )
    }

    if (dateRange.value) {
      const [start, end] = dateRange.value
      records = records.filter((item) => {
        const t = dayjs(item.createTime)
        return t.isAfter(start.startOf('day')) && t.isBefore(end.endOf('day'))
      })
    }

    dataSource.value = records
    pagination.value.total = pageData.total ?? 0
  } catch (e) {
    message.error((e as Error).message || '加载失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.value.current = 1
  void loadData()
}

function handleTableChange(pag: { current?: number; pageSize?: number }) {
  pagination.value.current = pag.current ?? 1
  pagination.value.pageSize = pag.pageSize ?? 10
  void loadData()
}

function viewArticle(record: ArticleVO) {
  if (!record.taskId) return
  router.push(`/article/${record.taskId}`)
}

async function exportArticle(record: ArticleVO) {
  try {
    const article = await getArticle(record.taskId)
    exportArticleVo(article)
    message.success('导出成功')
  } catch (e) {
    message.error((e as Error).message || '导出失败')
  }
}

async function handleDelete(record: ArticleVO) {
  try {
    await deleteArticle(record.id)
    message.success('删除成功')
    void loadData()
  } catch (e) {
    message.error((e as Error).message || '删除失败')
  }
}

function retryArticle(record: ArticleVO) {
  router.push({
    path: '/article/create',
    query: { topic: record.topic || '' },
  })
}

function goToCreate() {
  router.push('/article/create')
}

function formatDate(date: string) {
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

onMounted(() => {
  void loadData()
})
</script>

<template>
  <div class="article-list-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">创作历史</h1>
        <p class="page-subtitle">管理多阶段 AI 创作任务，支持查看、导出与删除</p>
      </div>
      <a-button type="primary" size="large" @click="goToCreate">
        <template #icon><PlusOutlined /></template>
        创作新文章
      </a-button>
    </div>

    <a-card :bordered="false" class="filter-card">
      <a-space wrap>
        <a-input-search
          v-model:value="searchKeyword"
          placeholder="搜索标题或选题"
          style="width: 260px"
          allow-clear
          @search="handleSearch"
        >
          <template #prefix><SearchOutlined /></template>
        </a-input-search>
        <a-range-picker
          v-model:value="dateRange"
          :placeholder="['开始日期', '结束日期']"
          @change="handleSearch"
        />
        <a-select
          v-model:value="statusFilter"
          placeholder="全部状态"
          style="width: 130px"
          allow-clear
          @change="handleSearch"
        >
          <a-select-option value="">全部</a-select-option>
          <a-select-option value="COMPLETED">已完成</a-select-option>
          <a-select-option value="PROCESSING">生成中</a-select-option>
          <a-select-option value="PENDING">等待中</a-select-option>
          <a-select-option value="FAILED">失败</a-select-option>
        </a-select>
        <a-button @click="handleSearch">查询</a-button>
      </a-space>
    </a-card>

    <a-card :bordered="false" class="table-card">
      <a-table
        :columns="columns"
        :data-source="dataSource"
        :loading="loading"
        :pagination="pagination"
        :scroll="{ x: 920 }"
        row-key="id"
        size="middle"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'title'">
            <a class="title-link" @click="viewArticle(record)">
              <div class="main-title">{{ record.mainTitle || record.topic || '-' }}</div>
              <div v-if="record.subTitle" class="sub-title">{{ record.subTitle }}</div>
            </a>
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag
              :color="
                record.status === 'COMPLETED'
                  ? 'success'
                  : record.status === 'FAILED'
                    ? 'error'
                    : record.status === 'PROCESSING'
                      ? 'processing'
                      : 'default'
              "
            >
              {{ getStatusText(record.status) }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'createTime'">
            {{ formatDate(record.createTime) }}
          </template>
          <template v-else-if="column.key === 'action'">
            <div class="action-cell">
              <a-button type="link" size="small" class="action-btn" @click="viewArticle(record)">
                查看
              </a-button>
              <a-button
                v-if="record.status === 'FAILED'"
                type="link"
                size="small"
                class="action-btn"
                @click="retryArticle(record)"
              >
                重试
              </a-button>
              <a-button
                v-else-if="record.status === 'COMPLETED'"
                type="link"
                size="small"
                class="action-btn"
                @click="exportArticle(record)"
              >
                导出
              </a-button>
              <a-popconfirm title="确定删除该文章？" @confirm="handleDelete(record)">
                <a-button type="link" size="small" danger class="action-btn">删除</a-button>
              </a-popconfirm>
            </div>
          </template>
        </template>
        <template #emptyText>
          <a-empty description="暂无文章">
            <a-button type="primary" @click="goToCreate">
              <PlusOutlined /> 开始创作
            </a-button>
          </a-empty>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<style scoped>
.article-list-page {
  width: 100%;
  max-width: 100%;
  margin: 0 auto;
}
.table-card {
  overflow: hidden;
}
.table-card :deep(.ant-card-body) {
  padding: 12px 16px 8px;
  overflow: hidden;
}
.table-card :deep(.ant-table-wrapper) {
  overflow-x: auto;
}
.action-cell {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  justify-content: flex-end;
  gap: 0;
  white-space: nowrap;
}
.action-cell :deep(.action-btn) {
  padding: 0 6px;
  height: 28px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
}
.page-title {
  margin: 0 0 6px;
  font-size: 24px;
  font-weight: 600;
}
.page-subtitle {
  margin: 0;
  color: rgba(0, 0, 0, 0.55);
}
.filter-card {
  margin-bottom: 16px;
}
.title-link {
  display: block;
  max-width: 220px;
  color: inherit;
}
.title-link:hover .main-title {
  color: #1677ff;
}
.main-title,
.sub-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.main-title {
  font-weight: 600;
}
.sub-title {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  margin-top: 2px;
}
</style>

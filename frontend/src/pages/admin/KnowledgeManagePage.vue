<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import type { UploadProps } from 'ant-design-vue'

import {
  deleteKnowledgeDocument,
  getKnowledgeStats,
  listKnowledgeDocumentChunks,
  listKnowledgeDocuments,
  reindexKnowledgeDocument,
  updateKnowledgeDocumentTitle,
  uploadKnowledgeDocument,
  type KnowledgeChunkVO,
  type KnowledgeDocumentVO,
  type KnowledgeStatsVO,
} from '@/api/knowledge'

const loading = ref(false)
const uploading = ref(false)
const renameOpen = ref(false)
const renameSaving = ref(false)
const renameTitle = ref('')
const renamingRecord = ref<KnowledgeDocumentVO | null>(null)
const chunksOpen = ref(false)
const chunksLoading = ref(false)
const chunkList = ref<KnowledgeChunkVO[]>([])
const chunkPreviewTitle = ref('')
const stats = ref<KnowledgeStatsVO | null>(null)
const dataSource = ref<KnowledgeDocumentVO[]>([])
const uploadTitle = ref('')
const selectedFile = ref<File | null>(null)
const statusFilter = ref<string>('')
const titleFilter = ref('')
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
})

const statusMap: Record<string, { text: string; color: string }> = {
  processing: { text: '处理中', color: 'processing' },
  ready: { text: '已就绪', color: 'success' },
  failed: { text: '失败', color: 'error' },
}

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 70 },
  { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
  { title: '文件名', dataIndex: 'fileName', key: 'fileName', ellipsis: true },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '分块数', dataIndex: 'chunkCount', key: 'chunkCount', width: 90 },
  { title: '上传时间', dataIndex: 'createTime', key: 'createTime', width: 180 },
  { title: '操作', key: 'action', width: 280 },
]

async function fetchStats() {
  const { data } = await getKnowledgeStats()
  if (data.code === 0 && data.data) {
    stats.value = data.data
  }
}

function formatSize(size: number) {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

async function fetchData(page = pagination.current, pageSize = pagination.pageSize) {
  loading.value = true
  try {
    const { data } = await listKnowledgeDocuments(page, pageSize, {
      status: statusFilter.value || undefined,
      title: titleFilter.value.trim() || undefined,
    })
    if (data.code === 0 && data.data) {
      dataSource.value = data.data.records ?? []
      pagination.total = data.data.total ?? 0
      pagination.current = data.data.current ?? page
      pagination.pageSize = data.data.size ?? pageSize
    } else {
      message.error(data.message ?? '加载失败')
      dataSource.value = []
    }
  } finally {
    loading.value = false
  }
}

const beforeUpload: UploadProps['beforeUpload'] = (file) => {
  const name = file.name.toLowerCase()
  const allowed = name.endsWith('.txt') || name.endsWith('.md') || name.endsWith('.docx')
  if (!allowed) {
    message.warning('仅支持 .txt / .md / .docx 文件（旧版 .doc 请先另存为 .docx）')
    return false
  }
  selectedFile.value = file as File
  return false
}

async function handleUpload() {
  if (!selectedFile.value) {
    message.warning('请先选择文件')
    return
  }
  uploading.value = true
  try {
    const { data } = await uploadKnowledgeDocument(selectedFile.value, uploadTitle.value)
    if (data.code === 0) {
      message.success(data.message ?? '上传成功')
      uploadTitle.value = ''
      selectedFile.value = null
      await fetchData(1, pagination.pageSize)
      await fetchStats()
    } else {
      message.error(data.message ?? '上传失败')
    }
  } finally {
    uploading.value = false
  }
}

async function handleDelete(record: KnowledgeDocumentVO) {
  const { data } = await deleteKnowledgeDocument(record.id)
  if (data.code === 0) {
    message.success('已删除')
    await fetchData()
    await fetchStats()
  } else {
    message.error(data.message ?? '删除失败')
  }
}

async function handleReindex(record: KnowledgeDocumentVO) {
  const { data } = await reindexKnowledgeDocument(record.id)
  if (data.code === 0) {
    message.success('重建索引成功')
    await fetchData()
  } else {
    message.error(data.message ?? '重建失败')
  }
}

function openRenameModal(record: KnowledgeDocumentVO) {
  renamingRecord.value = record
  renameTitle.value = record.title
  renameOpen.value = true
}

function closeRenameModal() {
  renameOpen.value = false
  renamingRecord.value = null
  renameTitle.value = ''
}

async function handleRenameSubmit() {
  const title = renameTitle.value.trim()
  if (!title) {
    message.warning('请输入标题')
    return
  }
  if (!renamingRecord.value) return

  renameSaving.value = true
  try {
    const { data } = await updateKnowledgeDocumentTitle(renamingRecord.value.id, title)
    if (data.code === 0) {
      message.success('标题已更新')
      closeRenameModal()
      await fetchData()
    } else {
      message.error(data.message ?? '更新失败')
    }
  } finally {
    renameSaving.value = false
  }
}

function handleStatusFilterChange() {
  pagination.current = 1
  void fetchData(1, pagination.pageSize)
}

function handleTitleSearch() {
  pagination.current = 1
  void fetchData(1, pagination.pageSize)
}

async function openChunksModal(record: KnowledgeDocumentVO) {
  chunkPreviewTitle.value = record.title
  chunkList.value = []
  chunksOpen.value = true
  chunksLoading.value = true
  try {
    const { data } = await listKnowledgeDocumentChunks(record.id)
    if (data.code === 0) {
      chunkList.value = data.data ?? []
    } else {
      message.error(data.message ?? '加载分块失败')
    }
  } finally {
    chunksLoading.value = false
  }
}

function closeChunksModal() {
  chunksOpen.value = false
  chunkList.value = []
  chunkPreviewTitle.value = ''
}

function handleTableChange(...args: unknown[]) {
  const pag = args[0] as { current?: number; pageSize?: number }
  void fetchData(pag?.current ?? 1, pag?.pageSize ?? 10)
}

onMounted(() => {
  void fetchStats()
  void fetchData()
})
</script>

<template>
  <div class="knowledge-page">
    <a-typography-title :level="3">系统知识库</a-typography-title>
    <a-typography-paragraph type="secondary">
      管理员上传参考资料后，阶段3生成正文时会自动检索并注入相关内容（RAG）。
    </a-typography-paragraph>

    <a-row v-if="stats" :gutter="16" class="stats-row">
      <a-col :span="6">
        <a-statistic title="文档总数" :value="stats.total" />
      </a-col>
      <a-col :span="6">
        <a-statistic title="已就绪" :value="stats.readyCount" value-style="color: #52c41a" />
      </a-col>
      <a-col :span="6">
        <a-statistic title="处理中" :value="stats.processingCount" value-style="color: #1677ff" />
      </a-col>
      <a-col :span="6">
        <a-statistic title="失败" :value="stats.failedCount" value-style="color: #ff4d4f" />
      </a-col>
    </a-row>

    <a-card title="上传文档" class="upload-card">
      <a-space direction="vertical" style="width: 100%">
        <a-input
          v-model:value="uploadTitle"
          placeholder="文档标题（可选，默认使用文件名）"
          allow-clear
        />
        <a-upload :before-upload="beforeUpload" :max-count="1" :show-upload-list="true">
          <a-button>选择 .txt / .md / .docx 文件</a-button>
        </a-upload>
        <a-button type="primary" :loading="uploading" @click="handleUpload">上传并建立索引</a-button>
      </a-space>
    </a-card>

    <div class="filter-bar">
      <a-space wrap>
        <a-input-search
          v-model:value="titleFilter"
          placeholder="搜索标题"
          style="width: 220px"
          allow-clear
          @search="handleTitleSearch"
        />
        <span class="filter-label">状态筛选</span>
        <a-select
          v-model:value="statusFilter"
          placeholder="全部状态"
          style="width: 130px"
          allow-clear
          @change="handleStatusFilterChange"
        >
          <a-select-option value="">全部</a-select-option>
          <a-select-option value="processing">处理中</a-select-option>
          <a-select-option value="ready">已就绪</a-select-option>
          <a-select-option value="failed">失败</a-select-option>
        </a-select>
        <a-button @click="handleTitleSearch">查询</a-button>
      </a-space>
    </div>

    <a-table
      row-key="id"
      class="doc-table"
      :columns="columns"
      :data-source="dataSource"
      :loading="loading"
      :pagination="{
        current: pagination.current,
        pageSize: pagination.pageSize,
        total: pagination.total,
        showSizeChanger: true,
        showTotal: (t: number) => `共 ${t} 条`,
      }"
      @change="handleTableChange"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'status'">
          <a-tooltip v-if="record.status === 'failed' && record.errorMessage" :title="record.errorMessage">
            <a-tag :color="statusMap[record.status]?.color ?? 'default'">
              {{ statusMap[record.status]?.text ?? record.status }}
            </a-tag>
          </a-tooltip>
          <a-tag v-else :color="statusMap[record.status]?.color ?? 'default'">
            {{ statusMap[record.status]?.text ?? record.status }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'fileName'">
          {{ record.fileName }} ({{ formatSize(record.fileSize) }})
        </template>
        <template v-else-if="column.key === 'action'">
          <a-space>
            <a-button
              v-if="record.status === 'ready' && record.chunkCount > 0"
              type="link"
              size="small"
              @click="openChunksModal(record)"
            >
              查看分块
            </a-button>
            <a-button type="link" size="small" @click="openRenameModal(record)">
              重命名
            </a-button>
            <a-button
              v-if="record.status === 'failed'"
              type="link"
              size="small"
              @click="handleReindex(record)"
            >
              重建索引
            </a-button>
            <a-popconfirm title="确定删除该文档及向量索引？" @confirm="handleDelete(record)">
              <a-button type="link" danger size="small">删除</a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <a-modal
      v-model:open="renameOpen"
      title="重命名文档"
      ok-text="保存"
      cancel-text="取消"
      :confirm-loading="renameSaving"
      @ok="handleRenameSubmit"
      @cancel="closeRenameModal"
    >
      <a-input
        v-model:value="renameTitle"
        placeholder="请输入新标题"
        :maxlength="200"
        show-count
        @press-enter="handleRenameSubmit"
      />
    </a-modal>

    <a-modal
      v-model:open="chunksOpen"
      :title="`分块预览：${chunkPreviewTitle}`"
      width="720px"
      :footer="null"
      @cancel="closeChunksModal"
    >
      <a-spin :spinning="chunksLoading">
        <a-empty v-if="!chunksLoading && chunkList.length === 0" description="暂无分块数据" />
        <a-collapse v-else>
          <a-collapse-panel
            v-for="chunk in chunkList"
            :key="chunk.chunkIndex"
            :header="`分块 #${chunk.chunkIndex + 1}`"
          >
            <pre class="chunk-content">{{ chunk.content }}</pre>
          </a-collapse-panel>
        </a-collapse>
      </a-spin>
    </a-modal>
  </div>
</template>

<style scoped>
.knowledge-page {
  max-width: 1100px;
}

.stats-row {
  margin-bottom: 24px;
}

.upload-card {
  margin-bottom: 24px;
}

.filter-bar {
  margin-bottom: 16px;
}

.filter-label {
  color: rgba(0, 0, 0, 0.65);
}

.doc-table {
  margin-top: 8px;
}

.chunk-content {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  font-size: 13px;
  line-height: 1.6;
}
</style>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import type { UploadProps } from 'ant-design-vue'

import {
  deleteKnowledgeDocument,
  listKnowledgeDocuments,
  reindexKnowledgeDocument,
  uploadKnowledgeDocument,
  type KnowledgeDocumentVO,
} from '@/api/knowledge'

const loading = ref(false)
const uploading = ref(false)
const dataSource = ref<KnowledgeDocumentVO[]>([])
const uploadTitle = ref('')
const selectedFile = ref<File | null>(null)
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
  { title: '操作', key: 'action', width: 160 },
]

function formatSize(size: number) {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

async function fetchData(page = pagination.current, pageSize = pagination.pageSize) {
  loading.value = true
  try {
    const { data } = await listKnowledgeDocuments(page, pageSize)
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

function handleTableChange(...args: unknown[]) {
  const pag = args[0] as { current?: number; pageSize?: number }
  void fetchData(pag?.current ?? 1, pag?.pageSize ?? 10)
}

onMounted(() => {
  void fetchData()
})
</script>

<template>
  <div class="knowledge-page">
    <a-typography-title :level="3">系统知识库</a-typography-title>
    <a-typography-paragraph type="secondary">
      管理员上传参考资料后，阶段3生成正文时会自动检索并注入相关内容（RAG）。
    </a-typography-paragraph>

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
          <a-tag :color="statusMap[record.status]?.color ?? 'default'">
            {{ statusMap[record.status]?.text ?? record.status }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'fileName'">
          {{ record.fileName }} ({{ formatSize(record.fileSize) }})
        </template>
        <template v-else-if="column.key === 'action'">
          <a-space>
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
  </div>
</template>

<style scoped>
.knowledge-page {
  max-width: 1100px;
}

.upload-card {
  margin-bottom: 24px;
}

.doc-table {
  margin-top: 8px;
}
</style>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'

import request from '@/request'

type Row = { id: number; title: string; prompt?: string; createTime: string }

const router = useRouter()
const loading = ref(false)
const dataSource = ref<Row[]>([])
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
})

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 72 },
  { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
  { title: '主题摘要', dataIndex: 'prompt', key: 'prompt', ellipsis: true },
  { title: '创建时间', dataIndex: 'createTime', key: 'createTime', width: 200 },
  { title: '操作', key: 'action', width: 100 },
]

const detailOpen = ref(false)
const detailLoading = ref(false)
const detailTitle = ref('')
const detailContent = ref('')

async function fetchList(page = pagination.current, pageSize = pagination.pageSize) {
  loading.value = true
  try {
    const { data } = await request.get<{
      code: number
      message?: string
      data?: {
        records: Row[]
        total: number
        current: number
        size: number
      }
    }>('/passage/list', {
      params: { current: page, pageSize },
    })
    if (data.code === 0 && data.data) {
      dataSource.value = data.data.records ?? []
      pagination.total = data.data.total ?? 0
      pagination.current = data.data.current ?? page
      pagination.pageSize = data.data.size ?? pageSize
    } else {
      message.error(data.message ?? '加载失败')
    }
  } finally {
    loading.value = false
  }
}

function handleTableChange(...args: unknown[]) {
  const pag = args[0] as { current?: number; pageSize?: number }
  void fetchList(pag?.current ?? 1, pag?.pageSize ?? 10)
}

async function viewDetail(id: number) {
  detailOpen.value = true
  detailLoading.value = true
  detailTitle.value = ''
  detailContent.value = ''
  try {
    const { data } = await request.get<{
      code: number
      data?: { title?: string; content?: string }
    }>('/passage/get', { params: { id } })
    if (data.code === 0 && data.data) {
      detailTitle.value = data.data.title ?? ''
      detailContent.value = data.data.content ?? ''
    } else {
      message.warning(data.message ?? '加载失败')
      detailOpen.value = false
    }
  } finally {
    detailLoading.value = false
  }
}

onMounted(() => {
  void fetchList()
})
</script>

<template>
  <div>
    <a-space style="margin-bottom: 16px">
      <a-typography-title :level="3" style="margin: 0">我的文章</a-typography-title>
      <a-button type="primary" @click="router.push('/passage/create')">去创作</a-button>
    </a-space>

    <a-table
      row-key="id"
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
        <template v-if="column.key === 'action'">
          <a class="link" @click="viewDetail(record.id)">查看</a>
        </template>
      </template>
    </a-table>

    <a-modal
      v-model:open="detailOpen"
      :title="detailTitle || '正文'"
      width="800px"
      :footer="null"
      destroy-on-close
    >
      <a-spin :spinning="detailLoading">
        <pre class="detail-pre">{{ detailContent }}</pre>
      </a-spin>
    </a-modal>
  </div>
</template>

<style scoped>
.detail-pre {
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  max-height: 60vh;
  overflow: auto;
  line-height: 1.6;
}
.link {
  color: #1677ff;
  cursor: pointer;
}
</style>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'

import request from '@/request'
import type { UserVO } from '@/types/user'

const loading = ref(false)
const dataSource = ref<UserVO[]>([])
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
})

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
  { title: '账号', dataIndex: 'userAccount', key: 'userAccount', ellipsis: true },
  { title: '昵称', dataIndex: 'userName', key: 'userName', ellipsis: true },
  { title: '角色', dataIndex: 'userRole', key: 'userRole', width: 100 },
  { title: '创建时间', dataIndex: 'createTime', key: 'createTime', ellipsis: true },
]

async function fetchData(page = pagination.current, pageSize = pagination.pageSize) {
  loading.value = true
  try {
    const { data } = await request.post<{
      code: number
      message?: string
      data?: {
        records: UserVO[]
        total: number
        current: number
        size: number
      }
    }>('/user/list/page', {
      current: page,
      pageSize,
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

function handleTableChange(...args: unknown[]) {
  const pag = args[0] as { current?: number; pageSize?: number }
  void fetchData(pag?.current ?? 1, pag?.pageSize ?? 10)
}

onMounted(() => {
  void fetchData()
})
</script>

<template>
  <div>
    <a-typography-title :level="3">用户管理</a-typography-title>
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
    />
  </div>
</template>

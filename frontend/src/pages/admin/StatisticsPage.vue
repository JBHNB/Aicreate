<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { ReloadOutlined } from '@ant-design/icons-vue'

import { getStatisticsOverview, type StatisticsVO } from '@/api/statistics'

const loading = ref(false)
const stats = ref<StatisticsVO | null>(null)

async function loadData() {
  loading.value = true
  try {
    stats.value = await getStatisticsOverview()
  } catch (e) {
    message.error((e as Error).message || '加载失败')
  } finally {
    loading.value = false
  }
}

function formatDuration(ms: number) {
  if (ms < 1000) return `${ms} ms`
  return `${(ms / 1000).toFixed(1)} s`
}

onMounted(() => {
  void loadData()
})
</script>

<template>
  <div class="statistics-page">
    <div class="head">
      <div>
        <h1>数据分析</h1>
        <p>文章创作与系统运营概览（管理员）</p>
      </div>
      <a-button :loading="loading" @click="loadData">
        <template #icon><ReloadOutlined /></template>
        刷新
      </a-button>
    </div>

    <a-spin :spinning="loading">
      <a-row v-if="stats" :gutter="[16, 16]">
        <a-col :xs="12" :md="6">
          <a-card>
            <a-statistic title="今日创作" :value="stats.todayCount" />
          </a-card>
        </a-col>
        <a-col :xs="12" :md="6">
          <a-card>
            <a-statistic
              title="今日失败"
              :value="stats.todayFailedCount"
              :value-style="{ color: stats.todayFailedCount > 0 ? '#cf1322' : undefined }"
            />
          </a-card>
        </a-col>
        <a-col :xs="12" :md="6">
          <a-card>
            <a-statistic title="本周创作" :value="stats.weekCount" />
          </a-card>
        </a-col>
        <a-col :xs="12" :md="6">
          <a-card>
            <a-statistic title="本月创作" :value="stats.monthCount" />
          </a-card>
        </a-col>
        <a-col :xs="12" :md="6">
          <a-card>
            <a-statistic title="总创作数" :value="stats.totalCount" />
          </a-card>
        </a-col>
        <a-col :xs="12" :md="6">
          <a-card>
            <a-statistic
              title="成功率"
              :value="stats.successRate"
              suffix="%"
              :precision="1"
            />
          </a-card>
        </a-col>
        <a-col :xs="12" :md="6">
          <a-card>
            <a-statistic title="平均耗时" :value="formatDuration(stats.avgDurationMs)" />
          </a-card>
        </a-col>
        <a-col :xs="12" :md="6">
          <a-card>
            <a-statistic title="活跃用户" :value="stats.activeUserCount" />
          </a-card>
        </a-col>
        <a-col :xs="12" :md="6">
          <a-card>
            <a-statistic title="VIP 用户" :value="stats.vipUserCount" />
          </a-card>
        </a-col>
        <a-col :xs="24" :md="12">
          <a-card title="用户">
            <p>总用户：{{ stats.totalUserCount }}</p>
            <p>配额消耗：{{ stats.quotaUsed }}</p>
          </a-card>
        </a-col>
      </a-row>
    </a-spin>
  </div>
</template>

<style scoped>
.statistics-page {
  max-width: 1100px;
  margin: 0 auto;
}
.head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}
.head h1 {
  margin: 0 0 6px;
  font-size: 22px;
}
.head p {
  margin: 0;
  color: rgba(0, 0, 0, 0.55);
}
</style>

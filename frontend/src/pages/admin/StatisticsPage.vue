<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import {
  BarChartOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  FileTextOutlined,
  LineChartOutlined,
  ReloadOutlined,
  RiseOutlined,
  TeamOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons-vue'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'

import { getStatisticsOverview, type StatisticsVO } from '@/api/statistics'

const loading = ref(false)
const stats = ref<StatisticsVO | null>(null)

const trendChartRef = ref<HTMLElement | null>(null)
const userChartRef = ref<HTMLElement | null>(null)
const quotaChartRef = ref<HTMLElement | null>(null)

let trendChart: echarts.ECharts | null = null
let userChart: echarts.ECharts | null = null
let quotaChart: echarts.ECharts | null = null

function formatDuration(ms: number) {
  if (ms < 1000) return `${ms} ms`
  return `${(ms / 1000).toFixed(1)} s`
}

function renderTrendChart() {
  if (!trendChartRef.value || !stats.value) return
  if (!trendChart) trendChart = echarts.init(trendChartRef.value)

  const option: EChartsOption = {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: ['今日', '本周', '本月', '总计'],
      axisLine: { lineStyle: { color: '#E2E8F0' } },
      axisLabel: { color: '#64748B' },
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#F1F5F9' } },
      axisLabel: { color: '#64748B' },
    },
    series: [
      {
        name: '创作数量',
        type: 'bar',
        data: [
          stats.value.todayCount,
          stats.value.weekCount,
          stats.value.monthCount,
          stats.value.totalCount,
        ],
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#4ADE80' },
            { offset: 1, color: '#22C55E' },
          ]),
          borderRadius: [4, 4, 0, 0],
        },
        barWidth: '40%',
      },
    ],
  }
  trendChart.setOption(option)
}

function renderUserChart() {
  if (!userChartRef.value || !stats.value) return
  if (!userChart) userChart = echarts.init(userChartRef.value)

  const otherUsers = Math.max(
    0,
    stats.value.totalUserCount - stats.value.activeUserCount - stats.value.vipUserCount,
  )

  const option: EChartsOption = {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: {
      orient: 'vertical',
      right: '8%',
      top: 'center',
      textStyle: { color: '#64748B' },
    },
    series: [
      {
        name: '用户分布',
        type: 'pie',
        radius: ['40%', '70%'],
        itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 },
        label: { show: false },
        emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
        data: [
          { value: stats.value.vipUserCount, name: 'VIP 会员', itemStyle: { color: '#22C55E' } },
          { value: stats.value.activeUserCount, name: '活跃用户', itemStyle: { color: '#3B82F6' } },
          { value: otherUsers, name: '其他用户', itemStyle: { color: '#94A3B8' } },
        ],
      },
    ],
  }
  userChart.setOption(option)
}

function renderQuotaChart() {
  if (!quotaChartRef.value || !stats.value) return
  if (!quotaChart) quotaChart = echarts.init(quotaChartRef.value)

  const totalQuota = stats.value.totalUserCount * 5
  const usedQuota = stats.value.quotaUsed
  const remainingQuota = Math.max(0, totalQuota - usedQuota)

  const option: EChartsOption = {
    tooltip: { trigger: 'item' },
    series: [
      {
        name: '配额统计',
        type: 'pie',
        radius: '70%',
        center: ['50%', '50%'],
        data: [
          { value: usedQuota, name: '已使用', itemStyle: { color: '#EF4444' } },
          { value: remainingQuota, name: '剩余', itemStyle: { color: '#22C55E' } },
        ],
        label: { formatter: '{b}: {c}' },
      },
    ],
  }
  quotaChart.setOption(option)
}

async function renderCharts() {
  await nextTick()
  renderTrendChart()
  renderUserChart()
  renderQuotaChart()
}

async function loadData() {
  loading.value = true
  try {
    stats.value = await getStatisticsOverview()
    await renderCharts()
  } catch (e) {
    message.error((e as Error).message || '加载数据失败')
  } finally {
    loading.value = false
  }
}

function handleResize() {
  trendChart?.resize()
  userChart?.resize()
  quotaChart?.resize()
}

onMounted(() => {
  void loadData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  userChart?.dispose()
  quotaChart?.dispose()
})
</script>

<template>
  <div class="statistics-page">
    <div class="page-header">
      <div class="header-container">
        <div class="header-content">
          <h1 class="page-title">数据分析</h1>
          <p class="page-subtitle">系统运营数据概览</p>
        </div>
        <a-button class="refresh-btn" :loading="loading" @click="loadData">
          <template #icon><ReloadOutlined /></template>
          刷新数据
        </a-button>
      </div>
    </div>

    <div class="container">
      <a-spin :spinning="loading">
        <template v-if="stats">
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-icon" style="background: rgba(34, 197, 94, 0.1); color: #22c55e">
                <FileTextOutlined />
              </div>
              <div class="stat-content">
                <span class="stat-label">今日创作</span>
                <div class="stat-value">{{ stats.todayCount }}</div>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon" style="background: rgba(239, 68, 68, 0.1); color: #ef4444">
                <CloseCircleOutlined />
              </div>
              <div class="stat-content">
                <span class="stat-label">今日失败</span>
                <div class="stat-value">{{ stats.todayFailedCount }}</div>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon" style="background: rgba(59, 130, 246, 0.1); color: #3b82f6">
                <RiseOutlined />
              </div>
              <div class="stat-content">
                <span class="stat-label">本周创作</span>
                <div class="stat-value">{{ stats.weekCount }}</div>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon" style="background: rgba(139, 92, 246, 0.1); color: #8b5cf6">
                <BarChartOutlined />
              </div>
              <div class="stat-content">
                <span class="stat-label">成功率</span>
                <div class="stat-value">{{ stats.successRate.toFixed(1) }}%</div>
              </div>
            </div>
          </div>

          <div class="charts-grid">
            <a-card class="chart-card" :bordered="false">
              <h3 class="chart-title">
                <LineChartOutlined />
                创作趋势
              </h3>
              <div ref="trendChartRef" class="chart-container" />
            </a-card>

            <a-card class="chart-card" :bordered="false">
              <h3 class="chart-title">
                <ThunderboltOutlined />
                性能统计
              </h3>
              <div class="performance-stats">
                <div class="perf-item">
                  <span class="perf-label">平均耗时</span>
                  <span class="perf-value">{{ formatDuration(stats.avgDurationMs) }}</span>
                </div>
                <div class="perf-item">
                  <span class="perf-label">总创作数</span>
                  <span class="perf-value">{{ stats.totalCount }}</span>
                </div>
                <div class="perf-item">
                  <span class="perf-label">本月创作</span>
                  <span class="perf-value">{{ stats.monthCount }}</span>
                </div>
              </div>
            </a-card>

            <a-card class="chart-card" :bordered="false">
              <h3 class="chart-title">
                <TeamOutlined />
                用户分析
              </h3>
              <div ref="userChartRef" class="chart-container" />
            </a-card>

            <a-card class="chart-card" :bordered="false">
              <h3 class="chart-title">
                <CheckCircleOutlined />
                配额使用情况
              </h3>
              <div ref="quotaChartRef" class="chart-container" />
            </a-card>
          </div>
        </template>
      </a-spin>
    </div>
  </div>
</template>

<style scoped lang="scss">
.statistics-page {
  background: var(--color-background-secondary);
  min-height: calc(100vh - 64px);
  padding-bottom: 48px;
}

.page-header {
  background: var(--gradient-hero);
  padding: 32px 20px;
  margin-bottom: 24px;
}

.header-container {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 6px;
  color: var(--color-text);
}

.page-subtitle {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
}

.refresh-btn {
  height: 38px;
  border-radius: var(--radius-md);
  font-weight: 500;
}

.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  background: white;
  border-radius: var(--radius-lg);
  padding: 24px;
  border: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all var(--transition-normal);

  &:hover {
    box-shadow: var(--shadow-card-hover);
    transform: translateY(-2px);
  }
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 24px;
}

.stat-label {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-bottom: 6px;
  display: block;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text);
  line-height: 1;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.chart-card {
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  overflow: hidden;

  :deep(.ant-card-body) {
    padding: 24px;
  }
}

.chart-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 20px;
  color: var(--color-text);

  .anticon {
    color: var(--color-primary);
    font-size: 18px;
  }
}

.chart-container {
  width: 100%;
  height: 300px;
}

.performance-stats {
  padding: 20px 0;

  .perf-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 0;
    border-bottom: 1px solid var(--color-border-light);

    &:last-child {
      border-bottom: none;
    }
  }

  .perf-label {
    font-size: 14px;
    color: var(--color-text-secondary);
  }

  .perf-value {
    font-size: 24px;
    font-weight: 600;
    color: var(--color-primary);
  }
}

@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .statistics-page {
    padding-bottom: 32px;
  }

  .header-container {
    flex-direction: column;
    align-items: stretch;
  }

  .refresh-btn {
    width: 100%;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .chart-container {
    height: 250px;
  }
}
</style>

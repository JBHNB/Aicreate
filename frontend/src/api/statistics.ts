import request from '@/request'

export interface StatisticsVO {
  todayCount: number
  weekCount: number
  monthCount: number
  totalCount: number
  successRate: number
  avgDurationMs: number
  activeUserCount: number
  totalUserCount: number
  vipUserCount: number
  quotaUsed: number
  /** 今日创作失败数（status=FAILED） */
  todayFailedCount: number
}

interface ApiResp<T> {
  code: number
  data?: T
  message?: string
}

export async function getStatisticsOverview(): Promise<StatisticsVO> {
  const { data } = await request.get<ApiResp<StatisticsVO>>('/statistics/overview')
  if (data.code !== 0) {
    throw new Error(data.message || '加载统计失败')
  }
  return data.data as StatisticsVO
}

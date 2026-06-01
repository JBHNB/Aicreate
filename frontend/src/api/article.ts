import request from '@/request'
import type {
  AgentExecutionStats,
  ArticlePageData,
  ArticleQueryRequest,
  ArticleVO,
} from '@/types/article'

interface ApiResp<T> {
  code: number
  data?: T
  message?: string
}

function assertOk<T>(resp: ApiResp<T>): T {
  if (resp.code !== 0) {
    throw new Error(resp.message || '请求失败')
  }
  return resp.data as T
}

export async function createArticle(body: {
  topic: string
  style?: string
  enabledImageMethods?: string[]
}): Promise<string> {
  const { data } = await request.post<ApiResp<string>>('/article/create', body)
  return assertOk(data)
}

export async function getArticle(taskId: string): Promise<ArticleVO> {
  const { data } = await request.get<ApiResp<ArticleVO>>(`/article/${encodeURIComponent(taskId)}`)
  return assertOk(data)
}

export async function listArticle(query: ArticleQueryRequest): Promise<ArticlePageData> {
  const { data } = await request.post<ApiResp<ArticlePageData>>('/article/list', {
    current: query.current ?? 1,
    pageSize: query.pageSize ?? 10,
    topic: query.topic,
    status: query.status,
    taskId: query.taskId,
  })
  return assertOk(data)
}

export async function deleteArticle(id: number): Promise<boolean> {
  const { data } = await request.post<ApiResp<boolean>>('/article/delete', { id })
  return assertOk(data)
}

export async function getExecutionLogs(taskId: string): Promise<AgentExecutionStats> {
  const { data } = await request.get<ApiResp<AgentExecutionStats>>(
    `/article/execution-logs/${encodeURIComponent(taskId)}`,
  )
  return assertOk(data)
}

export async function confirmTitle(body: {
  taskId: string
  selectedMainTitle: string
  selectedSubTitle: string
  userDescription?: string
}): Promise<void> {
  const { data } = await request.post<ApiResp<null>>('/article/confirm-title', body)
  assertOk(data)
}

export async function confirmOutline(body: {
  taskId: string
  outline: Array<{ section: number; title: string; points: string[] }>
}): Promise<void> {
  const { data } = await request.post<ApiResp<null>>('/article/confirm-outline', body)
  assertOk(data)
}

export async function aiModifyOutline(body: {
  taskId: string
  modifySuggestion: string
}): Promise<Array<{ section: number; title: string; points: string[] }>> {
  const { data } = await request.post<ApiResp<Array<{ section: number; title: string; points: string[] }>>>(
    '/article/ai-modify-outline',
    body,
  )
  return assertOk(data)
}

export async function resumeArticle(taskId: string, force = true): Promise<string> {
  const { data } = await request.post<ApiResp<null>>(
    `/article/${encodeURIComponent(taskId)}/resume?force=${force ? 'true' : 'false'}`,
  )
  if (data.code !== 0) {
    throw new Error(data.message || '恢复失败')
  }
  return data.message || '已恢复任务'
}

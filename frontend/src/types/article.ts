/** 文章模块类型（对齐后端 ArticleVO） */

export interface TitleOption {
  mainTitle: string
  subTitle: string
}

export interface OutlineSection {
  section: number
  title: string
  points: string[]
}

export interface ArticleImage {
  position: number
  url: string
  method: string
  keywords?: string
  description?: string
  sectionTitle?: string
  placeholderId?: string
}

export interface ArticleVO {
  id: number
  taskId: string
  userId: number
  topic: string
  userDescription?: string
  style?: string
  mainTitle?: string
  subTitle?: string
  titleOptions?: TitleOption[]
  outline?: OutlineSection[]
  content?: string
  fullContent?: string
  coverImage?: string
  images?: ArticleImage[]
  status: string
  phase?: string
  errorMessage?: string
  createTime: string
  completedTime?: string
  updateTime: string
}

export interface ArticlePageData {
  records: ArticleVO[]
  total: number
  current: number
  size: number
}

export interface ArticleQueryRequest {
  current?: number
  pageSize?: number
  topic?: string
  status?: string
  taskId?: string
}

export interface RetrievalSource {
  documentId: number
  title: string
  chunkIndex: number
  score: number
}

export interface Agent3InputData {
  retrievalHitCount?: number
  retrievalSources?: RetrievalSource[]
}

export interface AgentLogVO {
  id: number
  taskId: string
  agentName: string
  startTime: string
  endTime?: string
  durationMs?: number
  status: string
  errorMessage?: string
  inputData?: string
  outputData?: string
  createTime: string
}

export interface AgentExecutionStats {
  taskId: string
  totalDurationMs: number
  agentCount: number
  overallStatus: string
  logs: AgentLogVO[]
}

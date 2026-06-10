import request from '@/request'

export interface KnowledgeDocumentVO {
  id: number
  title: string
  fileName: string
  fileType: string
  fileSize: number
  status: string
  chunkCount: number
  errorMessage?: string
  createdBy: number
  createTime: string
  updateTime: string
}

export interface KnowledgeStatsVO {
  total: number
  readyCount: number
  processingCount: number
  failedCount: number
}

export interface KnowledgeChunkVO {
  chunkIndex: number
  content: string
  title: string
}

export async function uploadKnowledgeDocument(file: File, title?: string) {
  const formData = new FormData()
  formData.append('file', file)
  if (title?.trim()) {
    formData.append('title', title.trim())
  }
  return request.post<{ code: number; data?: KnowledgeDocumentVO; message?: string }>(
    '/knowledge/upload',
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120_000,
    },
  )
}

export async function listKnowledgeDocuments(
  current = 1,
  pageSize = 10,
  options?: { status?: string; title?: string },
) {
  return request.post<{
    code: number
    data?: {
      records: KnowledgeDocumentVO[]
      total: number
      current: number
      size: number
    }
    message?: string
  }>('/knowledge/list/page', {
    current,
    pageSize,
    ...(options?.status ? { status: options.status } : {}),
    ...(options?.title ? { title: options.title } : {}),
  })
}

export async function getKnowledgeStats() {
  return request.get<{ code: number; data?: KnowledgeStatsVO; message?: string }>(
    '/knowledge/stats',
  )
}

export async function deleteKnowledgeDocument(id: number) {
  return request.post<{ code: number; data?: boolean; message?: string }>(
    '/knowledge/delete',
    { id },
  )
}

export async function reindexKnowledgeDocument(id: number) {
  return request.post<{ code: number; data?: KnowledgeDocumentVO; message?: string }>(
    `/knowledge/reindex/${id}`,
  )
}

export async function updateKnowledgeDocumentTitle(id: number, title: string) {
  return request.post<{ code: number; data?: KnowledgeDocumentVO; message?: string }>(
    '/knowledge/update/title',
    { id, title },
  )
}

export async function searchKnowledgeDocumentsByStatus(status: string) {
  return request.post<{ code: number; data?: KnowledgeDocumentVO[]; message?: string }>(
    '/knowledge/search/status',
    { status },
  )
}

export async function searchKnowledgeDocumentsByTitle(title: string) {
  return request.post<{ code: number; data?: KnowledgeDocumentVO[]; message?: string }>(
    '/knowledge/search/title',
    { title },
  )
}

export async function listKnowledgeDocumentChunks(documentId: number) {
  return request.get<{ code: number; data?: KnowledgeChunkVO[]; message?: string }>(
    `/knowledge/${documentId}/chunks`,
  )
}

export async function batchDeleteKnowledgeDocuments(ids: number[]) {
  return request.post<{ code: number; data?: boolean; message?: string }>(
    '/knowledge/batch/delete',
    { ids },
  )
}

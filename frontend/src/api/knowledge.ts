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

export async function uploadKnowledgeDocument(file: File, title?: string) {
  const formData = new FormData()
  formData.append('file', file)
  if (title?.trim()) {
    formData.append('title', title.trim())
  }
  return request.post<{ code: number; data?: KnowledgeDocumentVO; message?: string }>(
    '/knowledge/upload',
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  )
}

export async function listKnowledgeDocuments(current = 1, pageSize = 10) {
  return request.post<{
    code: number
    data?: {
      records: KnowledgeDocumentVO[]
      total: number
      current: number
      size: number
    }
    message?: string
  }>('/knowledge/list/page', { current, pageSize })
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

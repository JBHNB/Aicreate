/**
 * SSE（与官方 reference-official/frontend/src/utils/sse.ts 一致）
 * 同源 /api 经 Vite 代理，Cookie 会自动携带。
 */

export interface SSEMessage {
  type: string
  [key: string]: unknown
}

export interface SSEOptions {
  onMessage: (message: SSEMessage) => void
  onError?: (error: Event) => void
  onComplete?: () => void
}

export function connectSSE(taskId: string, options: SSEOptions): EventSource {
  const { onMessage, onError, onComplete } = options
  const url = `/api/article/progress/${encodeURIComponent(taskId)}`
  const eventSource = new EventSource(url)

  eventSource.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data) as SSEMessage
      onMessage(msg)
      if (msg.type === 'ALL_COMPLETE' || msg.type === 'ERROR') {
        eventSource.close()
        onComplete?.()
      }
    } catch (e) {
      console.error('SSE 解析失败', e)
    }
  }

  eventSource.onerror = (err) => {
    onError?.(err)
    if (eventSource.readyState === EventSource.CLOSED) return
    eventSource.close()
  }

  return eventSource
}

export function closeSSE(es: EventSource | null) {
  if (es) es.close()
}

import { marked } from 'marked'

import { STATUS_TAG_COLOR_MAP, STATUS_TEXT_MAP } from '@/constants/article'
import type { ArticleImage, ArticleVO, OutlineSection } from '@/types/article'

marked.setOptions({ gfm: true, breaks: true })

export function getStatusText(status: string): string {
  return STATUS_TEXT_MAP[status] ?? status
}

export function getStatusTagColor(status: string): string {
  return STATUS_TAG_COLOR_MAP[status] ?? 'default'
}

export function markdownToHtml(markdown: string): string {
  if (!markdown?.trim()) return ''
  return marked.parse(markdown) as string
}

export interface ExportArticleOptions {
  title: string
  subTitle?: string
  content?: string
  fullContent?: string
  outline?: OutlineSection[]
  images?: ArticleImage[]
}

/** 导出为 .md 文件 */
export function exportAsMarkdown(options: ExportArticleOptions): void {
  const { title, subTitle, content, fullContent, outline, images } = options

  let markdown = `# ${title}\n\n`
  if (subTitle) {
    markdown += `> ${subTitle}\n\n`
  }

  if (fullContent) {
    markdown += fullContent
  } else {
    if (outline?.length) {
      markdown += `## 目录\n\n`
      outline.forEach((item) => {
        markdown += `${item.section}. ${item.title}\n`
      })
      markdown += `\n---\n\n`
    }
    markdown += content || ''
    if (images?.length) {
      markdown += `\n\n## 配图\n\n`
      images.forEach((image) => {
        markdown += `![${image.description || image.keywords || '配图'}](${image.url})\n\n`
      })
    }
  }

  const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${title || '文章'}.md`
  a.click()
  URL.revokeObjectURL(url)
}

export function exportArticleVo(article: ArticleVO): void {
  exportAsMarkdown({
    title: article.mainTitle || article.topic || '文章',
    subTitle: article.subTitle,
    content: article.content,
    fullContent: article.fullContent,
    outline: article.outline,
    images: article.images,
  })
}

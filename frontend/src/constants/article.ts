/** 文章状态与智能体展示名 */

export const STATUS_TEXT_MAP: Record<string, string> = {
  PENDING: '等待中',
  PROCESSING: '生成中',
  COMPLETED: '已完成',
  FAILED: '失败',
}

export const STATUS_TAG_COLOR_MAP: Record<string, string> = {
  PENDING: 'default',
  PROCESSING: 'processing',
  COMPLETED: 'success',
  FAILED: 'error',
}

export const AGENT_DISPLAY_NAME_MAP: Record<string, string> = {
  agent1_generate_titles: '生成标题',
  agent2_generate_outline: '生成大纲',
  agent3_generate_content: '生成正文',
  agent_reviewer_review_content: '内容审核',
  agent4_analyze_image_requirements: '分析配图',
  agent5_generate_images: '生成配图',
  agent6_merge_content: '图文合成',
  ai_modify_outline: 'AI 修改大纲',
}

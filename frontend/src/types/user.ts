/** 与后端 LoginUserVO（驼峰 alias）一致 */
export interface LoginUserVO {
  id: number
  userAccount: string
  userName?: string | null
  userAvatar?: string | null
  userProfile?: string | null
  userRole: string
  quota?: number | null
  createTime: string
  updateTime: string
}

/** 列表/详情用户 VO（无密码） */
export interface UserVO {
  id: number
  userAccount: string
  userName?: string | null
  userAvatar?: string | null
  userProfile?: string | null
  userRole: string
  createTime: string
}

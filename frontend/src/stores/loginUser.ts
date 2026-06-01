import { defineStore } from 'pinia'
import { ref } from 'vue'

import { DEFAULT_USERNAME } from '@/constants/user'
import request from '@/request'
import type { LoginUserVO } from '@/types/user'

export const useLoginUserStore = defineStore('loginUser', () => {
  const loginUser = ref<LoginUserVO | null>(null)

  function setLoginUser(user: LoginUserVO | null) {
    loginUser.value = user
  }

  function clearLoginUser() {
    loginUser.value = null
  }

  /** 从会话拉取当前登录用户；未登录时置为 null */
  async function fetchLoginUser() {
    try {
      const { data } = await request.get<{ code: number; data?: LoginUserVO }>('/user/get/login')
      if (data.code === 0 && data.data) {
        loginUser.value = data.data
      } else {
        loginUser.value = null
      }
    } catch {
      loginUser.value = null
    }
  }

  /** 展示名：优先昵称，否则账号 */
  function displayName(): string {
    const u = loginUser.value
    if (!u) return DEFAULT_USERNAME
    const name = u.userName?.trim()
    return name || u.userAccount
  }

  return {
    loginUser,
    setLoginUser,
    clearLoginUser,
    fetchLoginUser,
    displayName,
  }
})

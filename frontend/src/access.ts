import { message } from 'ant-design-vue'

import { USER_ROLE_ADMIN } from '@/constants/user'
import router from '@/router'
import { useLoginUserStore } from '@/stores/loginUser'

let firstFetchLoginUser = true

router.beforeEach(async (to, _from, next) => {
  const loginUserStore = useLoginUserStore()
  let loginUser = loginUserStore.loginUser

  if (firstFetchLoginUser) {
    await loginUserStore.fetchLoginUser()
    loginUser = loginUserStore.loginUser
    firstFetchLoginUser = false
  }

  const needsAuth = to.matched.some((r) => r.meta.requiresAuth)
  if (needsAuth && !loginUser) {
    message.warning('请先登录')
    next(`/user/login?redirect=${encodeURIComponent(to.fullPath)}`)
    return
  }

  const toUrl = to.fullPath
  if (toUrl.startsWith('/admin')) {
    if (!loginUser || loginUser.userRole !== USER_ROLE_ADMIN) {
      message.error('没有权限')
      next(`/user/login?redirect=${encodeURIComponent(to.fullPath)}`)
      return
    }
  }

  next()
})

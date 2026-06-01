<script setup lang="ts">
import { RouterLink, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'

import { USER_ROLE_ADMIN } from '@/constants/user'
import request from '@/request'
import { useLoginUserStore } from '@/stores/loginUser'

const router = useRouter()
const loginUserStore = useLoginUserStore()

async function handleLogout() {
  try {
    const { data } = await request.post<{ code: number }>('/user/logout')
    if (data.code === 0) {
      message.success('已退出登录')
    }
  } finally {
    loginUserStore.clearLoginUser()
    if (router.currentRoute.value.path.startsWith('/user')) {
      router.replace('/')
    }
  }
}
</script>

<template>
  <a-layout-header class="header">
    <div class="brand">
      <RouterLink to="/">AI 爆款文章创作器</RouterLink>
    </div>
    <div class="nav">
      <RouterLink to="/">首页</RouterLink>
      <RouterLink to="/about">关于</RouterLink>
      <template v-if="loginUserStore.loginUser">
        <RouterLink to="/article/create">AI 创作</RouterLink>
        <RouterLink to="/article/list">创作历史</RouterLink>
        <RouterLink to="/passage/my">简易文章</RouterLink>
      </template>
      <template v-if="loginUserStore.loginUser?.userRole === USER_ROLE_ADMIN">
        <RouterLink to="/admin/userManage" class="admin-link">用户管理</RouterLink>
        <RouterLink to="/admin/statistics" class="admin-link">数据分析</RouterLink>
      </template>

      <template v-if="loginUserStore.loginUser">
        <span class="user-wrap">
          <span class="user-name" :title="loginUserStore.loginUser.userAccount">
            {{ loginUserStore.displayName() }}
          </span>
          <span class="role-tag">{{ loginUserStore.loginUser.userRole }}</span>
        </span>
        <a class="logout" @click="handleLogout">退出</a>
      </template>
      <template v-else>
        <RouterLink to="/user/login" class="emph">登录</RouterLink>
        <RouterLink to="/user/register" class="emph register">注册账号</RouterLink>
      </template>
    </div>
  </a-layout-header>
</template>

<style scoped>
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
}
.brand a {
  font-weight: 600;
  color: rgba(0, 0, 0, 0.88);
}
.brand a:hover {
  color: #1677ff;
}
.nav {
  display: flex;
  align-items: center;
  gap: 16px;
}
.nav a {
  color: rgba(0, 0, 0, 0.65);
}
.nav a.router-link-active {
  color: #1677ff;
  font-weight: 500;
}
.nav a.emph {
  font-weight: 500;
}
.nav a.register {
  color: #1677ff;
}
.user-wrap {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: rgba(0, 0, 0, 0.85);
  font-size: 14px;
}
.user-name {
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.role-tag {
  font-size: 12px;
  color: #1677ff;
  background: #e6f4ff;
  padding: 0 6px;
  border-radius: 4px;
}
.logout {
  cursor: pointer;
  color: rgba(0, 0, 0, 0.65);
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.logout:hover {
  color: #1677ff;
}
.admin-link {
  color: #722ed1;
  font-weight: 500;
}
</style>

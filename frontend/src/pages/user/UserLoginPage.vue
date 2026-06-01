<script setup lang="ts">
import axios from 'axios'
import { reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'

import request from '@/request'
import { useLoginUserStore } from '@/stores/loginUser'
import type { LoginUserVO } from '@/types/user'

const router = useRouter()
const loginUserStore = useLoginUserStore()
const loading = ref(false)
const form = reactive({
  userAccount: '',
  userPassword: '',
})

async function onSubmit() {
  loading.value = true
  try {
    const { data } = await request.post('/user/login', {
      userAccount: form.userAccount,
      userPassword: form.userPassword,
    })
    if (data.code === 0) {
      const payload = data as { data?: LoginUserVO }
      if (payload.data) {
        loginUserStore.setLoginUser(payload.data)
      } else {
        await loginUserStore.fetchLoginUser()
      }
      message.success(data.message ?? '登录成功')
      const redirect = new URLSearchParams(window.location.search).get('redirect')
      router.replace(redirect || '/')
    } else {
      message.warning(data.message ?? '登录失败')
    }
  } catch (e: unknown) {
    if (axios.isAxiosError(e) && e.response?.status === 422) {
      const detail = e.response.data as { detail?: { msg?: string }[] }
      const msg =
        Array.isArray(detail?.detail) && detail.detail.length
          ? detail.detail.map((d) => d.msg).filter(Boolean).join('；')
          : '账号至少 4 位，密码至少 8 位'
      message.error(msg)
    } else {
      message.error('请求失败，请检查网络或稍后重试')
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="wrap">
    <a-card title="用户登录" class="card">
      <a-form :model="form" layout="vertical" @finish="onSubmit">
        <a-form-item
          label="账号"
          name="userAccount"
          :rules="[
            { required: true, message: '请输入账号' },
            { min: 4, message: '账号至少 4 个字符', trigger: 'blur' },
          ]"
        >
          <a-input v-model:value="form.userAccount" autocomplete="username" />
        </a-form-item>
        <a-form-item
          label="密码"
          name="userPassword"
          :rules="[
            { required: true, message: '请输入密码' },
            { min: 8, message: '密码至少 8 位', trigger: 'blur' },
          ]"
        >
          <a-input-password
            v-model:value="form.userPassword"
            autocomplete="current-password"
          />
        </a-form-item>
        <a-form-item>
          <a-button type="primary" html-type="submit" block :loading="loading">登录</a-button>
        </a-form-item>
      </a-form>
      <RouterLink to="/user/register">还没有账号？去注册</RouterLink>
    </a-card>
  </div>
</template>

<style scoped>
.wrap {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: linear-gradient(160deg, #f0f5ff 0%, #fff 50%);
}
.card {
  width: 100%;
  max-width: 400px;
}
</style>

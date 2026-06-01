<script setup lang="ts">
import axios from 'axios'
import { reactive, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'

import request from '@/request'

const router = useRouter()
const loading = ref(false)
const form = reactive({
  userAccount: '',
  userPassword: '',
  checkPassword: '',
})

function validateSamePassword() {
  return {
    validator(_: unknown, value: string) {
      if (value && value !== form.userPassword) {
        return Promise.reject(new Error('两次输入的密码不一致'))
      }
      return Promise.resolve()
    },
    trigger: 'change',
  }
}

async function onSubmit() {
  if (form.userPassword !== form.checkPassword) {
    message.warning('两次输入的密码不一致')
    return
  }
  loading.value = true
  try {
    const { data } = await request.post('/user/register', {
      userAccount: form.userAccount,
      userPassword: form.userPassword,
      checkPassword: form.checkPassword,
    })
    if (data.code === 0) {
      message.success(data.message ?? '注册成功')
      router.replace('/user/login')
    } else {
      message.warning(data.message ?? '注册失败')
    }
  } catch (e: unknown) {
    if (axios.isAxiosError(e) && e.response?.status === 422) {
      const detail = e.response.data as { detail?: { msg?: string }[] }
      const msg =
        Array.isArray(detail?.detail) && detail.detail.length
          ? detail.detail.map((d) => d.msg).filter(Boolean).join('；')
          : '账号至少 4 位，密码至少 8 位，请按提示修改'
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
    <a-card title="用户注册" class="card">
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
            autocomplete="new-password"
          />
        </a-form-item>
        <a-form-item
          label="确认密码"
          name="checkPassword"
          :rules="[
            { required: true, message: '请再次输入密码' },
            { min: 8, message: '密码至少 8 位', trigger: 'blur' },
            validateSamePassword(),
          ]"
        >
          <a-input-password
            v-model:value="form.checkPassword"
            autocomplete="new-password"
          />
        </a-form-item>
        <a-form-item>
          <a-button type="primary" html-type="submit" block :loading="loading">注册</a-button>
        </a-form-item>
      </a-form>
      <RouterLink to="/user/login">已有账号？去登录</RouterLink>
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
  background: linear-gradient(160deg, #f6ffed 0%, #fff 50%);
}
.card {
  width: 100%;
  max-width: 400px;
}
</style>

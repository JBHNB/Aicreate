<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'

import request from '@/request'

const router = useRouter()
const loading = ref(false)
const form = reactive({
  title: '',
  prompt: '',
})
const resultContent = ref('')

async function onSubmit() {
  loading.value = true
  resultContent.value = ''
  try {
    const { data } = await request.post<{
      code: number
      message?: string
      data?: { content?: string; id?: number }
    }>('/passage/generate', {
      title: form.title,
      prompt: form.prompt,
    })
    if (data.code === 0 && data.data) {
      message.success(data.message ?? '生成成功')
      resultContent.value = data.data.content ?? ''
    } else {
      message.warning(data.message ?? '生成失败')
    }
  } catch {
    message.error('请求失败')
  } finally {
    loading.value = false
  }
}

function goList() {
  router.push('/passage/my')
}
</script>

<template>
  <div>
    <a-typography-title :level="3">AI 创作</a-typography-title>
    <a-typography-paragraph type="secondary">
      须在「用户登录」后使用。后端已对接通义（百炼兼容接口）：在
      <code>python-backend/.env</code>
      中配置 <code>DASHSCOPE_API_KEY</code> 并<strong>重启</strong> FastAPI
      后，此处为真实模型生成；未配置或调用失败时显示占位文案。多阶段创作请用
      <code>/api/article/*</code>（Swagger <code>/docs</code>）。
    </a-typography-paragraph>

    <a-form :model="form" layout="vertical" style="max-width: 640px" @finish="onSubmit">
      <a-form-item
        label="标题"
        name="title"
        :rules="[{ required: true, message: '请输入标题' }]"
      >
        <a-input v-model:value="form.title" placeholder="文章标题" allow-clear />
      </a-form-item>
      <a-form-item
        label="创作主题 / 要求"
        name="prompt"
        :rules="[{ required: true, message: '请输入主题或创作要求' }]"
      >
        <a-textarea
          v-model:value="form.prompt"
          placeholder="描述你想写的主题、风格、受众等"
          :rows="5"
          allow-clear
        />
      </a-form-item>
      <a-form-item>
        <a-space>
          <a-button type="primary" html-type="submit" :loading="loading">生成文章</a-button>
          <a-button @click="goList">我的文章</a-button>
        </a-space>
      </a-form-item>
    </a-form>

    <a-card v-if="resultContent" title="生成结果" style="max-width: 800px; margin-top: 16px">
      <pre class="result-pre">{{ resultContent }}</pre>
    </a-card>
  </div>
</template>

<style scoped>
.result-pre {
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  margin: 0;
  line-height: 1.6;
}
</style>

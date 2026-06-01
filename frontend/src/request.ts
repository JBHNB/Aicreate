import axios from 'axios'
import { message } from 'ant-design-vue'

/** 与 Vite 代理一致：开发环境走 /api → 8567；生产可在 vite 配置或 nginx 再代理 */
const myAxios = axios.create({
  baseURL: '/api',
  timeout: 60_000,
  withCredentials: true,
})

myAxios.interceptors.response.use(
  (response) => {
    const data = response.data as { code?: number }
    if (data?.code === 40100) {
      const url = (response.request?.responseURL as string) ?? ''
      const onAuthPath =
        url.includes('/user/login') ||
        url.includes('/user/register') ||
        url.includes('/user/get/login')
      if (!onAuthPath && !window.location.pathname.includes('/user/login')) {
        message.warning('请先登录')
        window.location.href = `/user/login?redirect=${encodeURIComponent(window.location.href)}`
      }
    }
    return response
  },
  (error) => Promise.reject(error),
)

export default myAxios

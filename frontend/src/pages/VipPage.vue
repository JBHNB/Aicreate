<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  CheckCircleOutlined,
  CrownOutlined,
  SafetyOutlined,
  ThunderboltOutlined,
  RocketOutlined,
  PictureOutlined,
  AppstoreOutlined,
  EditOutlined,
  StarOutlined,
  GiftOutlined,
  QuestionCircleOutlined,
} from '@ant-design/icons-vue'

import { createVipPaymentSession } from '@/api/payment'
import { useLoginUserStore } from '@/stores/loginUser'
import { isVip as checkIsVip } from '@/utils/permission'

const router = useRouter()
const route = useRoute()
const loginUserStore = useLoginUserStore()
const purchasing = ref(false)

const isVip = computed(() => checkIsVip(loginUserStore.loginUser))

const features = [
  { icon: RocketOutlined, title: '无限创作配额', desc: '无限次使用文章创作功能，告别配额限制' },
  { icon: PictureOutlined, title: 'AI 智能生图', desc: '使用 AI 生成独特配图' },
  { icon: AppstoreOutlined, title: 'SVG 图表生成', desc: '自动生成精美的概念示意图和思维导图' },
  { icon: EditOutlined, title: 'AI 大纲编辑', desc: '使用 AI 助手快速优化文章大纲' },
  { icon: StarOutlined, title: '优先队列', desc: '享受更快的生成速度和优先服务' },
  { icon: GiftOutlined, title: '终身有效', desc: '一次购买，永久使用，无需续费' },
]

const pricingFeatures = [
  '无限创作配额',
  '全部高级配图功能',
  'AI 大纲智能编辑',
  '优先生成队列',
  '终身有效',
]

const faqs = [
  {
    question: '支付后多久生效？',
    answer: '支付成功后立即生效，刷新页面即可看到 VIP 权限。',
  },
  {
    question: '如何申请退款？',
    answer: '购买后 7 天内，如不满意可在会员页申请退款，退款后会员权限将被取消。',
  },
  {
    question: '会员是否需要续费？',
    answer: '不需要。永久会员一次购买，终身有效，无需任何续费。',
  },
  {
    question: '支付安全吗？',
    answer: '我们使用 Stripe 国际支付平台，全程加密传输，安全可靠。',
  },
]

onMounted(async () => {
  const success = route.query.success
  const cancelled = route.query.cancelled

  if (success === 'true') {
    await loginUserStore.fetchLoginUser()
    Modal.success({
      title: '支付成功！',
      content: '恭喜您成为永久会员，已解锁全部高级功能！',
      okText: '开始创作',
      onOk: () => {
        router.push('/article/create')
      },
    })
    router.replace('/vip')
  } else if (cancelled === 'true') {
    message.info('支付已取消')
    router.replace('/vip')
  }
})

async function handlePurchase() {
  if (!loginUserStore.loginUser?.id) {
    message.warning('请先登录')
    router.push('/user/login?redirect=/vip')
    return
  }

  if (isVip.value) {
    message.info('您已经是永久会员')
    return
  }

  purchasing.value = true
  try {
    const sessionUrl = await createVipPaymentSession()
    window.location.href = sessionUrl
  } catch (error) {
    console.error('创建支付失败:', error)
    message.error(error instanceof Error ? error.message : '创建支付失败，请稍后重试')
  } finally {
    purchasing.value = false
  }
}
</script>

<template>
  <div class="vip-page">
    <div class="vip-container">
      <div class="page-header">
        <div class="header-badge">
          <CrownOutlined />
          <span>会员专属</span>
        </div>
        <h1 class="page-title">升级永久会员</h1>
        <p class="page-subtitle">解锁全部高级功能，无限创作配额，终身有效</p>
      </div>

      <div class="main-section">
        <div class="pricing-card">
          <div class="pricing-badge">限时优惠</div>
          <div class="pricing-header">
            <div class="plan-icon">
              <CrownOutlined />
            </div>
            <h2 class="plan-name">永久会员</h2>
            <div class="price-display">
              <span class="currency">$</span>
              <span class="price">199</span>
              <span class="period">/永久</span>
            </div>
            <div class="original-price">
              <span class="original-label">原价</span>
              <span class="original-value">$299</span>
            </div>
          </div>

          <div class="pricing-divider" />

          <div class="pricing-features">
            <div v-for="(item, index) in pricingFeatures" :key="index" class="pricing-feature">
              <CheckCircleOutlined class="feature-check" />
              <span>{{ item }}</span>
            </div>
          </div>

          <a-button
            type="primary"
            size="large"
            :loading="purchasing"
            :disabled="isVip"
            class="purchase-btn"
            @click="handlePurchase"
          >
            <template #icon>
              <ThunderboltOutlined />
            </template>
            {{ isVip ? '您已是永久会员' : '立即升级' }}
          </a-button>

          <div class="security-notice">
            <SafetyOutlined />
            <span>安全支付 · 7天无理由退款</span>
          </div>
        </div>

        <div class="features-section">
          <h3 class="features-title">
            <GiftOutlined />
            会员特权
          </h3>
          <div class="features-grid">
            <div v-for="(feature, index) in features" :key="index" class="feature-card">
              <div class="feature-icon-wrapper">
                <component :is="feature.icon" class="feature-icon" />
              </div>
              <div class="feature-content">
                <h4 class="feature-title">{{ feature.title }}</h4>
                <p class="feature-desc">{{ feature.desc }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="faq-section">
        <div class="section-header">
          <QuestionCircleOutlined class="section-icon" />
          <h2 class="section-title">常见问题</h2>
        </div>
        <div class="faq-grid">
          <div v-for="(faq, index) in faqs" :key="index" class="faq-card">
            <h4 class="faq-question">{{ faq.question }}</h4>
            <p class="faq-answer">{{ faq.answer }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.vip-page {
  min-height: calc(100vh - 64px);
  background: linear-gradient(180deg, #f0fdf4 0%, #fafafa 100%);
  padding: 48px 24px 80px;
}

.vip-container {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  text-align: center;
  margin-bottom: 48px;
}

.header-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.2);
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
  color: #15803d;
  margin-bottom: 20px;
}

.page-title {
  font-size: 36px;
  font-weight: 700;
  margin: 0 0 12px;
  color: #1a1a1a;
}

.page-subtitle {
  font-size: 16px;
  color: #666;
  margin: 0;
}

.main-section {
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: 32px;
  margin-bottom: 56px;
}

.pricing-card {
  background: white;
  border-radius: 16px;
  padding: 36px 32px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
  border: 2px solid #22c55e;
  position: sticky;
  top: 88px;
  height: fit-content;
}

.pricing-badge {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  background: linear-gradient(135deg, #22c55e, #16a34a);
  color: white;
  padding: 6px 20px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.pricing-header {
  text-align: center;
  padding-bottom: 20px;
}

.plan-icon {
  width: 52px;
  height: 52px;
  margin: 0 auto 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(34, 197, 94, 0.1);
  border-radius: 12px;
  font-size: 26px;
  color: #22c55e;
}

.plan-name {
  font-size: 20px;
  font-weight: 700;
  margin: 0 0 14px;
}

.price-display {
  display: flex;
  align-items: baseline;
  justify-content: center;
  margin-bottom: 6px;
}

.currency {
  font-size: 18px;
  color: #666;
  margin-right: 2px;
}

.price {
  font-size: 52px;
  font-weight: 700;
  color: #22c55e;
  line-height: 1;
}

.period {
  font-size: 14px;
  color: #999;
  margin-left: 4px;
}

.original-price {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 13px;
  color: #999;
}

.original-value {
  text-decoration: line-through;
}

.pricing-divider {
  height: 1px;
  background: #eee;
  margin: 20px 0;
}

.pricing-feature {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  font-size: 14px;
}

.feature-check {
  color: #22c55e;
  flex-shrink: 0;
}

.purchase-btn {
  width: 100%;
  height: 48px;
  font-size: 15px;
  font-weight: 600;
  margin-top: 8px;
}

.security-notice {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 14px;
  font-size: 12px;
  color: #666;
}

.features-section,
.faq-section {
  background: white;
  border-radius: 16px;
  padding: 32px;
  border: 1px solid #eee;
}

.features-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 700;
  margin: 0 0 24px;
  color: #22c55e;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.feature-card {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 20px;
  background: #f9fafb;
  border-radius: 12px;
}

.feature-icon-wrapper {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(34, 197, 94, 0.1);
  border-radius: 8px;
}

.feature-icon {
  font-size: 18px;
  color: #22c55e;
}

.feature-title {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 4px;
}

.feature-desc {
  font-size: 13px;
  color: #666;
  margin: 0;
  line-height: 1.5;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 24px;
}

.section-icon {
  font-size: 20px;
  color: #22c55e;
}

.section-title {
  font-size: 18px;
  font-weight: 700;
  margin: 0;
}

.faq-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.faq-card {
  padding: 20px;
  background: #f9fafb;
  border-radius: 12px;
}

.faq-question {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 8px;
}

.faq-answer {
  font-size: 13px;
  color: #666;
  margin: 0;
  line-height: 1.6;
}

@media (max-width: 992px) {
  .main-section {
    grid-template-columns: 1fr;
  }

  .pricing-card {
    position: static;
    max-width: 400px;
    margin: 0 auto;
  }

  .features-grid,
  .faq-grid {
    grid-template-columns: 1fr;
  }
}
</style>

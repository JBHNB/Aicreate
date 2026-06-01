import request from '@/request'

interface ApiResp<T> {
  code: number
  data?: T
  message?: string
}

export interface PaymentRecordVO {
  id: number
  userId: number
  stripeSessionId?: string | null
  stripePaymentIntentId?: string | null
  amount: number
  currency: string
  status: string
  productType: string
  description?: string | null
  refundTime?: string | null
  refundReason?: string | null
  createTime: string
  updateTime: string
}

function assertOk<T>(resp: ApiResp<T>): T {
  if (resp.code !== 0) {
    throw new Error(resp.message || '请求失败')
  }
  return resp.data as T
}

/** 创建 VIP 支付会话，返回 Stripe Checkout URL */
export async function createVipPaymentSession(): Promise<string> {
  const { data } = await request.post<ApiResp<string>>('/payment/create-vip-session')
  return assertOk(data)
}

/** 获取当前用户支付记录 */
export async function getPaymentRecords(): Promise<PaymentRecordVO[]> {
  const { data } = await request.get<ApiResp<PaymentRecordVO[]>>('/payment/records')
  return assertOk(data)
}

/** 申请退款 */
export async function refundPayment(reason?: string): Promise<boolean> {
  const { data } = await request.post<ApiResp<boolean>>('/payment/refund', null, {
    params: reason ? { reason } : undefined,
  })
  return assertOk(data)
}

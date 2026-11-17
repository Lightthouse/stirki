import { api, setToken, savePhone } from './client'
import type {
  AddressesResponse,
  ServiceItem,
  AuthTokenResponse,
  ClientInfo,
  CreateOrderRequest,
  PaymentResponse,
  OrderDetail,
  OrderListItem,
  SystemSettings,
} from '../types'

export { setToken, clearToken, isAuthenticated, savePhone, clearPhone, getPhone } from './client'

export async function getMe() {
  return api.get<ClientInfo>('/auth/me')
}

export async function requestCode(phone: string, offerAccepted: boolean) {
  return api.post<{ message: string; code?: string }>('/auth/request-code', { phone, offer_accepted: offerAccepted })
}

export async function verifyCode(
  phone: string,
  code: string,
  email: string,
  consents: { offerAccepted: boolean; smsMarketingConsent: boolean },
) {
  const result = await api.post<AuthTokenResponse>('/auth/verify', {
    phone,
    code,
    email,
    offer_accepted: consents.offerAccepted,
    sms_marketing_consent: consents.smsMarketingConsent,
  })
  setToken(result.token)
  savePhone(phone)
  return result
}

export async function getAddresses() {
  return api.get<AddressesResponse>('/addresses')
}

export async function getServices() {
  return api.get<ServiceItem[]>('/services')
}

export async function createOrder(data: CreateOrderRequest) {
  return api.post<PaymentResponse>('/orders', data)
}

export async function getOrder(orderId: number) {
  return api.get<OrderDetail>(`/orders/${orderId}`)
}

export async function getOrders() {
  return api.get<OrderListItem[]>('/orders')
}

export async function verifyPayment(orderId: number) {
  return api.post<{ status: string }>(`/payments/verify/${orderId}`)
}

export async function getOrderByPaymentToken(token: string) {
  return api.get<PaymentResponse>(`/payments/by-token/${token}`)
}

/** Заход на главную: не чаще раза за сессию вкладки (обновления и переходы по сайту не считаются).
 *  visitor_id живёт в localStorage и нужен для подсчёта уникальных посетителей. */
export function trackVisit(): void {
  try {
    if (sessionStorage.getItem('visit_tracked')) return
    let visitorId = localStorage.getItem('visitor_id')
    if (!visitorId) {
      visitorId = crypto.randomUUID()
      localStorage.setItem('visitor_id', visitorId)
    }
    sessionStorage.setItem('visit_tracked', '1')
    api.post('/analytics/track-visit', { visitor_id: visitorId }).catch(() => {})
  } catch {
    // хранилище недоступно (приватный режим и т. п.) — визит не считаем
  }
}

export async function trackAdView(image_path: string): Promise<void> {
  await api.post('/analytics/track-ad-view', { image_path })
}

export async function updateMe(data: { name?: string }) {
  return api.patch<ClientInfo>('/auth/me', data)
}

export async function getAdImages(): Promise<string[]> {
  const result = await api.get<{ images: string[] }>('/advertising')
  return result.images
}

export async function getSystemSettings(): Promise<SystemSettings> {
  return api.get<SystemSettings>('/system-settings')
}

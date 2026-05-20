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

export async function requestCode(phone: string) {
  return api.post<{ message: string; code: string }>('/auth/request-code', { phone })
}

export async function verifyCode(phone: string, code: string) {
  const result = await api.post<AuthTokenResponse>('/auth/verify', { phone, code })
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

export async function trackVisit(ref: string): Promise<void> {
  await api.post('/analytics/track-visit', { ref })
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

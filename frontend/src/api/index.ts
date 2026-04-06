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

export async function simulatePayment(orderId: number) {
  return api.post<{ status: string; order_id: number }>(`/payments/test/simulate/${orderId}`)
}

export async function trackVisit(ref: string): Promise<void> {
  await api.post('/analytics/track-visit', { ref })
}

export async function updateMe(data: { name?: string; email?: string }) {
  return api.patch<ClientInfo>('/auth/me', data)
}

export async function getAdImages(): Promise<string[]> {
  const result = await api.get<{ images: string[] }>('/advertising')
  return result.images
}

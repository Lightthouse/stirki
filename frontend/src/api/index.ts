import { api, setToken } from './client'
import type {
  AddressesResponse,
  ServiceItem,
  AuthTokenResponse,
  CreateOrderRequest,
  PaymentResponse,
  OrderDetail,
  OrderListItem,
} from '../types'

export { setToken, clearToken, isAuthenticated } from './client'

export async function requestCode(phone: string) {
  return api.post<{ message: string; code: string }>('/auth/request-code', { phone })
}

export async function verifyCode(phone: string, code: string) {
  const result = await api.post<AuthTokenResponse>('/auth/verify', { phone, code })
  setToken(result.token)
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

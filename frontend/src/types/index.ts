export interface Street {
  name: string
  slug: string
  houses: string[]
}

export interface AddressesResponse {
  streets: Street[]
}

export interface ServiceItem {
  slug: string
  name: string
  price_rub: number
  is_active: boolean
}

export interface ClientInfo {
  id: number
  phone: string
  name: string | null
  street: string
  house: string
  apartment: number
  entrance: number
  floor: number
}

export interface AuthTokenResponse {
  token: string
  is_new_client: boolean
  client: ClientInfo | null
}

export interface CreateOrderRequest {
  street: string
  house: string
  apartment: number
  entrance: number
  floor: number
  washing_type: 'bag' | 'piece'
  bags_number: number
  services: string[]
  comment?: string
  is_free: boolean
}

export interface PaymentResponse {
  order_id: number
  total_price_rub: number
  confirmation_url: string | null
}

export interface OrderDetail {
  id: number
  status: string
  street: string
  house: string
  apartment: number
  entrance: number
  floor: number
  washing_type: 'bag' | 'piece'
  bags_number: number
  services: string[]
  total_price_rub: number
  payment_status: string
  is_free: boolean
  comment: string | null
  created_at: string
  updated_at: string
}

export interface OrderListItem {
  id: number
  status: string
  total_price_rub: number
  payment_status: string
  washing_type: 'bag' | 'piece'
  bags_number: number
  created_at: string
}

export interface SystemSettings {
  free_tariff_is_available: boolean
}

export type Step =
  | 'phone'
  | 'code'
  | 'name'
  | 'street'
  | 'house'
  | 'apartment'
  | 'bags'
  | 'services'
  | 'confirm'
  | 'payment'
  | 'status'

export interface OrderFormData {
  phone: string
  code: string
  name: string
  street: string
  house: string
  apartment: number
  entrance: number
  floor: number
  bags_number: number
  services: string[]
  comment: string
}

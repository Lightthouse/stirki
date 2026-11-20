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
  // действующая цена (по акции, если она идёт)
  price_rub: number
  // обычная цена, если сейчас акция: сайт её зачёркивает; иначе null
  regular_price_rub?: number | null
  is_active: boolean
}

export interface ClientInfo {
  id: number
  phone: string
  name: string | null
  email: string | null
  street: string
  house: string
  apartment: number
  entrance: number
  floor: number
}

// Ответ /auth/request-code (src/schemas/auth.py, RequestCodeOut)
export interface RequestCodeResponse {
  message: string
  // номер не зарегистрирован, код не отправлен — показать шаг регистрации
  registration_required: boolean
  // код на странице: вход по SMS выключен или номер отладочный
  code: string | null
}

export interface AuthTokenResponse {
  token: string
  is_new_client: boolean
  client: ClientInfo | null
}

// Как курьер передаёт вещи — обязательный выбор в корзине (src/enums.py, Handover).
export type Handover = 'door' | 'hand'

export const HANDOVER_LABELS: Record<Handover, string> = {
  door: 'Забрать и оставить у двери',
  hand: 'Лично в руки',
}

export interface CreateOrderRequest {
  street: string
  house: string
  apartment: number
  entrance: number
  floor: number
  bags_number: number
  pieces_number: number
  services: string[]
  comment?: string
  is_free: boolean
  handover: Handover
  // email для кассового чека — только у платного заказа
  email?: string
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
  washing_type: 'bag' | 'piece' | 'mixed'
  bags_number: number
  pieces_number: number
  services: string[]
  total_price_rub: number
  // цена пакета и вещи без допов на момент оформления (с учётом акции); null — старый или бесплатный заказ
  bag_price_rub?: number | null
  piece_price_rub?: number | null
  payment_status: string
  is_free: boolean
  // вещи вернут на следующий день: заказ оформлен вечером
  next_day_delivery: boolean
  handover: Handover
  comment: string | null
  payment_link: string | null
  created_at: string
  updated_at: string
}

export interface OrderListItem {
  id: number
  status: string
  total_price_rub: number
  payment_status: string
  washing_type: 'bag' | 'piece' | 'mixed'
  bags_number: number
  pieces_number: number
  created_at: string
}

export interface SystemSettings {
  free_tariff_is_available: boolean
  free_bag_slots: number
  free_piece_slots: number
  paid_bag_slots: number
  paid_piece_slots: number
  // «ЧЧ:ММ» по МСК
  order_accept_from: string
  order_accept_to: string
  // заказы с этого часа (МСК) забирают сразу, а возвращают на следующий день
  next_day_delivery_from_hour: number
  free_orders_per_address_per_day: number
  ad_count: number
  ad_duration_sec: number
  // контакты поддержки из админки; пустая строка — не показывать
  support_phone: string
  support_telegram: string
  support_email: string
  promo_enabled: boolean
  // надпись акции рядом с зачёркнутой ценой, например «акция 7 дней»
  promo_label: string
  is_accepting_orders: boolean
}

/** Текущий час по Москве (UTC+3 без перехода на летнее время), независимо от пояса устройства. */
// Простая проверка формата email; совпадает с проверкой на бэкенде (src/schemas/auth.py)
export const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/

export function mskHour(): number {
  return new Date(Date.now() + 3 * 3600_000).getUTCHours()
}

// «07:30» → «7:30» (как accept_hours_text на бэкенде)
const formatTime = (t: string) => t.replace(/^0(\d)/, '$1')

export function acceptHoursText(s: Pick<SystemSettings, 'order_accept_from' | 'order_accept_to'>): string {
  return `с ${formatTime(s.order_accept_from)} до ${formatTime(s.order_accept_to)}`
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

export const STATUS_NAMES: Record<string, string> = {
  courier_pickup: 'В пути',
  picked_up: 'Забрали',
  washing: 'Чистим',
  courier_delivery: 'Идём отдавать',
  delivered: 'Доставлено',
  canceled: 'Отменён',
  waiting_for_capture: 'Ожидание оплаты',
}

export function getStatusName(status: string): string {
  return STATUS_NAMES[status] ?? status
}

// Заказы, которые считаются активными (не завершены и не отменены)
export const ACTIVE_STATUSES = new Set([
  'courier_pickup',
  'picked_up',
  'washing',
  'courier_delivery',
])

export const TERMINAL_STATUSES = new Set(['delivered', 'canceled'])

// Номер шага таймлайна для каждого статуса (1–5)
export const STATUS_STEP_MAP: Record<string, number> = {
  courier_pickup: 1,
  picked_up: 2,
  washing: 3,
  courier_delivery: 4,
  delivered: 5,
}

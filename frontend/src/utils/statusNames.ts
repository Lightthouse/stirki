export function getStatusName(status: string): string {
  return STATUS_NAMES[status] || status
}

export const STATUS_NAMES: Record<string, string> = {
  new: 'Новый',
  courier_pickup: 'В пути',
  picked_up: 'Забрали',
  washing: 'Чистим',
  courier_delivery: 'Идём отдавать',
  delivered: 'Доставлено',
  canceled: 'Отменён',
}

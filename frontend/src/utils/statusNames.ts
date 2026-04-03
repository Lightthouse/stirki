export function getStatusName(status: string): string {
  return STATUS_NAMES[status] || status
}

export const STATUS_NAMES: Record<string, string> = {
  waiting_for_capture: 'Ожидает оплаты',
  new: 'Новый',
  courier_pickup: 'Курьер забирает',
  picked_up: 'Забран',
  washing: 'Стирка',
  drying: 'Сушка',
  ironing: 'Глажка',
  packing: 'Упаковка',
  courier_delivery: 'Доставка',
  delivered: 'Доставлен',
  canceled: 'Отменён',
}

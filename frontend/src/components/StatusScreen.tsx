import { useState } from 'react'
import { getStatusName, STATUS_STEP_MAP, ACTIVE_STATUSES } from '../utils/orderStatuses'
import type { OrderDetail } from '../types'
import { HANDOVER_LABELS } from '../types'
import { addonBagPrice } from './swipe/ServicesCard'
import { SupportContacts } from './ui/SupportContacts'

interface Props {
  order: OrderDetail
  serviceNames: Record<string, string>
  servicePrices: Record<string, number>
  streetName: string
  onClose: () => void
  onCancel: () => Promise<void>
}

const timelineSteps = [
  { icon: 'fa-person-walking', label: 'В пути' },
  { icon: 'fa-box', label: 'Забрали' },
  { icon: 'fa-soap', label: 'Чистим' },
  { icon: 'fa-truck', label: 'Идём отдавать' },
  { icon: 'fa-box-open', label: 'Доставлено' },
]

export function StatusScreen({ order, serviceNames, servicePrices, streetName, onClose, onCancel }: Props) {
  const [showSupport, setShowSupport] = useState(false)
  const [showCancel, setShowCancel] = useState(false)
  const [canceling, setCanceling] = useState(false)
  const [cancelError, setCancelError] = useState<string | null>(null)

  const confirmCancel = async () => {
    setCanceling(true)
    setCancelError(null)
    try {
      await onCancel()
      setShowCancel(false)
    } catch (e) {
      setCancelError(e instanceof Error ? e.message : 'Не удалось отменить заказ. Попробуйте ещё раз.')
    } finally {
      setCanceling(false)
    }
  }

  const isCanceled = order.status === 'canceled'
  const pickupPlace = order.handover === 'hand' ? 'из рук' : 'у двери'
  const isWaitingPayment = order.status === 'waiting_payment'
  const isActive = ACTIVE_STATUSES.has(order.status)
  const statusStep = STATUS_STEP_MAP[order.status] || 1
  const isFree = order.is_free

  // Цены на момент оформления (с учётом акции); у бесплатных и старых заказов их нет — берём текущий прайс.
  const basePrice = order.bag_price_rub ?? servicePrices['base'] ?? 990
  const piecePrice = order.piece_price_rub ?? servicePrices['piece'] ?? 190
  const itemsCount = order.bags_number + order.pieces_number
  // Допуслуга применяется к каждой позиции, за пакет — по цене `<slug>_bag` (как src/services/pricing.py),
  // поэтому строка допуслуги показывает число всех позиций и их общую стоимость
  const lines = [
    { key: 'bag', icon: 'fa-box-open', name: 'Пакет', count: order.bags_number, price: basePrice * order.bags_number },
    { key: 'piece', icon: 'fa-tshirt', name: 'Вещь', count: order.pieces_number, price: piecePrice * order.pieces_number },
    ...order.services
      .filter((s) => s !== 'base' && s !== 'piece')
      .map((slug) => ({
        key: slug,
        icon: 'fa-plus-circle',
        name: serviceNames[slug] || slug,
        count: itemsCount,
        price: (servicePrices[slug] ?? 0) * order.pieces_number
          + addonBagPrice(servicePrices, slug) * order.bags_number,
      })),
  ].filter((line) => line.count > 0)

  const addressDisplay = `${streetName}, д. ${order.house}, кв. ${order.apartment}`

  return (
    <div className="status-screen">
      {isWaitingPayment ? (
        <>
          <div className="check-circle" style={{ background: 'linear-gradient(135deg, #F2B84B, #d99a2b)' }}>
            <i className="fas fa-credit-card" />
          </div>
          <div className="status-title">Ожидает оплаты</div>
        </>
      ) : isCanceled ? (
        <>
          <div className="check-circle" style={{ background: 'linear-gradient(135deg, #E26D7B, #c9505f)' }}>
            <i className="fas fa-times" />
          </div>
          <div className="status-title">Заказ отменён</div>
        </>
      ) : isActive ? (
        <>
          <div className="check-circle">
            <i className="fas fa-check" />
          </div>
          <div className="status-title">Заказ оформлен</div>
        </>
      ) : (
        <div className="status-title">{getStatusName(order.status)}</div>
      )}

      <div style={{ marginBottom: 4 }}>
        <span className="order-number">
          <i className="fas fa-receipt" /> № ST-{order.id}
        </span>
      </div>
      {isActive && (
        <div className="status-current-label">{getStatusName(order.status)}</div>
      )}
      {!isFree && <div className="order-total"><i className="fas fa-ruble-sign" /> {order.total_price_rub} ₽</div>}

      <div className="details-card">
        <div className="card-content">
          {lines.map((line) => (
            <div key={line.key} className="detail-row">
              <div className="detail-label">
                <i className={`fas ${line.icon}`} /> {line.name}{line.count > 1 && ` ×${line.count}`}
              </div>
              <div className="detail-value">{isFree ? <><s>{line.price} ₽</s> 0 ₽</> : `${line.price} ₽`}</div>
            </div>
          ))}
          <div className="detail-row">
            <div className="detail-label"><i className="fas fa-map-pin" /> Адрес</div>
            <div className="detail-value">{addressDisplay}</div>
          </div>
          <div className="detail-row">
            <div className="detail-label"><i className={`fas ${order.handover === 'hand' ? 'fa-hand-holding' : 'fa-door-closed'}`} /> Передача</div>
            <div className="detail-value">{HANDOVER_LABELS[order.handover]}</div>
          </div>
          {order.comment && (
            <div className="detail-row">
              <div className="detail-label"><i className="fas fa-comment" /> Комментарий</div>
              <div className="detail-value">{order.comment}</div>
            </div>
          )}
        </div>
      </div>

      {isActive && (
        <div className="small-card">
          <p><i className="fas fa-truck-fast" /> Курьер спешит забрать ваш заказ {pickupPlace} за 15 минут</p>
          {order.next_day_delivery ? (
            <p><i className="fas fa-moon" /> Чистые вещи вернём завтра ко времени из комментария, если вы его указали</p>
          ) : (
            <p><i className="fas fa-soap" /> Постираем за 4 часа</p>
          )}
        </div>
      )}

      {!isCanceled && !isWaitingPayment && (
        <div className="status-timeline">
          {timelineSteps.map((s, i) => (
            <div key={i} className={`timeline-step${statusStep === i + 1 ? ' active' : ''}`}>
              <div className="step-icon"><i className={`fas ${s.icon}`} /></div>
              <div className="step-label">{s.label}</div>
            </div>
          ))}
        </div>
      )}

      {isWaitingPayment && (
        <div className="small-card">
          <p><i className="fas fa-info-circle" /> Курьер выедет сразу после оплаты. Если вы уже оплатили — статус обновится в течение минуты.</p>
          {order.payment_link && (
            <a className="btn-pill btn-pill-accent" href={order.payment_link} style={{ display: 'block', textAlign: 'center', marginTop: 12 }}>
              <i className="fas fa-credit-card" /> Перейти к оплате
            </a>
          )}
        </div>
      )}

      {cancelError && <div className="small-card"><p><i className="fas fa-exclamation-circle" /> {cancelError}</p></div>}

      <div className="status-actions">
        {isWaitingPayment && (
          <button className="status-btn" onClick={() => { setCancelError(null); setShowCancel(true) }}>
            <i className="fas fa-times" /> Отменить заказ
          </button>
        )}
        <button className="status-btn" onClick={() => setShowSupport(true)}>
          <i className="fas fa-headset" /> Связаться с поддержкой
        </button>
        <button className="status-btn" onClick={onClose}>
          <i className="fas fa-arrow-left" /> На главную
        </button>
      </div>

      {showCancel && (
        <div className="modal-overlay" onClick={() => !canceling && setShowCancel(false)}>
          <div className="modal-box" role="alertdialog" aria-labelledby="cancel-title" onClick={(e) => e.stopPropagation()}>
            <h3 id="cancel-title"><i className="fas fa-times-circle" /> Отменить заказ?</h3>
            <p>Заказ № ST-{order.id} ещё не оплачен. После отмены оплатить его будет нельзя — при необходимости оформите новый.</p>
            <button className="btn-pill btn-pill-accent" onClick={confirmCancel} disabled={canceling} style={{ marginBottom: 8 }}>
              {canceling ? 'Отменяем…' : 'Да, отменить'}
            </button>
            <button className="status-btn" onClick={() => setShowCancel(false)} disabled={canceling}>Не отменять</button>
          </div>
        </div>
      )}

      {showSupport && (
        <div className="modal-overlay" onClick={() => setShowSupport(false)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()}>
            <h3><i className="fas fa-headset" /> Поддержка</h3>
            <SupportContacts />
            <button className="status-btn" onClick={() => setShowSupport(false)}>Закрыть</button>
          </div>
        </div>
      )}
    </div>
  )
}

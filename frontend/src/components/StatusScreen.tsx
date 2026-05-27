import { useState } from 'react'
import { getStatusName, STATUS_STEP_MAP, ACTIVE_STATUSES } from '../utils/orderStatuses'
import type { OrderDetail } from '../types'

interface Props {
  order: OrderDetail
  serviceNames: Record<string, string>
  servicePrices: Record<string, number>
  streetName: string
  onClose: () => void
}

function getTimeWindow(): string {
  const now = new Date()
  const start = new Date(now.getTime() + 15 * 60000)
  const end = new Date(now.getTime() + 5 * 60 * 60000)
  const fmt = (d: Date) => `${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
  return `Сегодня, ${fmt(start)}–${fmt(end)}`
}

const timelineSteps = [
  { icon: 'fa-person-walking', label: 'В пути' },
  { icon: 'fa-box', label: 'Забрали' },
  { icon: 'fa-soap', label: 'Чистим' },
  { icon: 'fa-truck', label: 'Идём отдавать' },
  { icon: 'fa-box-open', label: 'Доставлено' },
]

export function StatusScreen({ order, serviceNames, servicePrices, streetName, onClose }: Props) {
  const [showSupport, setShowSupport] = useState(false)

  const isCanceled = order.status === 'canceled'
  const isActive = ACTIVE_STATUSES.has(order.status)
  const statusStep = STATUS_STEP_MAP[order.status] || 1
  const isFree = order.is_free

  const basePrice = servicePrices['base'] ?? 1490
  const piecePrice = servicePrices['piece'] ?? 390
  const addonDetails = order.services
    .filter((s) => s !== 'base' && s !== 'piece')
    .map((slug) => ({ slug, name: serviceNames[slug] || slug, price: servicePrices[slug] ?? 0 }))

  const addressDisplay = `${streetName}, д. ${order.house}, кв. ${order.apartment}`

  return (
    <div className="status-screen">
      {isCanceled ? (
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
          {Array.from({ length: order.bags_number }, (_, i) => (
            <div key={`bag-${i}`} className="detail-row">
              <div className="detail-label"><i className="fas fa-box-open" /> Пакет</div>
              <div className="detail-value">{isFree ? <><s>{basePrice} ₽</s> 0 ₽</> : `${basePrice} ₽`}</div>
            </div>
          ))}
          {Array.from({ length: order.pieces_number }, (_, i) => (
            <div key={`piece-${i}`} className="detail-row">
              <div className="detail-label"><i className="fas fa-tshirt" /> Вещь</div>
              <div className="detail-value">{isFree ? <><s>{piecePrice} ₽</s> 0 ₽</> : `${piecePrice} ₽`}</div>
            </div>
          ))}
          {addonDetails.map((addon) => (
            <div key={addon.slug} className="detail-row">
              <div className="detail-label"><i className="fas fa-plus-circle" /> {addon.name}</div>
              <div className="detail-value">{isFree ? <><s>{addon.price} ₽</s> 0 ₽</> : `+${addon.price} ₽`}</div>
            </div>
          ))}
          {isActive && (
            <div className="detail-row">
              <div className="detail-label"><i className="fas fa-calendar-alt" /> Время</div>
              <div className="detail-value">{getTimeWindow()}</div>
            </div>
          )}
          <div className="detail-row">
            <div className="detail-label"><i className="fas fa-map-pin" /> Адрес</div>
            <div className="detail-value">{addressDisplay}</div>
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
          <p><i className="fas fa-truck-fast" /> Курьер приедет в течение 15 минут</p>
          <p><i className="fas fa-door-open" /> Заберёт вещи у двери, вернёт чистыми через 3–5 часов</p>
        </div>
      )}

      {!isCanceled && (
        <div className="status-timeline">
          {timelineSteps.map((s, i) => (
            <div key={i} className={`timeline-step${statusStep === i + 1 ? ' active' : ''}`}>
              <div className="step-icon"><i className={`fas ${s.icon}`} /></div>
              <div className="step-label">{s.label}</div>
            </div>
          ))}
        </div>
      )}

      <div className="status-actions">
        <button className="status-btn" onClick={() => setShowSupport(true)}>
          <i className="fas fa-headset" /> Связаться с поддержкой
        </button>
        <button className="status-btn" onClick={onClose}>
          <i className="fas fa-arrow-left" /> На главную
        </button>
      </div>

      {showSupport && (
        <div className="modal-overlay" onClick={() => setShowSupport(false)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()}>
            <h3><i className="fas fa-headset" /> Поддержка</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16, margin: '20px 0' }}>
              <a href="tel:+79291234567" className="support-contact-link">
                <i className="fas fa-phone" /> +7 929 123-45-67
              </a>
              <a href="https://t.me/VITALII_PRIHODKO" target="_blank" rel="noreferrer" className="support-contact-link">
                <i className="fab fa-telegram" /> @VITALII_PRIHODKO
              </a>
              <a href="mailto:prihodko_1989@mail.ru" className="support-contact-link">
                <i className="fas fa-envelope" /> prihodko_1989@mail.ru
              </a>
            </div>
            <button className="status-btn" onClick={() => setShowSupport(false)}>Закрыть</button>
          </div>
        </div>
      )}

      {isActive && (
        <div className="status-note">
          <i className="fas fa-info-circle" /> Вы можете закрыть сайт — мы пришлём уведомление, когда курьер будет рядом
        </div>
      )}
    </div>
  )
}

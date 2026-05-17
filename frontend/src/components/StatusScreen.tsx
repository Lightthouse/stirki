import { useEffect, useState } from 'react'
import { getOrder } from '../api'
import { getStatusName } from '../utils/statusNames'

const STATUS_STEP_MAP: Record<string, number> = {
  new: 1,
  courier_pickup: 2,
  picked_up: 2,
  washing: 3,
  courier_delivery: 4,
  delivered: 4,
  canceled: 4,
}

const TERMINAL_STATUSES = new Set(['delivered', 'canceled'])

const ADDON_LABELS: Record<string, string> = {
  ironing: 'Глажка',
  conditioner: 'Кондиционер',
  vacuum_pack: 'Вакуумная упаковка',
}

interface Props {
  orderId: number
  totalPrice: number
  serviceType: 'bag' | 'piece'
  bagsNumber: number
  addons: string[]
  isFree: boolean
  addressDisplay: string
  comment?: string
  onClose: () => void
}

function getTimeWindow(): string {
  const now = new Date()
  const start = new Date(now.getTime() + 15 * 60000)
  const end = new Date(now.getTime() + 5 * 60 * 60000)
  const fmt = (d: Date) => `${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
  return `Сегодня, ${fmt(start)}–${fmt(end)}`
}

export function StatusScreen({ orderId, totalPrice, serviceType, bagsNumber, addons, isFree, addressDisplay, comment, onClose }: Props) {
  const [statusStep, setStatusStep] = useState(1)
  const [currentStatus, setCurrentStatus] = useState('new')
  const [showSupport, setShowSupport] = useState(false)

  useEffect(() => {
    if (orderId === 0) return
    const poll = setInterval(async () => {
      try {
        const order = await getOrder(orderId)
        setCurrentStatus(order.status)
        setStatusStep(STATUS_STEP_MAP[order.status] || 1)
        if (TERMINAL_STATUSES.has(order.status)) clearInterval(poll)
      } catch {
        // ignore
      }
    }, 10000)
    return () => clearInterval(poll)
  }, [orderId])

  const mainAddons = addons.filter((a) => a !== 'ironing')
  const hasIroning = addons.includes('ironing')
  const serviceLabel = serviceType === 'piece'
    ? 'Стирка вещи'
    : bagsNumber > 1
      ? `Стирка пакетов ×${bagsNumber}`
      : 'Стирка пакета'
  const serviceFull = serviceLabel + (hasIroning ? ' + глажка' : '')
  const addonsLabel = mainAddons.map((a) => ADDON_LABELS[a] || a).join(', ')
  const paymentLabel = isFree ? 'Бесплатно (реклама)' : 'Онлайн картой'
  const timeWindow = getTimeWindow()

  const timelineSteps = [
    { icon: 'fa-check', label: 'Заказ принят' },
    { icon: 'fa-person-walking', label: 'Курьер в пути' },
    { icon: 'fa-soap', label: 'Стирка' },
    { icon: 'fa-box-open', label: 'Доставлено' },
  ]

  return (
    <div className="status-screen">
      <div className="check-circle">
        <i className="fas fa-check" />
      </div>

      <div className="status-title">Заказ принят</div>
      <div style={{ marginBottom: 4 }}>
        <span className="order-number">
          <i className="fas fa-receipt" /> № {orderId > 0 ? `ST-${orderId}` : 'ST-—'}
        </span>
      </div>
      {orderId > 0 && (
        <div className="status-current-label">
          {getStatusName(currentStatus)}
        </div>
      )}
      {!isFree && <div className="order-total"><i className="fas fa-ruble-sign" /> {totalPrice} ₽</div>}

      <div className="details-card">
        <div className="card-content">
          <div className="detail-row">
            <div className="detail-label"><i className="fas fa-tshirt" /> Услуга</div>
            <div className="detail-value">{serviceFull}</div>
          </div>
          {mainAddons.length > 0 && (
            <div className="detail-row">
              <div className="detail-label"><i className="fas fa-plus-circle" /> Дополнительно</div>
              <div className="detail-value">{addonsLabel}</div>
            </div>
          )}
          <div className="detail-row">
            <div className="detail-label"><i className="fas fa-credit-card" /> Оплата</div>
            <div className="detail-value"><span className="badge-payment">{paymentLabel}</span></div>
          </div>
          <div className="detail-row">
            <div className="detail-label"><i className="fas fa-calendar-alt" /> Время</div>
            <div className="detail-value">{timeWindow}</div>
          </div>
          <div className="detail-row">
            <div className="detail-label"><i className="fas fa-map-pin" /> Адрес</div>
            <div className="detail-value">{addressDisplay}</div>
          </div>
          {comment && (
            <div className="detail-row">
              <div className="detail-label"><i className="fas fa-comment" /> Комментарий</div>
              <div className="detail-value">{comment}</div>
            </div>
          )}
        </div>
      </div>

      <div className="small-card">
        <p><i className="fas fa-truck-fast" /> Курьер приедет в течение 15 минут</p>
        <p><i className="fas fa-door-open" /> Заберёт вещи у двери, вернёт чистыми через 3–5 часов</p>
      </div>

      <div className="status-timeline">
        {timelineSteps.map((s, i) => (
          <div key={i} className={`timeline-step${statusStep >= i + 1 ? ' active' : ''}`}>
            <div className="step-icon"><i className={`fas ${s.icon}`} /></div>
            <div className="step-label">{s.label}</div>
          </div>
        ))}
      </div>

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

      <div className="status-note">
        <i className="fas fa-info-circle" /> Вы можете закрыть сайт — мы пришлём уведомление, когда курьер будет рядом
      </div>
    </div>
  )
}

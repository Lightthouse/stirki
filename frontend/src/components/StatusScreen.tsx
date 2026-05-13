import { useEffect, useState } from 'react'
import { getOrder } from '../api'

const STATUS_STEP_MAP: Record<string, number> = {
  waiting_for_capture: 1,
  new: 1,
  courier_pickup: 2,
  picked_up: 2,
  washing: 3,
  drying: 3,
  ironing: 3,
  packing: 3,
  courier_delivery: 4,
  delivered: 4,
}

const ADDON_LABELS: Record<string, string> = {
  ironing: 'Глажка',
  conditioner: 'Кондиционер',
  vacuum_pack: 'Вакуумная упаковка',
}

interface Props {
  orderId: number
  totalPrice: number
  serviceType: 'bag' | 'piece'
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

export function StatusScreen({ orderId, totalPrice, serviceType, addons, isFree, addressDisplay, comment, onClose }: Props) {
  const [statusStep, setStatusStep] = useState(1)

  useEffect(() => {
    if (orderId === 0) return
    const poll = setInterval(async () => {
      try {
        const order = await getOrder(orderId)
        const step = STATUS_STEP_MAP[order.status] || 1
        setStatusStep(step)
        if (step >= 4) clearInterval(poll)
      } catch {
        // ignore
      }
    }, 10000)
    return () => clearInterval(poll)
  }, [orderId])

  const serviceLabel = serviceType === 'piece' ? 'Вещь' : 'Пакет'
  const mainAddons = addons.filter((a) => a !== 'ironing')
  const hasIroning = addons.includes('ironing')
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
        <a href="mailto:prihodko_1989@mail.ru" style={{ textDecoration: 'none', width: '100%' }}>
          <button className="status-btn">
            <i className="fas fa-headset" /> Связаться с поддержкой
          </button>
        </a>
        <button className="status-btn" onClick={onClose}>
          <i className="fas fa-arrow-left" /> На главную
        </button>
      </div>

      <div className="status-note">
        <i className="fas fa-info-circle" /> Вы можете закрыть сайт — мы пришлём уведомление, когда курьер будет рядом
      </div>
    </div>
  )
}

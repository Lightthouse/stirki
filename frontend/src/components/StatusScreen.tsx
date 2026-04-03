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

interface Props {
  orderId: number
  totalPrice: number
  onClose: () => void
}

export function StatusScreen({ orderId, totalPrice, onClose }: Props) {
  const [statusStep, setStatusStep] = useState(1)
  const [_statusLabel, setStatusLabel] = useState('Заказ принят')

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

  useEffect(() => {
    const labels = ['', 'Заказ принят', 'Курьер в пути', 'Стирка', 'Доставлено']
    setStatusLabel(labels[statusStep] || 'Заказ принят')
  }, [statusStep])

  const timelineSteps = [
    { icon: 'fa-check', label: 'Заказ принят' },
    { icon: 'fa-person-walking', label: 'Курьер в пути' },
    { icon: 'fa-soap', label: 'Стирка' },
    { icon: 'fa-box-open', label: 'Доставлено' },
  ]

  return (
    <div className="status-screen">
      <div className="status-container">
        <div className="status-checkmark">
          <i className="fas fa-check-circle" />
        </div>
        <h3 className="status-title">✅ Заказ принят!</h3>
        <p className="status-message">
          Номер заказа: <strong>{orderId > 0 ? `#${orderId}` : '#—'}</strong>
          <br />
          Сумма: <strong>{totalPrice} ₽</strong>
        </p>
        <p className="status-info">
          🚚 Курьер приедет в течение 15 минут
          <br />
          📍 Заберёт вещи у двери, вернёт чистыми через 3-5 часов
        </p>

        <div className="status-timeline">
          {timelineSteps.map((s, i) => (
            <div key={i} className={`timeline-step${statusStep >= i + 1 ? ' active' : ''}`}>
              <div className="step-icon">
                <i className={`fas ${s.icon}`} />
              </div>
              <div className="step-label">{s.label}</div>
            </div>
          ))}
        </div>

        <div className="status-actions">
          <button className="status-btn status-btn-primary">
            <i className="fas fa-map-marker-alt" /> Отследить
          </button>
          <a
            href="https://wa.me/79991234567"
            target="_blank"
            rel="noopener noreferrer"
            style={{ textDecoration: 'none' }}
          >
            <button className="status-btn status-btn-secondary" style={{ width: '100%' }}>
              <i className="fas fa-headset" /> Связаться
            </button>
          </a>
          <button className="status-btn status-btn-outline" onClick={onClose}>
            <i className="fas fa-times" /> Закрыть
          </button>
        </div>

        <div className="status-note">
          <i className="fas fa-info-circle" />
          Вы можете закрыть сайт — мы пришлём уведомление, когда курьер будет рядом
        </div>
      </div>
    </div>
  )
}

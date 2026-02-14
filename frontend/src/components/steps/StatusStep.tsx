import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '../ui/Button'
import { getOrder, simulatePayment } from '../../api'
import type { OrderDetail } from '../../types'
import { STATUS_NAMES } from '../../utils/statusNames'

interface Props {
  orderId: number
  onNewOrder: () => void
}

export function StatusStep({ orderId, onNewOrder }: Props) {
  const [order, setOrder] = useState<OrderDetail | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchOrder = () => {
      getOrder(orderId)
        .then(setOrder)
        .catch((e) => setError(e instanceof Error ? e.message : 'Ошибка'))
    }

    fetchOrder()
    const interval = setInterval(fetchOrder, 10000)
    return () => clearInterval(interval)
  }, [orderId])

  if (error) {
    return (
      <div className="step">
        <h2>Ошибка</h2>
        <p className="error">{error}</p>
      </div>
    )
  }

  if (!order) {
    return (
      <div className="step">
        <h2>Загрузка...</h2>
      </div>
    )
  }

  return (
    <div className="step">
      <h2>Заказ #{order.id}</h2>
      <div className="status-badge">
        {STATUS_NAMES[order.status] || order.status}
      </div>
      <div className="confirm-details">
        <div className="confirm-row">
          <span>Адрес:</span>
          <span>{order.street}, д. {order.house}, кв. {order.apartment}</span>
        </div>
        <div className="confirm-row">
          <span>Пакетов:</span>
          <span>{order.bags_number}</span>
        </div>
        <div className="confirm-row">
          <span>Сумма:</span>
          <span>{order.total_price_rub} &#8381;</span>
        </div>
        <div className="confirm-row">
          <span>Оплата:</span>
          <span>{order.payment_status === 'succeeded' ? 'Оплачен' : 'Ожидание'}</span>
        </div>
      </div>
      {order.status === 'waiting_for_capture' && (
        <Button
          fullWidth
          onClick={() => {
            simulatePayment(orderId).then(() => {
              getOrder(orderId).then(setOrder)
            })
          }}
          style={{ marginBottom: '0.5rem', background: '#f59e0b' }}
        >
          Симулировать оплату (dev)
        </Button>
      )}
      <Button fullWidth onClick={onNewOrder}>
        Новый заказ
      </Button>
      <Link to="/orders" className="nav-link">
        Мои заказы
      </Link>
    </div>
  )
}

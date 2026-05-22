import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getOrders, getOrder } from '../api'
import { isAuthenticated } from '../api/client'
import { Button } from '../components/ui/Button'
import { STATUS_NAMES, ACTIVE_STATUSES } from '../utils/orderStatuses'
import type { OrderListItem, OrderDetail } from '../types'

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function OrdersPage() {
  const navigate = useNavigate()
  const [orders, setOrders] = useState<OrderListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedOrder, setSelectedOrder] = useState<OrderDetail | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)

  useEffect(() => {
    if (!isAuthenticated()) {
      navigate('/')
      return
    }
    getOrders()
      .then(setOrders)
      .catch((e) => setError(e instanceof Error ? e.message : 'Ошибка'))
      .finally(() => setLoading(false))
  }, [navigate])

  const handleOrderClick = (orderId: number) => {
    if (selectedOrder?.id === orderId) {
      setSelectedOrder(null)
      return
    }
    setDetailLoading(true)
    getOrder(orderId)
      .then(setSelectedOrder)
      .catch(() => {})
      .finally(() => setDetailLoading(false))
  }

  if (loading) {
    return (
      <div className="page">
        <header className="header">
          <h1>Стирки ON</h1>
        </header>
        <main className="main">
          <div className="step">
            <h2>Загрузка...</h2>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="page">
      <header className="header">
        <h1>Стирки ON</h1>
      </header>
      <main className="main">
        <div className="step">
          <h2>Мои заказы</h2>

          {error && <p className="error">{error}</p>}

          {orders.length === 0 && !error && (
            <p className="step-description">У вас пока нет заказов</p>
          )}

          <div className="orders-list">
            {orders.map((order) => {
              const isActive = ACTIVE_STATUSES.has(order.status)
              return (
                <div key={order.id}>
                  <button
                    className={`order-card ${isActive ? 'order-card-active' : ''}`}
                    onClick={() => handleOrderClick(order.id)}
                  >
                    <div className="order-card-header">
                      <span className="order-card-id">#{order.id}</span>
                      <span className="order-card-date">{formatDate(order.created_at)}</span>
                    </div>
                    <div className="order-card-body">
                      <span className={`status-badge-sm ${isActive ? 'status-badge-active' : 'status-badge-done'}`}>
                        {STATUS_NAMES[order.status] || order.status}
                      </span>
                      <span className="order-card-price">{order.total_price_rub} &#8381;</span>
                    </div>
                  </button>

                  {selectedOrder?.id === order.id && (
                    <div className="order-detail">
                      <div className="confirm-details">
                        <div className="confirm-row">
                          <span>Адрес:</span>
                          <span>{selectedOrder.street}, д. {selectedOrder.house}, кв. {selectedOrder.apartment}</span>
                        </div>
                        {selectedOrder.bags_number > 0 && (
                          <div className="confirm-row">
                            <span>Пакетов:</span>
                            <span>{selectedOrder.bags_number}</span>
                          </div>
                        )}
                        {selectedOrder.pieces_number > 0 && (
                          <div className="confirm-row">
                            <span>Вещей:</span>
                            <span>{selectedOrder.pieces_number}</span>
                          </div>
                        )}
                        <div className="confirm-row">
                          <span>Сумма:</span>
                          <span>{selectedOrder.total_price_rub} &#8381;</span>
                        </div>
                        <div className="confirm-row">
                          <span>Оплата:</span>
                          <span>{selectedOrder.payment_status === 'succeeded' ? 'Оплачен' : 'Ожидание'}</span>
                        </div>
                        {selectedOrder.comment && (
                          <div className="confirm-row">
                            <span>Комментарий:</span>
                            <span>{selectedOrder.comment}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {detailLoading && <p className="step-description">Загрузка...</p>}

          <Button fullWidth onClick={() => navigate('/')}>
            Новый заказ
          </Button>
        </div>
      </main>
    </div>
  )
}

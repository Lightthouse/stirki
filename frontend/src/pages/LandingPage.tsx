import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { isAuthenticated, clearToken, clearPhone } from '../api/client'
import { trackVisit, getAppStatus, getOrders, getMe } from '../api'
import { InfoModal } from '../components/ui/InfoModal'
import type { OrderListItem, ClientInfo } from '../types'
import { getStatusName } from '../utils/statusNames'

const ACTIVE_STATUSES = new Set([
  'waiting_for_capture', 'new', 'courier_pickup', 'picked_up',
  'washing', 'drying', 'ironing', 'packing', 'courier_delivery',
])

export function LandingPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [launched, setLaunched] = useState<boolean | null>(null)
  const [showPrelaunch, setShowPrelaunch] = useState(false)
  const [showInfo, setShowInfo] = useState(false)
  const [client, setClient] = useState<ClientInfo | null>(null)
  const [orders, setOrders] = useState<OrderListItem[]>([])
  const [loadingOrders, setLoadingOrders] = useState(false)

  const authenticated = isAuthenticated()

  useEffect(() => {
    const ref = searchParams.get('ref')
    if (ref && !authenticated) {
      trackVisit(ref).catch(() => {})
    }

    getAppStatus()
      .then((s) => setLaunched(s.launched))
      .catch(() => setLaunched(true))

    if (authenticated) {
      getMe().then(setClient).catch(() => {})
      setLoadingOrders(true)
      getOrders()
        .then(setOrders)
        .catch(() => {})
        .finally(() => setLoadingOrders(false))
    }
  }, [])

  function handleOrder() {
    if (launched === false) {
      setShowPrelaunch(true)
    } else {
      navigate('/order')
    }
  }

  function handleLogout() {
    clearToken()
    clearPhone()
    navigate('/')
    window.location.reload()
  }

  function formatDate(iso: string) {
    const d = new Date(iso)
    return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' })
  }

  return (
    <div className="start-screen">
      <div className="form-card">
        <div className="logo-large">стирка<span className="accent">он</span></div>

        {!authenticated ? (
          <>
            <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.7)', marginBottom: 20, lineHeight: 1.8 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                <i className="fas fa-door-open" style={{ color: '#ffd966', width: 18 }} />
                <span>Забираем у двери в обычном пакете</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                <i className="fas fa-tshirt" style={{ color: '#ffd966', width: 18 }} />
                <span>Индивидуальная стирка — только ваши вещи</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <i className="fas fa-truck" style={{ color: '#ffd966', width: 18 }} />
                <span>Стираем, сушим, гладим и возвращаем</span>
              </div>
            </div>
            <button className="btn-pill btn-pill-accent" onClick={() => navigate('/login')}>
              <i className="fas fa-sign-in-alt" /> Вход / Регистрация
            </button>
            <div className="small-text" style={{ marginTop: 14 }}>
              <span className="link-text" onClick={() => setShowInfo(true)}>
                📖 Подробнее о сервисе
              </span>
            </div>
          </>
        ) : (
          <>
            {client && (
              <div className="profile-block">
                <div className="profile-name">{client.name || 'Клиент'}</div>
                <div>{client.phone}</div>
                {client.street && (
                  <div style={{ color: 'rgba(255,255,255,0.5)', fontSize: 12 }}>
                    {client.street}, д. {client.house}, кв. {client.apartment}
                  </div>
                )}
              </div>
            )}

            <button className="btn-pill btn-pill-accent" onClick={handleOrder}>
              <i className="fas fa-plus" /> Новый заказ
            </button>

            {loadingOrders ? (
              <p style={{ textAlign: 'center', color: 'rgba(255,255,255,0.4)', fontSize: 13, marginTop: 16 }}>
                Загрузка заказов...
              </p>
            ) : orders.length > 0 ? (
              <div className="orders-list">
                {orders.map((order) => {
                  const isActive = ACTIVE_STATUSES.has(order.status)
                  return (
                    <div key={order.id} className={`order-card${isActive ? ' active' : ''}`}>
                      <div className="order-card-header">
                        <span className="order-card-id">Заказ #{order.id}</span>
                        <span className="order-card-date">{formatDate(order.created_at)}</span>
                      </div>
                      <div className="order-card-body">
                        <span className="order-card-price">{order.total_price_rub} ₽</span>
                        <span className={`status-badge-sm ${isActive ? 'status-badge-active' : 'status-badge-done'}`}>
                          {getStatusName(order.status)}
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : (
              <p style={{ textAlign: 'center', color: 'rgba(255,255,255,0.4)', fontSize: 13, marginTop: 16 }}>
                Заказов пока нет
              </p>
            )}

            <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 4 }}>
              <div className="small-text">
                <span className="link-text" onClick={() => setShowInfo(true)}>
                  📖 Подробнее о сервисе
                </span>
              </div>
              <button className="btn-ghost" onClick={handleLogout}>
                <i className="fas fa-sign-out-alt" /> Выйти
              </button>
            </div>
          </>
        )}
      </div>

      {showPrelaunch && (
        <div className="modal-overlay" onClick={() => setShowPrelaunch(false)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()}>
            <h3>Скоро открываемся!</h3>
            <p>Мы начнём принимать заказы совсем скоро и сообщим вам первыми!</p>
            <button className="btn-pill btn-pill-accent" onClick={() => setShowPrelaunch(false)}>
              Закрыть
            </button>
          </div>
        </div>
      )}

      {showInfo && <InfoModal onClose={() => setShowInfo(false)} />}
    </div>
  )
}

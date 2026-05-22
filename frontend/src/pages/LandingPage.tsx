import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { isAuthenticated, clearToken, clearPhone } from '../api/client'
import { trackVisit, getOrders, getMe, getAddresses, getOrder, getServices } from '../api'

const POLL_INTERVAL_MS = 60_000
import { InfoModal } from '../components/ui/InfoModal'
import { OfferModal } from '../components/ui/OfferModal'
import { PwaBanner } from '../components/PwaBanner'
import type { OrderListItem, OrderDetail, ServiceItem, ClientInfo } from '../types'
import { getStatusName, ACTIVE_STATUSES } from '../utils/orderStatuses'

export function LandingPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [showInfo, setShowInfo] = useState(false)
  const [showOffer, setShowOffer] = useState(false)
  const [showActiveOrderModal, setShowActiveOrderModal] = useState(false)
  const [client, setClient] = useState<ClientInfo | null>(null)
  const [orders, setOrders] = useState<OrderListItem[]>([])
  const [loadingOrders, setLoadingOrders] = useState(false)
  const [slugToStreet, setSlugToStreet] = useState<Record<string, string>>({})
  const [services, setServices] = useState<ServiceItem[]>([])
  const [selectedOrderId, setSelectedOrderId] = useState<number | null>(null)
  const [selectedOrder, setSelectedOrder] = useState<OrderDetail | null>(null)
  const [loadingDetail, setLoadingDetail] = useState(false)

  const authenticated = isAuthenticated()
  const hasActiveOrders = orders.some((o) => ACTIVE_STATUSES.has(o.status))

  useEffect(() => {
    const ref = searchParams.get('ref')
    if (ref && !authenticated) {
      trackVisit(ref).catch(() => {})
    }

    getAddresses()
      .then((res) => {
        const map: Record<string, string> = {}
        res.streets.forEach((s) => { map[s.slug] = s.name })
        setSlugToStreet(map)
      })
      .catch(() => {})
    getServices().then(setServices).catch(() => {})

    if (authenticated) {
      getMe().then(setClient).catch(() => {})
      setLoadingOrders(true)
      getOrders()
        .then(setOrders)
        .catch(() => {})
        .finally(() => setLoadingOrders(false))
    }
  }, [])

  useEffect(() => {
    if (!authenticated || !hasActiveOrders) return
    const poll = setInterval(() => {
      getOrders().then(setOrders).catch(() => {})
    }, POLL_INTERVAL_MS)
    return () => clearInterval(poll)
  }, [authenticated, hasActiveOrders])

  function handleOrder() {
    if (orders.some((o) => ACTIVE_STATUSES.has(o.status))) {
      setShowActiveOrderModal(true)
      return
    }
    navigate('/order')
  }

  function handleOrderClick(orderId: number) {
    setSelectedOrderId(orderId)
    setSelectedOrder(null)
    setLoadingDetail(true)
    getOrder(orderId)
      .then(setSelectedOrder)
      .catch(() => {})
      .finally(() => setLoadingDetail(false))
  }

  const serviceNames: Record<string, string> = Object.fromEntries(
    services.map((s) => [s.slug, s.name])
  )

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
      <div className="app-header">
        <div className="app-logo">
          стирка<span>он</span>
        </div>
        <div className="header-actions">
          <div className="header-icon" onClick={() => setShowInfo(true)} title="О сервисе">
            <i className="fas fa-info-circle" />
          </div>
        </div>
      </div>
      <div className="form-card">
        {!authenticated ? (
          <>
            <div className="hero-title-large">
              Бесплатный сервис<br />
              по стирке и глажке<br />
              повседневной одежды<br />
              с доставкой
            </div>
            <ul className="hero-features-list">
              <li>Забираем у вашей двери в обычном пакете, возвращаем в нашей фирменной упаковке</li>
              <li>Индивидуальная стирка — каждый заказ в отдельной стиральной машине</li>
              <li>Стираем, сушим, гладим и возвращаем в тот же день</li>
            </ul>
            <button className="btn-pill btn-pill-accent" onClick={() => navigate('/login')}>
              Вход / Регистрация
            </button>
            <div className="small-text" style={{ marginTop: 14, display: 'flex', flexDirection: 'column', gap: 4 }}>
              <span className="link-text" onClick={() => setShowInfo(true)}>
                Подробнее о сервисе
              </span>
              <span className="link-text" onClick={() => setShowOffer(true)}>
                Публичная оферта
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
                  <div style={{ color: '#9AAEAA', fontSize: 12 }}>
                    {slugToStreet[client.street] ?? client.street}, д. {client.house}, кв. {client.apartment}
                  </div>
                )}
              </div>
            )}

            <button className="btn-pill btn-pill-accent" onClick={handleOrder}>
              <i className="fas fa-plus" /> Новый заказ
            </button>

            {loadingOrders ? (
              <p style={{ textAlign: 'center', color: '#9AAEAA', fontSize: 13, marginTop: 16 }}>
                Загрузка заказов...
              </p>
            ) : orders.length > 0 ? (
              <div className="orders-list">
                {orders.map((order) => {
                  const isActive = ACTIVE_STATUSES.has(order.status)
                  return (
                    <div
                      key={order.id}
                      className={`order-card${isActive ? ' active' : ''}`}
                      style={{ cursor: 'pointer' }}
                      onClick={() => handleOrderClick(order.id)}
                    >
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
              <p style={{ textAlign: 'center', color: '#9AAEAA', fontSize: 13, marginTop: 16 }}>
                Заказов пока нет
              </p>
            )}

            <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 4 }}>
              <div className="small-text">
                <span className="link-text" onClick={() => setShowInfo(true)}>
                  Подробнее о сервисе
                </span>
              </div>
              <div className="small-text">
                <span className="link-text" onClick={() => setShowOffer(true)}>
                  Публичная оферта
                </span>
              </div>
              <button className="btn-ghost" onClick={handleLogout}>
                <i className="fas fa-sign-out-alt" /> Выйти
              </button>
            </div>
          </>
        )}
      </div>

      {showInfo && <InfoModal onClose={() => setShowInfo(false)} />}
      {showOffer && <OfferModal onClose={() => setShowOffer(false)} />}
      {showActiveOrderModal && (
        <div className="modal-overlay" onClick={() => setShowActiveOrderModal(false)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()}>
            <h3><i className="fas fa-clock" /> Заказ уже в работе</h3>
            <p>
              У вас есть активный заказ. Оформить новый можно будет после его завершения.
            </p>
            <button className="btn-pill btn-pill-accent" onClick={() => setShowActiveOrderModal(false)}>
              Понятно
            </button>
          </div>
        </div>
      )}
      {selectedOrderId !== null && (
        <div className="modal-overlay" onClick={() => setSelectedOrderId(null)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()}>
            <h3><i className="fas fa-receipt" /> Заказ #{selectedOrderId}</h3>

            {loadingDetail && (
              <p style={{ textAlign: 'center', color: 'var(--text-faint)', fontSize: 13 }}>
                Загрузка...
              </p>
            )}

            {!loadingDetail && selectedOrder && (() => {
              const streetName = slugToStreet[selectedOrder.street] ?? selectedOrder.street
              const address = `${streetName}, д. ${selectedOrder.house}, кв. ${selectedOrder.apartment}`
              const createdAt = new Date(selectedOrder.created_at).toLocaleString('ru-RU', {
                day: 'numeric', month: 'long', year: 'numeric',
                hour: '2-digit', minute: '2-digit',
              })
              const parts: string[] = []
              if (selectedOrder.bags_number > 0) parts.push(selectedOrder.bags_number > 1 ? `Пакетов × ${selectedOrder.bags_number}` : 'Пакет')
              if (selectedOrder.pieces_number > 0) parts.push(selectedOrder.pieces_number > 1 ? `Вещей × ${selectedOrder.pieces_number}` : 'Вещь')
              const typeLabel = parts.join(' + ') || 'Стирка'
              const countLabel = ''
              const addons = selectedOrder.services
                .filter((s) => s !== 'base' && s !== 'piece')
                .map((s) => serviceNames[s] || s)

              return (
                <>
                  <section>
                    <h4><i className="fas fa-map-pin" style={{ marginRight: 6 }} />Адрес</h4>
                    <p>{address}</p>
                  </section>

                  <section>
                    <h4><i className="fas fa-calendar-alt" style={{ marginRight: 6 }} />Оформлен</h4>
                    <p>{createdAt}</p>
                  </section>

                  <section>
                    <h4><i className="fas fa-box-open" style={{ marginRight: 6 }} />Состав</h4>
                    <ul>
                      <li style={{ fontWeight: 600, color: 'var(--text)' }}>
                        {typeLabel}{countLabel}
                      </li>
                      {addons.map((name) => (
                        <li key={name}>+ {name}</li>
                      ))}
                    </ul>
                  </section>

                  <section>
                    <h4><i className="fas fa-ruble-sign" style={{ marginRight: 6 }} />Итого</h4>
                    <p style={{ fontWeight: 700, color: 'var(--teal)', fontSize: 18 }}>
                      {selectedOrder.is_free ? 'Бесплатно' : `${selectedOrder.total_price_rub} ₽`}
                    </p>
                  </section>

                  {selectedOrder.comment && (
                    <section>
                      <h4><i className="fas fa-comment" style={{ marginRight: 6 }} />Комментарий</h4>
                      <p>{selectedOrder.comment}</p>
                    </section>
                  )}
                </>
              )
            })()}

            {!loadingDetail && !selectedOrder && (
              <p style={{ textAlign: 'center', color: 'var(--text-faint)', fontSize: 13 }}>
                Не удалось загрузить данные
              </p>
            )}

            <button className="btn-pill" onClick={() => setSelectedOrderId(null)}>
              Закрыть
            </button>
          </div>
        </div>
      )}

      <PwaBanner />
    </div>
  )
}

import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { isAuthenticated } from '../api/client'
import { getOrder, getServices, getAddresses } from '../api'
import { StatusScreen } from '../components/StatusScreen'
import { TERMINAL_STATUSES } from '../utils/orderStatuses'
import type { OrderDetail, ServiceItem, Street } from '../types'

const POLL_INTERVAL_MS = 60_000

export function OrderStatusPage() {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const orderId = Number(id)

  const [order, setOrder] = useState<OrderDetail | null>(null)
  const [services, setServices] = useState<ServiceItem[]>([])
  const [streets, setStreets] = useState<Street[]>([])
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    if (!isAuthenticated()) {
      navigate('/login')
      return
    }
    getServices().then(setServices).catch(() => {})
    getAddresses().then((res) => setStreets(res.streets)).catch(() => {})
  }, [])

  useEffect(() => {
    if (!orderId) {
      setNotFound(true)
      return
    }
    let cancelled = false
    const fetchOrder = async () => {
      try {
        const o = await getOrder(orderId)
        if (cancelled) return
        setOrder(o)
        if (TERMINAL_STATUSES.has(o.status)) clearInterval(poll)
      } catch {
        if (!cancelled) setNotFound(true)
      }
    }
    const poll = setInterval(fetchOrder, POLL_INTERVAL_MS)
    fetchOrder()
    return () => {
      cancelled = true
      clearInterval(poll)
    }
  }, [orderId])

  if (notFound) {
    return (
      <div className="status-screen">
        <div className="status-title">Заказ не найден</div>
        <div className="status-actions">
          <button className="status-btn" onClick={() => navigate('/')}>
            <i className="fas fa-arrow-left" /> На главную
          </button>
        </div>
      </div>
    )
  }

  if (!order) {
    return (
      <div className="status-screen">
        <div className="status-current-label">Загрузка...</div>
      </div>
    )
  }

  const serviceNames: Record<string, string> = Object.fromEntries(services.map((s) => [s.slug, s.name]))
  const servicePrices: Record<string, number> = Object.fromEntries(services.map((s) => [s.slug, s.price_rub]))
  const streetName = streets.find((s) => s.slug === order.street)?.name ?? order.street

  return (
    <StatusScreen
      order={order}
      serviceNames={serviceNames}
      servicePrices={servicePrices}
      streetName={streetName}
      onClose={() => navigate('/')}
    />
  )
}

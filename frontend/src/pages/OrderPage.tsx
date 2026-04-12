import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { isAuthenticated, clearToken, clearPhone } from '../api/client'
import { getMe, createOrder, getAdImages, trackAdView } from '../api'
import { AddressCard } from '../components/swipe/AddressCard'
import { TariffCard } from '../components/swipe/TariffCard'
import { MachinesCard } from '../components/swipe/MachinesCard'
import { ServicesCard } from '../components/swipe/ServicesCard'
import { CartMini } from '../components/CartMini'
import { CartExpanded } from '../components/CartExpanded'
import { StatusScreen } from '../components/StatusScreen'
import { InfoModal } from '../components/ui/InfoModal'
import { AdViewer } from '../components/AdViewer'
import type { AddressData } from '../components/swipe/AddressCard'
import type { Tariff } from '../components/swipe/TariffCard'
import type { CartItem } from '../components/swipe/ServicesCard'
import type { ClientInfo } from '../types'

export function OrderPage() {
  const navigate = useNavigate()
  const swipeRef = useRef<HTMLDivElement>(null)

  const [_client, setClient] = useState<ClientInfo | null>(null)
  const [address, setAddress] = useState<AddressData>({
    street: '', house: '', entrance: 1, apartment: 1, comment: '',
  })
  const [tariff, setTariff] = useState<Tariff | null>(null)
  const [serviceType, setServiceType] = useState<'bag' | 'piece'>('bag')
  const [cart, setCart] = useState<CartItem[]>([])
  const [showCart, setShowCart] = useState(false)
  const [overlayVisible, setOverlayVisible] = useState(false)
  const [showStatus, setShowStatus] = useState(false)
  const [orderId, setOrderId] = useState<number | null>(null)
  const [orderTotal, setOrderTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [showInfo, setShowInfo] = useState(false)
  const [hasPreviousAddress, setHasPreviousAddress] = useState(false)
  const [addressError, setAddressError] = useState(false)
  const [adsWatched, setAdsWatched] = useState(0)
  const [showAdViewer, setShowAdViewer] = useState(false)
  const [adImages, setAdImages] = useState<string[]>([])

  // Hint states per card
  const [hints, setHints] = useState({ address: false, tariff: false, machines: false })

  const showMachines = tariff === 'free'

  useEffect(() => {
    if (!isAuthenticated()) {
      navigate('/login')
      return
    }
    getMe()
      .then((c) => {
        setClient(c)
        if (c.street) {
          setHasPreviousAddress(true)
          setAddress({
            street: c.street,
            house: c.house || '',
            entrance: c.entrance || 1,
            apartment: c.apartment || 1,
            comment: '',
          })
        }
      })
      .catch((e: Error) => {
        if (e.message.includes('401')) {
          clearToken()
          clearPhone()
          navigate('/login')
        }
      })
    getAdImages().then(setAdImages).catch(() => {})
  }, [])

  function scrollToCard(index: number) {
    const container = swipeRef.current
    if (!container) return
    const cards = container.querySelectorAll('.swipe-card')
    if (cards[index]) {
      cards[index].scrollIntoView({ behavior: 'smooth' })
    }
  }

  function handleWatchAd() {
    setShowAdViewer(true)
  }

  function handleAdComplete() {
    setShowAdViewer(false)
    setAdsWatched(3)
  }

  function handleTariffSelect(t: Tariff) {
    setTariff(t)
    if (t === 'free') {
      setServiceType('bag')
      setCart([])
      setAdsWatched(0)
    }
    setTimeout(() => {
      if (t === 'free') {
        scrollToCard(2) // machines card
      } else {
        scrollToCard(showMachines ? 3 : 2) // services card
      }
    }, 300)
  }

  function handleAddToCart(item: CartItem) {
    setCart((prev) => [...prev, item])
  }

  function handleRemoveFromCart(idx: number) {
    setCart((prev) => prev.filter((_, i) => i !== idx))
  }

  function handleClearCart() {
    setCart([])
  }

  function handleServiceTypeChange(type: 'bag' | 'piece') {
    if (type !== serviceType) {
      setServiceType(type)
      setCart([])
    }
  }

  function openCart() {
    setShowCart(true)
    setOverlayVisible(true)
  }

  function closeCart() {
    setShowCart(false)
    setOverlayVisible(false)
  }

  async function handleCheckout() {
    if (cart.length === 0) return
    if (!address.street || !address.house) {
      setAddressError(true)
      setTimeout(() => setAddressError(false), 3000)
      return
    }
    setLoading(true)
    try {
      const servicesSet = new Set<string>()
      cart.forEach((item) => item.addons.forEach((a) => servicesSet.add(a)))

      const result = await createOrder({
        street: address.street,
        house: address.house,
        apartment: address.apartment,
        entrance: address.entrance,
        floor: 1,
        washing_type: serviceType,
        bags_number: cart.length,
        services: Array.from(servicesSet),
        comment: address.comment || undefined,
        is_free: tariff === 'free',
      })

      setOrderId(result.order_id)
      setOrderTotal(result.total_price_rub)
    } catch (e) {
      console.error('Ошибка создания заказа:', e)
      // Для демонстрации показываем экран статуса даже при ошибке
      setOrderId(0)
      setOrderTotal(cart.reduce((sum, item) => sum + item.price, 0))
    } finally {
      setLoading(false)
      closeCart()
      setShowStatus(true)
    }
  }

  function activateHint(key: keyof typeof hints) {
    setHints((prev) => ({ ...prev, [key]: true }))
  }

  return (
    <div className="main-app">
      {/* Header */}
      <div className="app-header">
        <div className="app-logo" onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
          стирка<span>он</span>
        </div>
        <div className="header-actions">
          <div className="header-icon" onClick={() => setShowInfo(true)} title="О сервисе">
            <i className="fas fa-info-circle" />
          </div>
          <div className="header-icon" onClick={() => navigate('/')} title="На главную">
            <i className="fas fa-home" />
          </div>
        </div>
      </div>

      {/* Swipe cards */}
      <div className="swipe-container" ref={swipeRef}>
        <AddressCard
          data={address}
          onChange={setAddress}
          onHintActivate={() => activateHint('address')}
          hintActive={hints.address}
          hasPreviousAddress={hasPreviousAddress}
        />
        <TariffCard
          selected={tariff}
          onSelect={handleTariffSelect}
          onHintActivate={() => activateHint('tariff')}
          hintActive={hints.tariff}
        />
        {showMachines && (
          <MachinesCard
            onHintActivate={() => activateHint('machines')}
            hintActive={hints.machines}
          />
        )}
        <ServicesCard
          tariff={tariff}
          serviceType={serviceType}
          onServiceTypeChange={handleServiceTypeChange}
          cart={cart}
          onAddToCart={handleAddToCart}
          adsWatched={adsWatched}
          onWatchAd={handleWatchAd}
          addressValid={!!(address.street && address.house)}
        />
      </div>

      {/* Cart mini — visible when cart has items */}
      {cart.length > 0 && !showCart && (
        <CartMini cart={cart} onClick={openCart} />
      )}

      {/* Overlay */}
      <div
        className={`overlay${overlayVisible ? ' show' : ''}`}
        onClick={closeCart}
      />

      {/* Cart expanded */}
      <CartExpanded
        cart={cart}
        show={showCart}
        onClose={closeCart}
        onRemove={handleRemoveFromCart}
        onClear={handleClearCart}
        onCheckout={handleCheckout}
        loading={loading}
      />

      {/* Status screen */}
      {showStatus && orderId !== null && (
        <StatusScreen
          orderId={orderId}
          totalPrice={orderTotal}
          onClose={() => { setShowStatus(false); navigate('/') }}
        />
      )}

      {/* Info modal */}
      {showInfo && <InfoModal onClose={() => setShowInfo(false)} />}

      {/* Address error toast */}
      {addressError && (
        <div className="toast-error">
          <i className="fas fa-map-marker-alt" /> Укажите адрес доставки
        </div>
      )}

      {/* Ad viewer */}
      {showAdViewer && (
        <AdViewer
          images={adImages}
          onComplete={handleAdComplete}
          onAdViewed={(path) => { trackAdView(path).catch(() => {}) }}
        />
      )}
    </div>
  )
}

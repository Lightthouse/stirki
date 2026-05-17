import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { isAuthenticated, clearToken, clearPhone } from '../api/client'
import { getMe, createOrder, getOrder, getAdImages, trackAdView, getAddresses, getSystemSettings, verifyPayment, getOrderByPaymentToken } from '../api'
import { AddressCard } from '../components/swipe/AddressCard'
import { TariffCard } from '../components/swipe/TariffCard'
import { MachinesCard } from '../components/swipe/MachinesCard'
import { ServicesCard } from '../components/swipe/ServicesCard'
import { CartMini } from '../components/CartMini'
import { CartExpanded } from '../components/CartExpanded'
import { StatusScreen } from '../components/StatusScreen'
import { InfoModal } from '../components/ui/InfoModal'
import { AdViewer } from '../components/AdViewer'
import { OfferModal } from '../components/ui/OfferModal'
import { PrivacyModal } from '../components/ui/PrivacyModal'
import type { AddressData } from '../components/swipe/AddressCard'
import type { Tariff } from '../components/swipe/TariffCard'
import type { CartItem } from '../components/swipe/ServicesCard'
import type { ClientInfo, Street, OrderDetail } from '../types'

export function OrderPage() {
  const navigate = useNavigate()
  const swipeRef = useRef<HTMLDivElement>(null)
  const [activeCard, setActiveCard] = useState(0)

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

  const [paymentOrder, setPaymentOrder] = useState<OrderDetail | null>(null)
  const [hasPreviousAddress, setHasPreviousAddress] = useState(false)
  const [addressError, setAddressError] = useState(false)
  const [adsWatched, setAdsWatched] = useState(0)
  const [showAdViewer, setShowAdViewer] = useState(false)
  const [adImages, setAdImages] = useState<string[]>([])
  const [showOffer, setShowOffer] = useState(false)
  const [showPrivacy, setShowPrivacy] = useState(false)
  const [streets, setStreets] = useState<Street[]>([])
  const [statusAddons, setStatusAddons] = useState<string[]>([])
  const [freeTariffAvailable, setFreeTariffAvailable] = useState(true)
  const [freeTariffError, setFreeTariffError] = useState(false)
  const [activeOrderError, setActiveOrderError] = useState(false)
  const [orderError, setOrderError] = useState(false)

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
    getAddresses().then((res) => setStreets(res.streets)).catch(() => {})
    getSystemSettings().then((s) => setFreeTariffAvailable(s.free_tariff_is_available)).catch(() => {})
  }, [])

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const token = params.get('payment_token')
    if (token) {
      window.history.replaceState({}, '', '/order')
      getOrderByPaymentToken(token)
        .then((result) => {
          verifyPayment(result.order_id).catch(() => {})
          return getOrder(result.order_id)
        })
        .then((order) => {
          setPaymentOrder(order)
          setOrderId(order.id)
          setShowStatus(true)
        })
        .catch(() => {})
    }
  }, [])

  useEffect(() => {
    const container = swipeRef.current
    if (!container) return
    const onScroll = () => {
      const idx = Math.round(container.scrollTop / container.clientHeight)
      setActiveCard(idx)
    }
    container.addEventListener('scroll', onScroll, { passive: true })
    return () => container.removeEventListener('scroll', onScroll)
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
    const servicesSet = new Set<string>()
    cart.forEach((item) => item.addons.forEach((a) => servicesSet.add(a)))
    setStatusAddons(Array.from(servicesSet))
    setLoading(true)
    try {
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

      setLoading(false)
      closeCart()

      if (result.confirmation_url) {
        window.location.href = result.confirmation_url
        return
      }

      setOrderId(result.order_id)
      setOrderTotal(result.total_price_rub)
      setShowStatus(true)
    } catch (e) {
      setLoading(false)
      closeCart()
      if (e instanceof Error && e.message === 'У вас уже есть активный заказ') {
        setActiveOrderError(true)
        setTimeout(() => {
          setActiveOrderError(false)
          navigate('/')
        }, 2000)
      } else if (e instanceof Error && e.message === 'Бесплатный тариф временно недоступен') {
        setFreeTariffAvailable(false)
        setFreeTariffError(true)
        setTimeout(() => {
          setFreeTariffError(false)
          setTariff(null)
          setCart([])
          scrollToCard(0)
        }, 1000)
      } else {
        console.error('Ошибка создания заказа:', e)
        setOrderError(true)
        setTimeout(() => setOrderError(false), 4000)
      }
    }
  }

  function activateHint(key: keyof typeof hints) {
    setHints((prev) => ({ ...prev, [key]: true }))
  }

  return (
    <div className="main-app">
      {/* Vertical navigation dots */}
      <div className="v-dots">
        {Array.from({ length: showMachines ? 4 : 3 }, (_, i) => (
          <div key={i} className={`v-dot${activeCard === i ? ' active' : ''}`} />
        ))}
      </div>

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
            onMachineSelect={() => {
              setTimeout(() => scrollToCard(3), 350)
            }}
            freeTariffAvailable={freeTariffAvailable}
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
        onShowOffer={() => setShowOffer(true)}
        onShowPrivacy={() => setShowPrivacy(true)}
      />

      {/* Status screen */}
      {showStatus && orderId !== null && (
        <StatusScreen
          orderId={paymentOrder?.id ?? orderId}
          totalPrice={paymentOrder?.total_price_rub ?? orderTotal}
          serviceType={paymentOrder?.washing_type ?? serviceType}
          bagsNumber={paymentOrder?.bags_number ?? (cart.length || 1)}
          addons={paymentOrder?.services ?? statusAddons}
          isFree={paymentOrder ? paymentOrder.is_free : tariff === 'free'}
          addressDisplay={(() => {
            const src = paymentOrder ?? null
            const streetSlug = src ? src.street : address.street
            const house = src ? src.house : address.house
            const apt = src ? src.apartment : address.apartment
            const streetName = streets.find((s) => s.slug === streetSlug)?.name ?? streetSlug
            return `${streetName}, д. ${house}, кв. ${apt}`
          })()}
          comment={paymentOrder?.comment ?? (address.comment || undefined) ?? undefined}
          onClose={() => { setShowStatus(false); setPaymentOrder(null); navigate('/') }}
        />
      )}

      {/* Info modal */}
      {showInfo && <InfoModal onClose={() => setShowInfo(false)} />}

      {/* Legal modals */}
      {showOffer && <OfferModal onClose={() => setShowOffer(false)} />}
      {showPrivacy && <PrivacyModal onClose={() => setShowPrivacy(false)} />}

      {/* Address error toast */}
      {addressError && (
        <div className="toast-error">
          <i className="fas fa-map-marker-alt" /> Укажите адрес доставки
        </div>
      )}

      {/* Free tariff unavailable toast */}
      {freeTariffError && (
        <div className="toast-error">
          <i className="fas fa-clock" /> Бесплатный тариф временно недоступен
        </div>
      )}

      {/* Active order toast */}
      {activeOrderError && (
        <div className="toast-error">
          <i className="fas fa-clock" /> У вас уже есть активный заказ
        </div>
      )}

      {/* Generic order error toast */}
      {orderError && (
        <div className="toast-error">
          <i className="fas fa-exclamation-circle" /> Не удалось создать заказ. Попробуйте ещё раз
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

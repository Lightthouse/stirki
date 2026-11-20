import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { isAuthenticated } from '../api/client'
import { getMe, createOrder, getAdImages, trackAdView, getAddresses, getSystemSettings, getServices } from '../api'
import { AddressCard } from '../components/swipe/AddressCard'
import { TariffCard } from '../components/swipe/TariffCard'
import { MachinesCard } from '../components/swipe/MachinesCard'
import { ServicesCard } from '../components/swipe/ServicesCard'
import { CartMini } from '../components/CartMini'
import { CartExpanded } from '../components/CartExpanded'
import { InfoModal } from '../components/ui/InfoModal'
import { AdViewer } from '../components/AdViewer'
import { OfferModal } from '../components/ui/OfferModal'
import { PrivacyModal } from '../components/ui/PrivacyModal'
import { SupportContacts } from '../components/ui/SupportContacts'
import type { AddressData } from '../components/swipe/AddressCard'
import type { Tariff } from '../components/swipe/TariffCard'
import { addonBagPrice, buildPriceMap, toggleAddonSet } from '../components/swipe/ServicesCard'
import type { AddonItem, CartItem, OrderLimits } from '../components/swipe/ServicesCard'
import type { ClientInfo, Street, ServiceItem, Handover } from '../types'
import { acceptHoursText, EMAIL_RE } from '../types'

export function OrderPage() {
  const navigate = useNavigate()
  const swipeRef = useRef<HTMLDivElement>(null)
  const [activeCard, setActiveCard] = useState(0)

  const [_client, setClient] = useState<ClientInfo | null>(null)
  const [address, setAddress] = useState<AddressData>({
    street: '', house: '', entrance: 1, floor: 1, apartment: 1, comment: '',
  })
  const [tariff, setTariff] = useState<Tariff | null>(null)
  const [serviceType, setServiceType] = useState<'bag' | 'piece'>('bag')
  const [cart, setCart] = useState<CartItem[]>([])
  const [addons, setAddons] = useState<Set<string>>(new Set())
  const [showCart, setShowCart] = useState(false)
  const [overlayVisible, setOverlayVisible] = useState(false)
  const [loading, setLoading] = useState(false)
  const [showInfo, setShowInfo] = useState(false)

  const [hasPreviousAddress, setHasPreviousAddress] = useState(false)
  const [profileLoaded, setProfileLoaded] = useState(false)
  const [addressError, setAddressError] = useState(false)
  const [adsWatched, setAdsWatched] = useState(0)
  const [showAdViewer, setShowAdViewer] = useState(false)
  const [adImages, setAdImages] = useState<string[]>([])
  const [showOffer, setShowOffer] = useState(false)
  const [showPrivacy, setShowPrivacy] = useState(false)
  const [streets, setStreets] = useState<Street[]>([])
  const [services, setServices] = useState<ServiceItem[]>([])
  const [freeTariffAvailable, setFreeTariffAvailable] = useState(true)
  const [freeTariffError, setFreeTariffError] = useState(false)
  const [orderLimits, setOrderLimits] = useState<OrderLimits>({
    freeBagSlots: 1, freePieceSlots: 0, paidBagSlots: 5, paidPieceSlots: 1,
  })
  const [adSettings, setAdSettings] = useState({ count: 1, durationSec: 1 })
  // null — настройки ещё не загружены; строка — текст часов приёма, если сейчас заказы не принимаются
  const [closedHours, setClosedHours] = useState<string | null>(null)
  const [activeOrderError, setActiveOrderError] = useState(false)
  const [orderError, setOrderError] = useState<string | null>(null)
  // Текст ошибки создания платежа (бэкенд: PAYMENT_FAILED_DETAIL в routers/orders.py).
  // Показывается окном с контактами поддержки, а не исчезающей плашкой.
  const [paymentError, setPaymentError] = useState<string | null>(null)
  const [nextDayFromHour, setNextDayFromHour] = useState<number | null>(null)
  const [handover, setHandover] = useState<Handover | null>(null)
  const [handoverError, setHandoverError] = useState(false)
  const [promoLabel, setPromoLabel] = useState('')
  // Email для чека платного заказа: подставляется сохранённый с прошлого заказа, сохраняется при оформлении.
  const [email, setEmail] = useState('')
  const [emailError, setEmailError] = useState(false)
  // Перед каждым оформлением показываем, что не стираем: клиент мог пропустить это в «О сервисе».
  const [showNotWashed, setShowNotWashed] = useState(false)

  // Hint states per card
  const [hints, setHints] = useState({ address: false, tariff: false, machines: false })

  const showMachines = tariff === 'free'
  const prices = buildPriceMap(services)
  const minPaidPrice = Math.min(prices.piece, prices.base)
  const adsRequired = Math.max(0, Math.min(adSettings.count, adImages.length))
  const addonItems: AddonItem[] = tariff === 'free' ? [] : services
    .filter((s) => addons.has(s.slug))
    .map((s) => ({ slug: s.slug, name: s.name, price: s.price_rub, bagPrice: addonBagPrice(prices, s.slug) }))

  useEffect(() => {
    if (!isAuthenticated()) {
      navigate('/login')
      return
    }
    getMe()
      .then((c) => {
        setClient(c)
        if (c.email) setEmail(c.email)
        if (c.street) {
          setHasPreviousAddress(true)
          setAddress({
            street: c.street,
            house: c.house || '',
            entrance: c.entrance || 1,
            floor: c.floor || 1,
            apartment: c.apartment || 1,
            comment: '',
          })
        }
      })
      .catch(() => {})  // 401 обрабатывается в api/client.ts
      .finally(() => setProfileLoaded(true))
    getAdImages().then(setAdImages).catch(() => {})
    getServices().then(setServices).catch(() => {})
    getAddresses().then((res) => setStreets(res.streets)).catch(() => {})
    getSystemSettings().then((s) => {
      setFreeTariffAvailable(s.free_tariff_is_available)
      setPromoLabel(s.promo_enabled ? s.promo_label : '')
      setOrderLimits({
        freeBagSlots: s.free_bag_slots,
        freePieceSlots: s.free_piece_slots,
        paidBagSlots: s.paid_bag_slots,
        paidPieceSlots: s.paid_piece_slots,
      })
      setAdSettings({ count: s.ad_count, durationSec: s.ad_duration_sec })
      setNextDayFromHour(s.next_day_delivery_from_hour)
      if (!s.is_accepting_orders) setClosedHours(acceptHoursText(s))
    }).catch(() => {})
  }, [])

  useEffect(() => {
    // Новый пользователь без сохранённого адреса: после загрузки профиля
    // подставляем первую доступную улицу/дом (раньше это делал AddressCard,
    // что вызывало гонку с загрузкой профиля).
    if (profileLoaded && !hasPreviousAddress && streets.length > 0 && !address.street) {
      const first = streets[0]
      setAddress((a) => ({ ...a, street: first.slug, house: first.houses[0] || '' }))
    }
  }, [profileLoaded, hasPreviousAddress, streets, address.street])

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

  // Рекламные картинки грузим в фоне сразу, пока клиент выбирает адрес и тариф, —
  // к просмотру они уже в кэше браузера и показ начинается без ожидания.
  // Ссылки держим в ref, чтобы загруженные картинки не выбросил сборщик мусора.
  // Бесплатный тариф выключен — рекламу не покажут, трафик клиента не тратим.
  const adPreloadRef = useRef<HTMLImageElement[]>([])
  useEffect(() => {
    if (!freeTariffAvailable) return
    adPreloadRef.current = adImages.map((src) => {
      const img = new Image()
      img.src = src
      return img
    })
  }, [adImages, freeTariffAvailable])

  function handleWatchAd() {
    setShowAdViewer(true)
  }

  function handleAdComplete() {
    setShowAdViewer(false)
    setAdsWatched(adsRequired)
  }

  function handleTariffSelect(t: Tariff) {
    setTariff(t)
    if (t === 'free') {
      setServiceType('bag')
      setCart([])
      setAddons(new Set())
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

  function handleToggleAddon(slug: string) {
    setAddons((prev) => toggleAddonSet(prev, slug))
  }

  function handleClearCart() {
    setCart([])
  }

  function handleServiceTypeChange(type: 'bag' | 'piece') {
    setServiceType(type)
  }

  function openCart() {
    setShowCart(true)
    setOverlayVisible(true)
  }

  function closeCart() {
    setShowCart(false)
    setOverlayVisible(false)
  }

  function handleCheckout() {
    if (cart.length === 0) return
    if (!address.street || !address.house) {
      setAddressError(true)
      setTimeout(() => setAddressError(false), 3000)
      return
    }
    if (!handover) {
      setHandoverError(true)
      setTimeout(() => setHandoverError(false), 3000)
      return
    }
    const isFree = tariff === 'free'
    if (!isFree && !EMAIL_RE.test(email)) {
      setEmailError(true)
      setTimeout(() => setEmailError(false), 3000)
      return
    }
    setShowNotWashed(true)
  }

  // «Хорошо» в окне «Мы не стираем» — создаём заказ.
  async function submitOrder() {
    setShowNotWashed(false)
    const isFree = tariff === 'free'
    if (!handover) return
    const bagsInCart = cart.filter((i) => i.type === 'bag').length
    const piecesInCart = cart.filter((i) => i.type === 'piece').length
    setLoading(true)
    try {
      const result = await createOrder({
        street: address.street,
        house: address.house,
        apartment: address.apartment,
        entrance: address.entrance,
        floor: address.floor,
        bags_number: bagsInCart,
        pieces_number: piecesInCart,
        services: addonItems.map((a) => a.slug),
        comment: address.comment || undefined,
        is_free: isFree,
        handover,
        ...(!isFree && { email }),
      })

      setLoading(false)
      closeCart()

      if (result.confirmation_url) {
        window.location.href = result.confirmation_url
        return
      }

      navigate(`/order/${result.order_id}`)
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
      } else if (e instanceof Error && e.message.startsWith('Не удалось перейти к оплате')) {
        setPaymentError(e.message)
      } else {
        console.error('Ошибка создания заказа:', e)
        // Бэкенд отдаёт понятные русские тексты (часы приёма, лимит бесплатных заказов, зона
        // обслуживания); технические ошибки вида «HTTP 500» заменяем общим текстом.
        const msg = e instanceof Error && !e.message.startsWith('HTTP ') && e.message !== 'Failed to fetch'
          ? e.message
          : 'Не удалось создать заказ. Попробуйте ещё раз'
        setOrderError(msg)
        setTimeout(() => setOrderError((cur) => (cur === msg ? null : cur)), 8000)
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
          <img src="/logo.png" alt="стиркаON" />
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
          streets={streets}
          onChange={setAddress}
          onHintActivate={() => activateHint('address')}
          hintActive={hints.address}
          hasPreviousAddress={hasPreviousAddress}
        />
        <TariffCard
          minPaidPrice={minPaidPrice}
          adsRequired={adsRequired}
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
          adsRequired={adsRequired}
          onWatchAd={handleWatchAd}
          addons={addons}
          onToggleAddon={handleToggleAddon}
          addressValid={!!(address.street && address.house)}
          limits={orderLimits}
          services={services}
          promoLabel={promoLabel}
        />
      </div>

      {/* Cart mini — always visible on services card */}
      {!showCart && (
        <CartMini cart={cart} addons={addonItems} isFree={tariff === 'free'} onClick={openCart} />
      )}

      {/* Overlay */}
      <div
        className={`overlay${overlayVisible ? ' show' : ''}`}
        onClick={closeCart}
      />

      {/* Cart expanded */}
      <CartExpanded
        cart={cart}
        addons={addonItems}
        isFree={tariff === 'free'}
        show={showCart}
        onClose={closeCart}
        onRemove={handleRemoveFromCart}
        onClear={handleClearCart}
        onCheckout={handleCheckout}
        loading={loading}
        onShowOffer={() => setShowOffer(true)}
        onShowPrivacy={() => setShowPrivacy(true)}
        nextDayFromHour={nextDayFromHour}
        handover={handover}
        onHandoverChange={(h) => { setHandover(h); setHandoverError(false) }}
        handoverError={handoverError}
        email={email}
        onEmailChange={(v) => { setEmail(v); setEmailError(false) }}
        emailError={emailError}
      />

      {/* Info modal */}
      {showInfo && <InfoModal onClose={() => setShowInfo(false)} />}

      {/* Legal modals */}
      {showOffer && <OfferModal onClose={() => setShowOffer(false)} />}
      {showPrivacy && <PrivacyModal onClose={() => setShowPrivacy(false)} />}

      {/* Не выбран способ передачи вещей */}
      {handoverError && (
        <div className="toast-error" role="alert">
          <i className="fas fa-hand-pointer" /> <span>Выберите, как передать вещи</span>
        </div>
      )}

      {/* Не указан или неверный email для чека */}
      {emailError && (
        <div className="toast-error" role="alert">
          <i className="fas fa-envelope" /> <span>{email ? 'Проверьте email — на него придёт чек' : 'Укажите email для чека'}</span>
        </div>
      )}

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
        <div className="toast-error" role="alert">
          <i className="fas fa-exclamation-circle" /> <span>{orderError}</span>
          <button className="toast-close" onClick={() => setOrderError(null)} aria-label="Закрыть">
            <i className="fas fa-times" />
          </button>
        </div>
      )}

      {/* Перед оформлением: что не стираем. Клик мимо окна — отмена, заказ не создаётся. */}
      {showNotWashed && (
        <div className="modal-overlay" onClick={() => setShowNotWashed(false)}>
          <div className="modal-box" role="alertdialog" aria-labelledby="not-washed-title" onClick={(e) => e.stopPropagation()}>
            <h3 id="not-washed-title"><i className="fas fa-ban" /> Мы не стираем</h3>
            <ul className="not-washed-list">
              <li>обувь</li>
              <li>любую верхнюю одежду</li>
              <li>домашний текстиль</li>
              <li>ковры</li>
            </ul>
            <button className="status-btn" onClick={submitOrder} autoFocus>Хорошо</button>
          </div>
        </div>
      )}

      {/* Не удалось создать платёж: заказ отменён на бэкенде, операторам ушло письмо */}
      {paymentError && (
        <div className="modal-overlay" onClick={() => setPaymentError(null)}>
          <div className="modal-box" role="alertdialog" onClick={(e) => e.stopPropagation()}>
            <h3><i className="fas fa-exclamation-circle" /> Оплата не прошла</h3>
            <p>{paymentError} Мы уже получили сообщение о сбое. Попробуйте ещё раз через несколько минут или свяжитесь с нами:</p>
            <SupportContacts />
            <button className="status-btn" onClick={() => setPaymentError(null)}>Понятно</button>
          </div>
        </div>
      )}

      {/* Вне часов приёма заказов */}
      {closedHours && (
        <div className="modal-overlay">
          <div className="modal-box">
            <h3><i className="fas fa-clock" /> Сейчас заказы не принимаются</h3>
            <p>Мы принимаем заказы ежедневно {closedHours}. Будем рады видеть вас в это время!</p>
            <button className="btn-pill btn-pill-accent" onClick={() => navigate('/')}>
              На главную
            </button>
          </div>
        </div>
      )}

      {/* Ad viewer */}
      {showAdViewer && (
        <AdViewer
          images={adImages}
          count={adsRequired}
          durationSec={adSettings.durationSec}
          onComplete={handleAdComplete}
          onAdViewed={(path) => { trackAdView(path).catch(() => {}) }}
        />
      )}
    </div>
  )
}

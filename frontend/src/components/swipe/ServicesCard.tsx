import { useState } from 'react'
import type { ServiceItem } from '../../types'
import type { Tariff } from './TariffCard'

const BASE_SLUGS = new Set(['base', 'piece'])

export interface AddonItem {
  slug: string
  name: string
  /** цена за вещь */
  price: number
  /** цена за пакет (может отличаться, см. addonBagPrice) */
  bagPrice: number
}

export interface CartItem {
  type: 'bag' | 'piece'
  basePrice: number
}

/** Итог корзины: допуслуги выбираются на весь заказ и считаются за каждую позицию
 *  (за пакет — по цене пакета), как в src/services/pricing.py. */
export function calcCartTotals(cart: CartItem[], addons: AddonItem[], isFree: boolean) {
  const addonsPiece = addons.reduce((sum, a) => sum + a.price, 0)
  const addonsBag = addons.reduce((sum, a) => sum + a.bagPrice, 0)
  const fullTotal = cart.reduce(
    (sum, item) => sum + item.basePrice + (item.type === 'bag' ? addonsBag : addonsPiece),
    0,
  )
  return { fullTotal, total: isFree ? 0 : fullTotal }
}

export interface OrderLimits {
  freeBagSlots: number
  freePieceSlots: number
  paidBagSlots: number
  paidPieceSlots: number
}

function getMaxItems(tariff: Tariff | null, serviceType: 'bag' | 'piece', limits: OrderLimits): number {
  if (!tariff) return 0
  if (tariff === 'free') return serviceType === 'bag' ? limits.freeBagSlots : limits.freePieceSlots
  return serviceType === 'bag' ? limits.paidBagSlots : limits.paidPieceSlots
}

// Цены по оферте — на случай, если прайс не загрузился. Актуальные цены приходят из БД.
const FALLBACK_PRICES: Record<string, number> = {
  base: 990,
  piece: 190,
  steaming: 390,
  steaming_bag: 990,
  color_catcher_sheets: 50,
  hypoallergenic_conditioner: 80,
  laundry_net: 150,
  no_conditioner: 0,
}

// Допы, которые нельзя выбрать вместе: выбор одного снимает другой (на бэкенде — EXCLUSIVE_ADDONS в pricing.py).
const EXCLUSIVE_ADDONS: [string, string][] = [['hypoallergenic_conditioner', 'no_conditioner']]

/** Включить или выключить доп; при включении снимаются несовместимые с ним. */
export function toggleAddonSet(prev: Set<string>, slug: string): Set<string> {
  const next = new Set(prev)
  if (next.has(slug)) {
    next.delete(slug)
    return next
  }
  next.add(slug)
  for (const [a, b] of EXCLUSIVE_ADDONS) {
    if (slug === a) next.delete(b)
    if (slug === b) next.delete(a)
  }
  return next
}

// Больше стольких допов — компактный список, чтобы карточка «Что стираем» помещалась на экран телефона.
const COMPACT_DOPS_FROM = 4

// Услуга `<slug>_bag` — цена допуслуги за пакет; сама по себе не выбирается (как BAG_PRICE_SUFFIX на бэкенде).
const BAG_PRICE_SUFFIX = '_bag'

/** Доп, который выбирает клиент. `<slug>_bag` при существующем `<slug>` — цена за пакет, не отдельный доп. */
export function isAddonSlug(slug: string, allSlugs: Set<string>): boolean {
  if (BASE_SLUGS.has(slug)) return false
  return !(slug.endsWith(BAG_PRICE_SUFFIX) && allSlugs.has(slug.slice(0, -BAG_PRICE_SUFFIX.length)))
}

/** Цена допуслуги за пакет: `<slug>_bag`, если задана, иначе обычная цена. */
export function addonBagPrice(prices: Record<string, number>, slug: string): number {
  return prices[slug + BAG_PRICE_SUFFIX] ?? prices[slug] ?? 0
}

export function buildPriceMap(services: ServiceItem[]): Record<string, number> {
  const map: Record<string, number> = { ...FALLBACK_PRICES }
  for (const s of services) map[s.slug] = s.price_rub
  return map
}

interface Props {
  tariff: Tariff | null
  serviceType: 'bag' | 'piece'
  onServiceTypeChange: (type: 'bag' | 'piece') => void
  cart: CartItem[]
  onAddToCart: (item: CartItem) => void
  adsWatched: number
  adsRequired: number
  onWatchAd: () => void
  addons: Set<string>
  onToggleAddon: (slug: string) => void
  addressValid: boolean
  limits: OrderLimits
  services: ServiceItem[]
  // надпись акции рядом с зачёркнутой ценой (system_settings.promo_label)
  promoLabel: string
}

export function ServicesCard({ tariff, serviceType, onServiceTypeChange, cart, onAddToCart, adsWatched, adsRequired, onWatchAd, addons, onToggleAddon, addressValid, limits, services, promoLabel }: Props) {
  const prices = buildPriceMap(services)
  // Обычная цена при действующей акции — зачёркивается рядом с ценой по акции.
  const regularPrice = (slug: string) => services.find((s) => s.slug === slug)?.regular_price_rub ?? null
  const shownSlug = serviceType === 'piece' ? 'piece' : 'base'
  const promoRegular = regularPrice(shownSlug)
  const allSlugs = new Set(services.map((s) => s.slug))
  const availableDops = services.filter((s) => isAddonSlug(s.slug, allSlugs))

  const [added, setAdded] = useState(false)
  const [needAds, setNeedAds] = useState(false)
  const [dopHint, setDopHint] = useState(false)
  const [limitHint, setLimitHint] = useState(false)

  const isFree = tariff === 'free'
  const maxBags = getMaxItems(tariff, 'bag', limits)
  const maxPieces = getMaxItems(tariff, 'piece', limits)
  const bagsInCart = cart.filter((i) => i.type === 'bag').length
  const piecesInCart = cart.filter((i) => i.type === 'piece').length
  const canAddBag = maxBags > 0 && bagsInCart < maxBags
  const canAddPiece = maxPieces > 0 && piecesInCart < maxPieces
  const bagDisabled = !!tariff && !canAddBag
  const pieceDisabled = !!tariff && !canAddPiece
  const canAdd = serviceType === 'bag' ? canAddBag : canAddPiece

  function showLimitHint() {
    setLimitHint(true)
    setTimeout(() => setLimitHint(false), 2000)
  }

  function handleSwitchToBag() {
    if (bagDisabled) { showLimitHint(); return }
    onServiceTypeChange('bag')
  }

  function handleSwitchToPiece() {
    if (pieceDisabled) { showLimitHint(); return }
    onServiceTypeChange('piece')
  }

  function toggleAddon(key: string) {
    if (isFree) {
      setDopHint(true)
      setTimeout(() => setDopHint(false), 2000)
      return
    }
    onToggleAddon(key)
  }

  function handleAdd() {
    if (!tariff) return
    if (!canAdd) return
    if (isFree && adsWatched < adsRequired) {
      setNeedAds(true)
      setTimeout(() => setNeedAds(false), 2500)
      return
    }
    const basePrice = serviceType === 'piece' ? prices.piece : prices.base
    onAddToCart({ type: serviceType, basePrice })
    setAdded(true)
    setTimeout(() => setAdded(false), 1000)
  }

  const canSubmit = canAdd && !!tariff && addressValid

  const DOPS = availableDops.map((s) => ({
    key: s.slug,
    label: s.name,
    // показываем цену для выбранного типа: вещь или пакет
    price: serviceType === 'bag' ? addonBagPrice(prices, s.slug) : prices[s.slug],
  }))

  function getBtnLabel() {
    if (added) return 'Добавлено!'
    if (!tariff && !addressValid) return 'Укажите тариф и адрес'
    if (!tariff) return 'Выберите тариф'
    if (!addressValid) return 'Укажите адрес'
    if (!canAdd) return 'Лимит исчерпан'
    return 'Добавить в корзину'
  }

  return (
    <div className="swipe-card">
      <div className={`card-content${DOPS.length >= COMPACT_DOPS_FROM ? ' services-compact' : ''}`}>
        <div className="hero-title">Что стираем</div>

        <div className="service-switch">
          <div
            className={`switch-opt${serviceType === 'piece' ? ' active' : ''}${pieceDisabled ? ' unavailable' : ''}`}
            onClick={handleSwitchToPiece}
          >
            Вещь
          </div>
          <div
            className={`switch-opt${serviceType === 'bag' ? ' active' : ''}${bagDisabled ? ' unavailable' : ''}`}
            onClick={handleSwitchToBag}
          >
            Пакет
          </div>
        </div>

        {isFree ? (
          <div className="price-free-block">
            <span className="price-strikethrough">{regularPrice('base') ?? prices.base} ₽</span>
            <span className="price-big price-big--free">0 ₽</span>
          </div>
        ) : promoRegular !== null ? (
          <div className="price-free-block">
            <span className="price-strikethrough">{promoRegular} ₽</span>
            <span className="price-big">{prices[shownSlug]} ₽</span>
          </div>
        ) : (
          <div className="price-big">
            {prices[shownSlug]} ₽
          </div>
        )}
        <div className="price-label">
          {!isFree && promoRegular !== null && promoLabel && <span className="promo-badge">{promoLabel}</span>}
          {isFree
            ? 'бесплатная стирка пакета до 3 кг'
            : serviceType === 'piece'
              ? 'стоимость стирки одной вещи'
              : 'стоимость пакета до 3 кг'}
        </div>

        {/* На бесплатном тарифе допы не включаются — подпись про корзину там ни к чему */}
        {DOPS.length > 0 && !isFree && (
          <div className="price-label extras-label">
            допы действуют на всю корзину
          </div>
        )}
        <div className="extras">
          {DOPS.map((dop) => (
            <div
              key={dop.key}
              className={`extra-item${addons.has(dop.key) ? ' active' : ''}${isFree ? ' disabled' : ''}`}
              onClick={() => toggleAddon(dop.key)}
            >
              <div className="extra-name">{dop.label}</div>
              <div className="extra-price">+{dop.price} ₽</div>
            </div>
          ))}
        </div>

        {isFree && adsRequired > 0 && (
          <div
            className={`unlock-card${adsWatched >= adsRequired ? ' unlock-card--done' : ''}`}
            style={{ marginTop: 16 }}
            onClick={adsWatched >= adsRequired ? undefined : onWatchAd}
          >
            <span>
              <i className={`fas ${adsWatched >= adsRequired ? 'fa-check-circle' : 'fa-play-circle'}`} />
              {adsWatched >= adsRequired ? ' реклама просмотрена' : ' СМОТРЕТЬ РЕКЛАМУ'}
            </span>
            <span className="unlock-counter">{adsWatched}/{adsRequired}</span>
          </div>
        )}

        <button
          className={`add-btn${added ? ' add-success' : ''}`}
          onClick={canSubmit ? handleAdd : undefined}
          disabled={!canSubmit}
        >
          <i className={`fas ${added ? 'fa-check-circle' : 'fa-plus-circle'}`} />
          {getBtnLabel()}
        </button>

        {needAds && (
          <div className="need-ads-hint" style={{ marginTop: 12 }}>
            <i className="fas fa-play-circle" /> Просмотрите рекламу
          </div>
        )}
      </div>

      {dopHint && (
        <div className="dop-hint">
          <i className="fas fa-lock" /> Доступно только в платном тарифе
        </div>
      )}

      {limitHint && (
        <div className="dop-hint">
          <i className="fas fa-ban" /> Превышает лимиты тарифа
        </div>
      )}
    </div>
  )
}

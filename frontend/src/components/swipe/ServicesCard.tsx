import { useState } from 'react'
import type { ServiceItem } from '../../types'
import type { Tariff } from './TariffCard'

const BASE_SLUGS = new Set(['base', 'piece'])

export interface AddonItem {
  slug: string
  name: string
  price: number
}

export interface CartItem {
  type: 'bag' | 'piece'
  basePrice: number
}

/** Итог корзины: допуслуги выбираются на весь заказ и считаются за каждую позицию. */
export function calcCartTotals(cart: CartItem[], addons: AddonItem[], isFree: boolean) {
  const positionsTotal = cart.reduce((sum, item) => sum + item.basePrice, 0)
  const addonsPerPosition = addons.reduce((sum, a) => sum + a.price, 0)
  const fullTotal = positionsTotal + addonsPerPosition * cart.length
  return { fullTotal, total: isFree ? 0 : fullTotal, addonsPerPosition }
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

const FALLBACK_PRICES: Record<string, number> = {
  base: 1490,
  piece: 390,
  ironing: 190,
  conditioner: 100,
  vacuum_pack: 150,
  color_catcher_sheets: 100,
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
}

export function ServicesCard({ tariff, serviceType, onServiceTypeChange, cart, onAddToCart, adsWatched, adsRequired, onWatchAd, addons, onToggleAddon, addressValid, limits, services }: Props) {
  const prices = buildPriceMap(services)
  const availableDops = services.filter((s) => !BASE_SLUGS.has(s.slug))

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
    const basePrice = serviceType === 'piece' ? (prices.piece ?? 390) : (prices.base ?? 1490)
    onAddToCart({ type: serviceType, basePrice })
    setAdded(true)
    setTimeout(() => setAdded(false), 1000)
  }

  const canSubmit = canAdd && !!tariff && addressValid

  const DOPS = availableDops.map((s) => ({
    key: s.slug,
    label: s.name,
    price: prices[s.slug] ?? s.price_rub,
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
      <div className="card-content">
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
            <span className="price-strikethrough">{prices.base ?? 1490} ₽</span>
            <span className="price-big price-big--free">0 ₽</span>
          </div>
        ) : (
          <div className="price-big">
            {serviceType === 'piece' ? (prices.piece ?? 390) : (prices.base ?? 1490)} ₽
          </div>
        )}
        <div className="price-label">
          {isFree
            ? 'бесплатная стирка'
            : serviceType === 'piece'
              ? 'стоимость стирки одной вещи'
              : 'стоимость пакета до 3 кг'}
        </div>

        {DOPS.length > 0 && (
          <div className="price-label" style={{ marginTop: 12 }}>
            допуслуги — на весь заказ, цена за каждую позицию
          </div>
        )}
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

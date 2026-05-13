import { useEffect, useState } from 'react'
import { getServices } from '../../api'
import type { ServiceItem } from '../../types'
import type { Tariff } from './TariffCard'

export interface CartItem {
  type: 'bag' | 'piece'
  addons: string[]
  price: number
}

// piece всегда 1; bag free=1, bag paid=5
function getMaxItems(tariff: Tariff | null, serviceType: 'bag' | 'piece'): number {
  if (!tariff) return 0
  if (serviceType === 'piece') return 1
  return tariff === 'free' ? 1 : 5
}

const FALLBACK_PRICES: Record<string, number> = {
  base: 1490,
  piece: 390,
  ironing: 990,
  conditioner: 100,
  vacuum_pack: 150,
}

function buildPriceMap(services: ServiceItem[]): Record<string, number> {
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
  onWatchAd: () => void
  addressValid: boolean
}

export function ServicesCard({ tariff, serviceType, onServiceTypeChange, cart, onAddToCart, adsWatched, onWatchAd, addressValid }: Props) {
  const [prices, setPrices] = useState<Record<string, number>>(FALLBACK_PRICES)
  const [addons, setAddons] = useState<Set<string>>(new Set())
  const [added, setAdded] = useState(false)
  const [needAds, setNeedAds] = useState(false)
  const [dopHint, setDopHint] = useState(false)

  useEffect(() => {
    getServices().then((services) => setPrices(buildPriceMap(services)))
  }, [])

  const isFree = tariff === 'free'
  const maxItems = getMaxItems(tariff, serviceType)
  const canAdd = cart.length < maxItems

  function toggleAddon(key: string) {
    if (isFree) {
      setDopHint(true)
      setTimeout(() => setDopHint(false), 2000)
      return
    }
    setAddons((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  function calcPrice(): number {
    let price = serviceType === 'piece' ? (prices.piece ?? 390) : (prices.base ?? 1490)
    if (addons.has('conditioner')) price += prices.conditioner ?? 0
    if (addons.has('vacuum_pack')) price += prices.vacuum_pack ?? 0
    if (addons.has('ironing')) price += prices.ironing ?? 0
    return price
  }

  function handleAdd() {
    if (!tariff) return
    if (!canAdd) return
    if (isFree && adsWatched < 3) {
      setNeedAds(true)
      setTimeout(() => setNeedAds(false), 2500)
      return
    }
    const price = isFree ? 0 : calcPrice()
    onAddToCart({ type: isFree ? 'bag' : serviceType, addons: isFree ? [] : Array.from(addons), price })
    setAddons(new Set())
    setAdded(true)
    setTimeout(() => setAdded(false), 1000)
  }

  const canSubmit = canAdd && !!tariff && addressValid

  const DOPS = [
    { key: 'conditioner', label: 'Кондиционер', price: prices.conditioner ?? 100 },
    { key: 'vacuum_pack', label: 'Вакуумная упаковка', price: prices.vacuum_pack ?? 150 },
    { key: 'ironing', label: 'Глажка', price: prices.ironing ?? 990 },
  ]

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
            className={`switch-opt${serviceType === 'piece' && !isFree ? ' active' : ''}`}
            onClick={() => !isFree && onServiceTypeChange('piece')}
            style={isFree ? { opacity: 0.4, pointerEvents: 'none' } : {}}
          >
            Вещь
          </div>
          <div
            className={`switch-opt${serviceType === 'bag' || isFree ? ' active' : ''}`}
            onClick={() => onServiceTypeChange('bag')}
          >
            Пакет
          </div>
        </div>

        <div className="price-big">
          {isFree
            ? '0 ₽'
            : `${serviceType === 'piece' ? (prices.piece ?? 390) : (prices.base ?? 1490)} ₽`}
        </div>
        <div className="price-label">
          {isFree
            ? 'бесплатная стирка'
            : serviceType === 'piece'
              ? 'стоимость стирки одной вещи'
              : 'стоимость пакета до 3 кг'}
        </div>

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

        {isFree && (
          <div
            className={`ad-block${adsWatched >= 3 ? ' ad-block--done' : ''}`}
            style={{ marginTop: 16 }}
            onClick={adsWatched >= 3 ? undefined : onWatchAd}
          >
            <span>
              <i className={`fas ${adsWatched >= 3 ? 'fa-check-circle' : 'fa-play-circle'}`} />
              {adsWatched >= 3 ? ' реклама просмотрена' : ' СМОТРЕТЬ РЕКЛАМУ'}
            </span>
            <span className="ad-counter">{adsWatched}/3</span>
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
    </div>
  )
}

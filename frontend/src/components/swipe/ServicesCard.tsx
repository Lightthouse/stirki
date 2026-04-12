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
  base: 890,
  piece: 190,
  ironing: 990,
  conditioner: 50,
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
      setTimeout(() => setDopHint(false), 2500)
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
    let price = serviceType === 'piece' ? (prices.piece ?? 190) : (prices.base ?? 890)
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

  const ironingPrice = prices.ironing ?? 990

  return (
    <div className="swipe-card">
      <div className="card-content">
        <div className="service-panel">
          <div className="service-selector">
            <span
              className={`service-option${serviceType === 'piece' && !isFree ? ' active' : ''}`}
              onClick={() => !isFree && onServiceTypeChange('piece')}
              style={isFree ? { opacity: 0.4, pointerEvents: 'none' } : {}}
            >
              <i className="fas fa-tshirt" /> вещь
            </span>
            <span
              className={`service-option${serviceType === 'bag' || isFree ? ' active' : ''}`}
              onClick={() => onServiceTypeChange('bag')}
            >
              <i className="fas fa-shopping-bag" /> пакет
            </span>
          </div>

          <div className="service-display">
            <div className="service-emoji">
              {isFree ? '🛍️' : serviceType === 'piece' ? '👕' : '🛍️'}
            </div>
            <div className="service-name">
              {isFree ? 'Пакет' : serviceType === 'piece' ? 'Вещь' : 'Пакет'}
            </div>
            <div className="service-price">
              {isFree ? (
                <>
                  <span style={{ textDecoration: 'line-through', opacity: 0.5, fontSize: 22 }}>{prices.base ?? 890} ₽</span>
                  {' '}0 ₽
                </>
              ) : (
                `${serviceType === 'piece' ? (prices.piece ?? 190) : (prices.base ?? 890)} ₽`
              )}
            </div>
          </div>

          <div className="dops-row">
            {[
              { key: 'conditioner', label: `кондиционер +${prices.conditioner ?? 0}` },
              { key: 'vacuum_pack', label: `вакуум +${prices.vacuum_pack ?? 0}` },
              { key: 'ironing', label: `глажка +${ironingPrice}` },
            ].map((dop) => (
              <span
                key={dop.key}
                className={`dop-tag${addons.has(dop.key) ? ' active' : ''}${isFree ? ' disabled' : ''}`}
                onClick={() => toggleAddon(dop.key)}
              >
                {dop.label}
              </span>
            ))}
          </div>

          {dopHint && (
            <div className="dop-hint">
              <i className="fas fa-lock" /> Допуслуги доступны только в платном тарифе
            </div>
          )}

          {isFree && (
            <div
              className={`ad-block${adsWatched >= 3 ? ' ad-block--done' : ''}`}
              onClick={adsWatched >= 3 ? undefined : onWatchAd}
            >
              <span>
                <i className={`fas ${adsWatched >= 3 ? 'fa-check-circle' : 'fa-play-circle'}`} />
                {adsWatched >= 3 ? ' реклама просмотрена' : ' СМОТРЕТЬ РЕКЛАМУ'}
              </span>
              <span className="ad-counter">{adsWatched}/3</span>
            </div>
          )}

          <div
            className="add-to-cart-btn"
            onClick={canAdd && tariff && addressValid ? handleAdd : undefined}
            style={!canAdd || !tariff || !addressValid ? { opacity: 0.4, cursor: 'default' } : {}}
          >
            <i className={`${added ? 'fas' : 'far'} fa-heart`} />
            {added ? 'добавлено'
              : !tariff && !addressValid ? 'укажите тариф и адрес'
              : !tariff ? 'выберите тариф'
              : !addressValid ? 'укажите адрес'
              : !canAdd ? 'лимит исчерпан'
              : 'добавить в корзину'}
          </div>
          {needAds && (
            <div className="need-ads-hint">
              <i className="fas fa-play-circle" /> Просмотрите рекламу
            </div>
          )}
        </div>

        <div className="progress-dots">
          <span className="dot" />
          <span className="dot" />
          <span className="dot" />
          <span className="dot active" />
        </div>
      </div>
    </div>
  )
}

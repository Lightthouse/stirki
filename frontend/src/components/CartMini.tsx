import { useEffect, useRef, useState } from 'react'
import { calcCartTotals } from './swipe/ServicesCard'
import type { AddonItem, CartItem } from './swipe/ServicesCard'

interface Props {
  cart: CartItem[]
  addons: AddonItem[]
  isFree: boolean
  onClick: () => void
}

export function CartMini({ cart, addons, isFree, onClick }: Props) {
  const { total, fullTotal } = calcCartTotals(cart, addons, isFree)

  // Плашка вздрагивает, когда в корзину что-то добавили, — чтобы клиент заметил, что её можно открыть.
  const [shaking, setShaking] = useState(false)
  const prevCount = useRef(cart.length)
  useEffect(() => {
    if (cart.length > prevCount.current) setShaking(true)
    prevCount.current = cart.length
  }, [cart.length])

  return (
    <div
      className={`cart-mini${shaking ? ' cart-mini--shake' : ''}`}
      onClick={onClick}
      onAnimationEnd={() => setShaking(false)}
    >
      <div className="cart-mini-left">
        <i className="fas fa-receipt" />
        <div className="cart-mini-price-block">
          {isFree && cart.length > 0 && (
            <span className="cart-mini-strikethrough">{fullTotal} ₽</span>
          )}
          <span className="cart-mini-total">{total} ₽</span>
        </div>
      </div>
      <div className="cart-mini-badge">от 15 мин</div>
    </div>
  )
}

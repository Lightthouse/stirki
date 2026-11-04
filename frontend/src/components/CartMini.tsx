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

  return (
    <div className="cart-mini" onClick={onClick}>
      <div className="cart-mini-left">
        <i className="fas fa-receipt" />
        <div className="cart-mini-price-block">
          {isFree && cart.length > 0 && (
            <span className="cart-mini-strikethrough">{fullTotal} ₽</span>
          )}
          <span className="cart-mini-total">{total} ₽</span>
        </div>
      </div>
      <div className="cart-mini-count">{cart.length}</div>
    </div>
  )
}

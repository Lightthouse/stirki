import type { CartItem } from './swipe/ServicesCard'

interface Props {
  cart: CartItem[]
  isFree: boolean
  onClick: () => void
}

export function CartMini({ cart, isFree, onClick }: Props) {
  const total = cart.reduce((sum, item) => sum + item.price, 0)
  const fullTotal = cart.reduce(
    (sum, item) => sum + item.basePrice + item.addons.reduce((s, a) => s + a.price, 0),
    0,
  )

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

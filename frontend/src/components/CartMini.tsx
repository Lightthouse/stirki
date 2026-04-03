import type { CartItem } from './swipe/ServicesCard'

interface Props {
  cart: CartItem[]
  onClick: () => void
}

export function CartMini({ cart, onClick }: Props) {
  const total = cart.reduce((sum, item) => sum + item.price, 0)

  return (
    <div className="cart-mini" onClick={onClick}>
      <div className="cart-mini-left">
        <i className="fas fa-shopping-bag" />
        <span className="cart-mini-total">{total} ₽</span>
      </div>
      <div className="cart-mini-count">{cart.length}</div>
    </div>
  )
}

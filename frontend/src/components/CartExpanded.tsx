import { calcCartTotals } from './swipe/ServicesCard'
import type { AddonItem, CartItem } from './swipe/ServicesCard'

interface Props {
  cart: CartItem[]
  addons: AddonItem[]
  isFree: boolean
  show: boolean
  onClose: () => void
  onRemove: (idx: number) => void
  onClear: () => void
  onCheckout: () => void
  loading: boolean
  onShowOffer: () => void
  onShowPrivacy: () => void
}

export function CartExpanded({ cart, addons, isFree, show, onClose, onRemove, onClear, onCheckout, loading, onShowOffer, onShowPrivacy }: Props) {
  const { total, fullTotal } = calcCartTotals(cart, addons, isFree)
  const bags = cart.filter((i) => i.type === 'bag').length
  const pieces = cart.length - bags

  return (
    <div className={`cart-expanded${show ? ' show' : ''}`}>
      <div className="cart-header">
        <h3><i className="fas fa-receipt" /> корзина</h3>
        <i className="fas fa-times close-cart" onClick={onClose} />
      </div>

      {cart.length === 0 ? (
        <div className="cart-empty">
          <i className="fas fa-receipt" style={{ fontSize: 32, marginBottom: 8 }} />
          <br />
          Корзина пуста
        </div>
      ) : (
        cart.map((item, idx) => (
          <div key={idx} className="cart-item">
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600 }}>
                <i className={item.type === 'piece' ? 'fas fa-tshirt' : 'fas fa-box-open'} />
                {' '}{item.type === 'piece' ? 'Вещь' : 'Пакет'}
              </div>
              <div className="cart-item-detail">
                базовая стоимость:{' '}
                {isFree
                  ? <><s>{item.basePrice} ₽</s> 0 ₽</>
                  : `${item.basePrice} ₽`}
              </div>
            </div>
            <div className="cart-item-right">
              <span className="cart-item-price">
                {isFree ? '0 ₽' : `${item.basePrice} ₽`}
              </span>
              <button className="remove-item-btn" onClick={() => onRemove(idx)}>
                <i className="fas fa-trash-alt" />
              </button>
            </div>
          </div>
        ))
      )}

      {cart.length > 0 && addons.map((a) => (
        <div key={a.slug} className="cart-item">
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 600 }}>
              <i className="fas fa-plus-circle" /> {a.name}
            </div>
            <div className="cart-item-detail">
              {a.price === a.bagPrice
                ? `${a.price} ₽ × ${cart.length} поз.`
                : [pieces > 0 && `${a.price} ₽ × ${pieces} вещ.`, bags > 0 && `${a.bagPrice} ₽ × ${bags} пак.`]
                    .filter(Boolean).join(' + ')}
            </div>
          </div>
          <div className="cart-item-right">
            <span className="cart-item-price">{a.price * pieces + a.bagPrice * bags} ₽</span>
          </div>
        </div>
      ))}

      <div className="cart-total">
        <span>Итого</span>
        <div className="cart-total-right">
          {isFree && cart.length > 0 && (
            <span className="cart-total-strikethrough">{fullTotal} ₽</span>
          )}
          <span className="cart-total-amount">{total} ₽</span>
        </div>
      </div>

      {cart.length > 0 && (
        <div className="legal-text">
          Нажимая «Оформить заказ», вы принимаете{' '}
          <a onClick={onShowOffer} style={{ cursor: 'pointer' }}>условия публичной оферты</a>, соглашаетесь на{' '}
          <a onClick={onShowPrivacy} style={{ cursor: 'pointer' }}>обработку персональных данных</a>.
        </div>
      )}

      <button className="clear-cart-btn" onClick={onClear} disabled={cart.length === 0}>
        <i className="fas fa-trash-alt" /> Очистить корзину
      </button>
      <button
        className="checkout-btn"
        disabled={cart.length === 0 || loading}
        onClick={onCheckout}
      >
        {loading ? (
          'Создание заказа...'
        ) : (
          <><i className="fas fa-check-circle" /> Оформить заказ</>
        )}
      </button>
    </div>
  )
}

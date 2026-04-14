import type { CartItem } from './swipe/ServicesCard'

interface Props {
  cart: CartItem[]
  show: boolean
  onClose: () => void
  onRemove: (idx: number) => void
  onClear: () => void
  onCheckout: (paymentMethod: string) => void
  loading: boolean
  onShowOffer: () => void
  onShowPrivacy: () => void
}

const ADDON_NAMES: Record<string, string> = {
  conditioner: 'кондиционер',
  vacuum: 'вакуум',
  ironing: 'глажка',
}

export function CartExpanded({ cart, show, onClose, onRemove, onClear, onCheckout, loading, onShowOffer, onShowPrivacy }: Props) {
  const total = cart.reduce((sum, item) => sum + item.price, 0)

  function getAddonLabel(addons: string[]) {
    return addons.map((k) => ADDON_NAMES[k] || k).join(', ')
  }

  return (
    <div className={`cart-expanded${show ? ' show' : ''}`}>
      <div className="cart-header">
        <h3><i className="fas fa-shopping-cart" /> корзина</h3>
        <i className="fas fa-times close-cart" onClick={onClose} />
      </div>

      {cart.length === 0 ? (
        <div className="cart-empty">
          <i className="fas fa-shopping-cart" style={{ fontSize: 32, marginBottom: 8 }} />
          <br />
          Корзина пуста
        </div>
      ) : (
        <>
          {cart.map((item, idx) => (
            <div key={idx} className="cart-item">
              <div>
                <div>
                  <i className={item.type === 'piece' ? 'fas fa-tshirt' : 'fas fa-shopping-bag'} />
                  {' '}{item.type === 'piece' ? 'Вещь' : 'Пакет'}
                  {item.addons.length > 0 && ` + ${getAddonLabel(item.addons)}`}
                </div>
                {item.addons.length > 0 && (
                  <div className="cart-item-detail">= {item.price} ₽</div>
                )}
              </div>
              <div className="cart-item-right">
                <span className="cart-item-price">{item.price} ₽</span>
                <button className="remove-item-btn" onClick={() => onRemove(idx)}>
                  <i className="fas fa-trash-alt" />
                </button>
              </div>
            </div>
          ))}

          <div className="cart-total">
            <span>Итого</span>
            <span className="cart-total-amount">{total} ₽</span>
          </div>

          <div className="payment-options">
            <div className="payment-title"><i className="fas fa-credit-card" /> Способ оплаты</div>
            <label className="payment-option">
              <input type="radio" name="payment" value="card" defaultChecked />
              <span><i className="fab fa-cc-visa" /> Банковская карта</span>
            </label>
            <label className="payment-option">
              <input type="radio" name="payment" value="sbp" />
              <span><i className="fas fa-qrcode" /> QR-код (СБП)</span>
            </label>
            <label className="payment-option">
              <input type="radio" name="payment" value="tpay" />
              <span><i className="fas fa-mobile-alt" /> T‑Pay</span>
            </label>
          </div>

          <div className="legal-text">
            Нажимая «Оформить заказ», вы принимаете{' '}
            <a onClick={onShowOffer} style={{ cursor: 'pointer' }}>условия публичной оферты</a>, соглашаетесь на{' '}
            <a onClick={onShowPrivacy} style={{ cursor: 'pointer' }}>обработку персональных данных</a>.
          </div>
        </>
      )}

      <button className="clear-cart-btn" onClick={onClear} disabled={cart.length === 0}>
        <i className="fas fa-trash-alt" /> Очистить корзину
      </button>
      <button
        className="checkout-btn"
        disabled={cart.length === 0 || loading}
        onClick={() => {
          const checked = document.querySelector<HTMLInputElement>('input[name="payment"]:checked')
          onCheckout(checked?.value || 'card')
        }}
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

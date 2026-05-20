import type { CartItem } from './swipe/ServicesCard'

interface Props {
  cart: CartItem[]
  isFree: boolean
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
  vacuum_pack: 'вакуумный пакет',
  ironing: 'глажка',
  color_catcher_sheets: 'салфетки против окрашивания',
}

const ADDON_PRICES_DISPLAY: Record<string, string> = {
  conditioner: '+100 ₽',
  vacuum_pack: '+150 ₽',
  ironing: '+990 ₽',
  color_catcher_sheets: '+100 ₽',
}

export function CartExpanded({ cart, isFree, show, onClose, onRemove, onClear, onCheckout, loading, onShowOffer, onShowPrivacy }: Props) {
  const total = cart.reduce((sum, item) => sum + item.price, 0)
  const fullTotal = cart.reduce((sum, item) => sum + item.basePrice + item.addons.reduce((_s, _k) => _s, 0), 0)

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
        cart.map((item, idx) => {
          return (
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
                {item.addons.length > 0 && (
                  <div className="cart-item-detail">
                    {item.addons.map((k) => `${ADDON_NAMES[k] || k} ${ADDON_PRICES_DISPLAY[k] || ''}`).join(' · ')}
                  </div>
                )}
              </div>
              <div className="cart-item-right">
                <span className="cart-item-price">
                  {isFree ? '0 ₽' : `${item.price} ₽`}
                </span>
                <button className="remove-item-btn" onClick={() => onRemove(idx)}>
                  <i className="fas fa-trash-alt" />
                </button>
              </div>
            </div>
          )
        })
      )}

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

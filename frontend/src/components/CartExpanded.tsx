import { useEffect, useRef } from 'react'
import { calcCartTotals } from './swipe/ServicesCard'
import type { AddonItem, CartItem } from './swipe/ServicesCard'
import { HANDOVER_LABELS, mskHour } from '../types'
import type { Handover } from '../types'

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
  // час (МСК), с которого заказ возвращают на следующий день; null — настройки не загружены
  nextDayFromHour: number | null
  // способ передачи вещей; null — клиент ещё не выбрал (выбор обязателен)
  handover: Handover | null
  onHandoverChange: (h: Handover) => void
  // подсветить блок выбора: пытались оформить заказ без выбора
  handoverError: boolean
  // email для кассового чека (только платный тариф); подставлен из прошлого заказа
  email: string
  onEmailChange: (email: string) => void
  // подсветить поле: пытались оформить заказ без корректного email
  emailError: boolean
}

export function CartExpanded({ cart, addons, isFree, show, onClose, onRemove, onClear, onCheckout, loading, onShowOffer, onShowPrivacy, nextDayFromHour, handover, onHandoverChange, handoverError, email, onEmailChange, emailError }: Props) {
  // Считаем в момент показа: страница может быть открыта с 18:50, а заказ оформляют в 19:05.
  const nextDay = nextDayFromHour !== null && mskHour() >= nextDayFromHour
  const handoverRef = useRef<HTMLDivElement>(null)
  const emailRef = useRef<HTMLDivElement>(null)

  // Нажали «Оформить» без выбора — показываем блок выбора, даже если он прокручен за край корзины.
  useEffect(() => {
    if (handoverError) handoverRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, [handoverError])
  useEffect(() => {
    if (emailError) emailRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, [emailError])
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
        <div ref={handoverRef} className={`handover-choice${handoverError ? ' handover-choice--error' : ''}`} role="radiogroup" aria-label="Как передать вещи">
          <div className="handover-title">Как передать вещи</div>
          {(Object.keys(HANDOVER_LABELS) as Handover[]).map((h) => (
            <label key={h} className={`handover-option${handover === h ? ' selected' : ''}`}>
              <input type="radio" name="handover" value={h} checked={handover === h} onChange={() => onHandoverChange(h)} />
              <i className={`fas ${h === 'door' ? 'fa-door-closed' : 'fa-hand-holding'}`} />
              <span>{HANDOVER_LABELS[h]}</span>
            </label>
          ))}
        </div>
      )}

      {cart.length > 0 && !isFree && (
        <div ref={emailRef} className={`handover-choice${emailError ? ' handover-choice--error' : ''}`}>
          <label className="handover-title" htmlFor="receipt-email">Email для чеков</label>
          <input
            id="receipt-email"
            className="cart-email-input"
            type="email"
            inputMode="email"
            autoComplete="email"
            placeholder="mail@example.ru"
            value={email}
            onChange={(e) => onEmailChange(e.target.value.trim())}
          />
          <div className="cart-email-hint">Сюда придёт кассовый чек об оплате</div>
        </div>
      )}

      {cart.length > 0 && nextDay && (
        <div className="cart-note">
          <i className="fas fa-moon" />
          <span>
            Заказы после {nextDayFromHour}:00 курьер заберёт сразу, а чистые вещи вернёт завтра.
            Нужно к определённому времени — укажите его в комментарии к адресу.
          </span>
        </div>
      )}

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

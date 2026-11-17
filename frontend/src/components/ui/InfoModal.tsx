import { useEffect, useState } from 'react'
import { getServices, getSystemSettings } from '../../api'
import type { ServiceItem, SystemSettings } from '../../types'
import { acceptHoursText } from '../../types'
import { isAddonSlug } from '../swipe/ServicesCard'
import { SupportContacts } from './SupportContacts'

interface Props {
  onClose: () => void
}

export function InfoModal({ onClose }: Props) {
  const [services, setServices] = useState<ServiceItem[]>([])
  const [settings, setSettings] = useState<SystemSettings | null>(null)

  useEffect(() => {
    getServices().then(setServices).catch(() => {})
    getSystemSettings().then(setSettings).catch(() => {})
  }, [])

  const base = services.find((s) => s.slug === 'base')
  const piece = services.find((s) => s.slug === 'piece')
  const addons = services.filter((s) => isAddonSlug(s.slug))
  const bagPrice = (slug: string) => services.find((s) => s.slug === `${slug}_bag`)?.price_rub

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()}>
        <h3><i className="fas fa-star" /> о стиркаОН</h3>

        <section>
          <h4>Как работаем</h4>
          <ul>
            <li>Забираем у двери в любом стандартном продуктовом пакете (25×40 см)</li>
            <li>Стираем, сушим и гладим</li>
            <li>Возвращаем упакованные вещи к двери или в руки</li>
          </ul>
        </section>

        <section>
          <h4>Важно</h4>
          <ul>
            <li>Каждый этап виден в приложении</li>
            <li>Индивидуально — в барабане только ваши вещи</li>
            <li>Бережная стирка — до 30°C, отжим до 800 об/мин</li>
            <li>По цветам не делим — один пакет = один цвет</li>
          </ul>
        </section>

        <section>
          <h4>Тарифы</h4>
          <ul>
            {base && <li>Пакет одежды или белья (до 3 кг) — {base.price_rub} ₽</li>}
            {piece && <li>Одна вещь — {piece.price_rub} ₽</li>}
            {addons.map((a) => (
              <li key={a.slug}>
                {a.name} — {bagPrice(a.slug) !== undefined && bagPrice(a.slug) !== a.price_rub
                  ? `+${a.price_rub} ₽ за вещь / +${bagPrice(a.slug)} ₽ за пакет`
                  : `+${a.price_rub} ₽ за позицию`}
              </li>
            ))}
          </ul>
        </section>

        <section>
          <h4>Дополнительно</h4>
          <ul>
            <li>Локация — Мытищи</li>
            {settings && <li>Приём заказов — ежедневно {acceptHoursText(settings)}</li>}
            {settings && settings.next_day_delivery_from_hour < settings.order_accept_to_hour && (
              <li>
                Заказы после {settings.next_day_delivery_from_hour}:00 забираем сразу, а возвращаем на следующий день.
                Нужно к определённому времени — укажите его в комментарии к заказу
              </li>
            )}
          </ul>
        </section>

        <section>
          <h4>Поддержка</h4>
          <SupportContacts />
        </section>

        <button className="btn-pill btn-pill-accent" onClick={onClose}>
          Понятно
        </button>
      </div>
    </div>
  )
}

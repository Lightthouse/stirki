import { useEffect, useState } from 'react'
import { getSystemSettings } from '../../api'
import type { SystemSettings } from '../../types'

type Contacts = Pick<SystemSettings, 'support_phone' | 'support_telegram' | 'support_email'>

// Контакты меняются в админке («Системные настройки»); за открытие страницы грузим их один раз.
let contactsPromise: Promise<Contacts> | null = null

function loadContacts(): Promise<Contacts> {
  if (!contactsPromise) {
    contactsPromise = getSystemSettings().catch((e) => {
      contactsPromise = null // не запоминаем ошибку — попробуем снова при следующем показе
      throw e
    })
  }
  return contactsPromise
}

/** Контакты поддержки: телефон, Telegram, email. Пустой в админке контакт не показывается. */
export function SupportContacts() {
  const [contacts, setContacts] = useState<Contacts | null>(null)

  useEffect(() => {
    loadContacts().then(setContacts).catch(() => {})
  }, [])

  if (!contacts) return null
  const { support_phone: phone, support_telegram: telegram, support_email: email } = contacts

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, margin: '20px 0' }}>
      {phone && (
        <a href={`tel:${phone.replace(/[^+\d]/g, '')}`} className="support-contact-link">
          <i className="fas fa-phone" /> {phone}
        </a>
      )}
      {telegram && (
        <a href={`https://t.me/${telegram}`} target="_blank" rel="noreferrer" className="support-contact-link">
          <i className="fab fa-telegram" /> @{telegram}
        </a>
      )}
      {email && (
        <a href={`mailto:${email}`} className="support-contact-link">
          <i className="fas fa-envelope" /> {email}
        </a>
      )}
    </div>
  )
}

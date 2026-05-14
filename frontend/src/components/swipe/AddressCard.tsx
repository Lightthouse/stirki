import { useEffect, useState } from 'react'
import { getAddresses } from '../../api'
import type { Street } from '../../types'

export interface AddressData {
  street: string
  house: string
  entrance: number
  apartment: number
  comment: string
}

interface Props {
  data: AddressData
  onChange: (data: AddressData) => void
  onHintActivate: () => void
  hintActive: boolean
  hasPreviousAddress?: boolean
}

export function AddressCard({ data, onChange, onHintActivate, hintActive, hasPreviousAddress }: Props) {
  const [streets, setStreets] = useState<Street[]>([])
  const [houses, setHouses] = useState<string[]>([])

  useEffect(() => {
    getAddresses().then((res) => setStreets(res.streets))
  }, [])

  useEffect(() => {
    if (streets.length > 0 && !data.street) {
      const first = streets[0]
      onChange({ ...data, street: first.slug, house: first.houses[0] || '' })
    }
  }, [streets])

  useEffect(() => {
    const found = streets.find((s) => s.slug === data.street)
    setHouses(found?.houses || [])
    if (found && found.houses.length > 0 && !data.house) {
      onChange({ ...data, house: found.houses[0] })
    }
  }, [data.street, streets])

  function update(field: keyof AddressData, value: string | number) {
    onChange({ ...data, [field]: value })
    onHintActivate()
  }

  return (
    <div className="swipe-card">
      <div className="card-content">
        <div className="form-card">
          <h3 style={{ color: '#4F9DA7', marginBottom: hasPreviousAddress ? 4 : 16, fontSize: 16 }}>
            <i className="fas fa-map-marker-alt" /> адрес доставки
          </h3>
          {hasPreviousAddress && (
            <div className="address-prefilled-hint">
              <i className="fas fa-history" /> подставлен адрес с прошлого заказа
            </div>
          )}

          <div className="input-field">
            <i className="fas fa-street-view" />
            <select
              value={data.street}
              onChange={(e) => update('street', e.target.value)}
            >
              {streets.map((s) => (
                <option key={s.slug} value={s.slug}>{s.name}</option>
              ))}
            </select>
          </div>

          <div className="address-inline-group">
            <div className="address-inline-item">
              <span className="address-inline-label">Дом</span>
              <div className="input-field address-inline-field">
                <select
                  value={data.house}
                  onChange={(e) => update('house', e.target.value)}
                >
                  {houses.map((h) => (
                    <option key={h} value={h}>{h}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="address-inline-item">
              <span className="address-inline-label">Подъезд</span>
              <div className="input-field address-inline-field">
                <select
                  value={data.entrance}
                  onChange={(e) => update('entrance', Number(e.target.value))}
                >
                  {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((n) => (
                    <option key={n} value={n}>{n}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="address-inline-item">
              <span className="address-inline-label">Кв.</span>
              <div className="input-field address-inline-field">
                <select
                  value={data.apartment}
                  onChange={(e) => update('apartment', Number(e.target.value))}
                >
                  {Array.from({ length: 1000 }, (_, i) => i + 1).map((n) => (
                    <option key={n} value={n}>{n}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div className="input-field">
            <i className="fas fa-comment" />
            <input
              type="text"
              placeholder="Комментарий для курьера"
              value={data.comment}
              onChange={(e) => update('comment', e.target.value)}
            />
          </div>
        </div>

        <div className={`swipe-hint${hintActive ? ' active' : ''}`}>
          <i className="fas fa-chevron-up" /> потяните вверх <i className="fas fa-chevron-up" />
        </div>
      </div>
    </div>
  )
}

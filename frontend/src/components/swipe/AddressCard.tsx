import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { getAddresses } from '../../api'
import type { Street } from '../../types'

export interface AddressData {
  street: string
  house: string
  entrance: number
  floor: number
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

interface SheetConfig {
  title: string
  options: Array<{ label: string; value: string | number }>
  field: keyof AddressData
}

function BottomSheet({
  config,
  current,
  onSelect,
  onClose,
}: {
  config: SheetConfig
  current: string | number
  onSelect: (field: keyof AddressData, value: string | number) => void
  onClose: () => void
}) {
  const portal = document.querySelector('.app') ?? document.body

  return createPortal(
    <div className="addr-overlay" onClick={onClose}>
      <div className="addr-sheet" onClick={(e) => e.stopPropagation()}>
        <div className="addr-sheet-handle" />
        <div className="addr-sheet-title">{config.title}</div>
        <div className="addr-sheet-list">
          {config.options.map((opt) => (
            <div
              key={opt.value}
              className={`addr-sheet-option${opt.value === current ? ' selected' : ''}`}
              onClick={() => { onSelect(config.field, opt.value); onClose() }}
            >
              {opt.label}
            </div>
          ))}
        </div>
        <button className="addr-sheet-close" onClick={onClose}>Закрыть</button>
      </div>
    </div>,
    portal,
  )
}

export function AddressCard({ data, onChange, onHintActivate, hintActive, hasPreviousAddress }: Props) {
  const [streets, setStreets] = useState<Street[]>([])
  const [houses, setHouses] = useState<string[]>([])
  const [sheet, setSheet] = useState<SheetConfig | null>(null)

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
    if (found && found.houses.length > 0 && (!data.house || !found.houses.includes(data.house))) {
      onChange({ ...data, house: found.houses[0] })
    }
  }, [data.street, streets])

  function update(field: keyof AddressData, value: string | number) {
    onChange({ ...data, [field]: value })
    onHintActivate()
  }

  function openStreetSheet() {
    setSheet({
      title: 'Улица',
      options: streets.map((s) => ({ label: s.name, value: s.slug })),
      field: 'street',
    })
  }

  function openHouseSheet() {
    setSheet({
      title: 'Дом',
      options: houses.map((h) => ({ label: h, value: h })),
      field: 'house',
    })
  }

  function openNumSheet(field: 'entrance' | 'floor' | 'apartment', title: string, max: number) {
    setSheet({
      title,
      options: Array.from({ length: max }, (_, i) => ({ label: String(i + 1), value: i + 1 })),
      field,
    })
  }

  const streetName = streets.find((s) => s.slug === data.street)?.name ?? data.street

  return (
    <div className="swipe-card">
      <div className="card-content">
        <div className="form-card">
          <div className="card-subtitle">ВАШ АДРЕС:</div>
          {hasPreviousAddress && (
            <div className="address-prefilled-hint">
              <i className="fas fa-history" /> подставлен адрес с прошлого заказа
            </div>
          )}

          <div className="address-field-plain">
            <span className="address-field-label">Улица</span>
            <div className="addr-picker" onClick={openStreetSheet}>
              <span className="addr-picker-value">{streetName || '—'}</span>
              <i className="fas fa-chevron-down addr-picker-chevron" />
            </div>
          </div>

          <div className="address-inline-group address-inline-group--4">
            <div className="address-inline-item">
              <span className="address-inline-label">Дом</span>
              <div className="addr-picker addr-picker-sm" onClick={openHouseSheet}>
                <span className="addr-picker-value">{data.house || '—'}</span>
                <i className="fas fa-chevron-down addr-picker-chevron" />
              </div>
            </div>
            <div className="address-inline-item">
              <span className="address-inline-label">Подъезд</span>
              <div className="addr-picker addr-picker-sm" onClick={() => openNumSheet('entrance', 'Подъезд', 9)}>
                <span className="addr-picker-value">{data.entrance}</span>
                <i className="fas fa-chevron-down addr-picker-chevron" />
              </div>
            </div>
            <div className="address-inline-item">
              <span className="address-inline-label">Этаж</span>
              <div className="addr-picker addr-picker-sm" onClick={() => openNumSheet('floor', 'Этаж', 30)}>
                <span className="addr-picker-value">{data.floor}</span>
                <i className="fas fa-chevron-down addr-picker-chevron" />
              </div>
            </div>
            <div className="address-inline-item">
              <span className="address-inline-label">Кв.</span>
              <div className="addr-picker addr-picker-sm" onClick={() => openNumSheet('apartment', 'Квартира', 1000)}>
                <span className="addr-picker-value">{data.apartment}</span>
                <i className="fas fa-chevron-down addr-picker-chevron" />
              </div>
            </div>
          </div>

          <div className="address-field-plain">
            <span className="address-field-label">Комментарий для курьера</span>
            <input
              className="address-field-input"
              type="text"
              placeholder="Код домофона, ориентир..."
              value={data.comment}
              onChange={(e) => update('comment', e.target.value)}
            />
          </div>
        </div>

        <div className={`nav-indicator${hintActive ? ' nav-indicator--active' : ''}`}>
          <div className="nav-line" />
          <div className="nav-text">
            <span>после заполнения</span>
            <span>листайте вверх</span>
          </div>
        </div>
      </div>

      {sheet && (
        <BottomSheet
          config={sheet}
          current={data[sheet.field]}
          onSelect={update}
          onClose={() => setSheet(null)}
        />
      )}
    </div>
  )
}

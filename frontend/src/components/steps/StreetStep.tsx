import { useState, useEffect } from 'react'
import { Button } from '../ui/Button'
import { getAddresses } from '../../api'
import type { Street } from '../../types'

interface Props {
  selected: string
  onSelect: (street: string) => void
  onNext: () => void
  onBack: () => void
}

export function StreetStep({ selected, onSelect, onNext, onBack }: Props) {
  const [streets, setStreets] = useState<Street[]>([])

  useEffect(() => {
    getAddresses().then((data) => setStreets(data.streets))
  }, [])

  const handleSelect = (name: string) => {
    onSelect(name)
  }

  return (
    <div className="step">
      <h2>Выберите улицу</h2>
      <div className="options-grid">
        {streets.map((s) => (
          <button
            key={s.slug}
            type="button"
            className={`option-btn ${selected === s.name ? 'option-btn-selected' : ''}`}
            onClick={() => handleSelect(s.name)}
          >
            {s.name}
          </button>
        ))}
      </div>
      <div className="step-buttons">
        <Button variant="outline" onClick={onBack}>Назад</Button>
        <Button onClick={onNext} disabled={!selected}>Далее</Button>
      </div>
    </div>
  )
}

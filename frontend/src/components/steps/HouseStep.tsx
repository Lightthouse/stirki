import { useState, useEffect } from 'react'
import { Button } from '../ui/Button'
import { getAddresses } from '../../api'
import type { Street } from '../../types'

interface Props {
  street: string
  selected: string
  onSelect: (house: string) => void
  onNext: () => void
  onBack: () => void
}

export function HouseStep({ street, selected, onSelect, onNext, onBack }: Props) {
  const [houses, setHouses] = useState<string[]>([])

  useEffect(() => {
    getAddresses().then((data) => {
      const found = data.streets.find((s: Street) => s.name === street)
      setHouses(found?.houses || [])
    })
  }, [street])

  return (
    <div className="step">
      <h2>Выберите дом</h2>
      <p className="step-description">{street}</p>
      <div className="options-grid">
        {houses.map((h) => (
          <button
            key={h}
            type="button"
            className={`option-btn ${selected === h ? 'option-btn-selected' : ''}`}
            onClick={() => onSelect(h)}
          >
            {h}
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

import { useState, useEffect } from 'react'
import { Button } from '../ui/Button'
import { ServiceCard } from '../ui/ServiceCard'
import { getServices } from '../../api'
import type { ServiceItem } from '../../types'

interface Props {
  selected: string[]
  onToggle: (slug: string) => void
  onNext: () => void
  onBack: () => void
  bagsNumber: number
}

function formatPrice(n: number): string {
  return n.toLocaleString('ru-RU')
}

export function ServicesStep({ selected, onToggle, onNext, onBack, bagsNumber }: Props) {
  const [services, setServices] = useState<ServiceItem[]>([])
  const [basePrice, setBasePrice] = useState(0)

  useEffect(() => {
    getServices().then((data) => {
      const base = data.find((s) => s.slug === 'base')
      if (base) setBasePrice(base.price_rub)
      // Не показываем базовую стирку как опцию — она включена всегда
      setServices(data.filter((s) => s.slug !== 'base'))
    })
  }, [])

  const extrasSum = services
    .filter((s) => selected.includes(s.slug))
    .reduce((sum, s) => sum + s.price_rub, 0)

  const total = bagsNumber * (basePrice + extrasSum)

  return (
    <div className="step">
      <h2>Дополнительные услуги</h2>
      <p className="step-description">Выберите нужные услуги (необязательно)</p>
      <div className="services-list">
        {services.map((s) => (
          <ServiceCard
            key={s.slug}
            name={s.name}
            price={s.price_rub}
            selected={selected.includes(s.slug)}
            onToggle={() => onToggle(s.slug)}
          />
        ))}
      </div>
      {basePrice > 0 && (
        <div className="price-formula">
          <span className="price-formula-label">Итого:</span>
          <span className="price-formula-calc">
            {bagsNumber} &times; ({formatPrice(basePrice)} ₽{extrasSum > 0 && <> + {formatPrice(extrasSum)} ₽</>}) = <strong>{formatPrice(total)} ₽</strong>
          </span>
        </div>
      )}
      <div className="step-buttons">
        <Button variant="outline" onClick={onBack}>Назад</Button>
        <Button onClick={onNext}>Далее</Button>
      </div>
    </div>
  )
}

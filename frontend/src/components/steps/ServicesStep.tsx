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
}

export function ServicesStep({ selected, onToggle, onNext, onBack }: Props) {
  const [services, setServices] = useState<ServiceItem[]>([])

  useEffect(() => {
    getServices().then((data) => {
      // Не показываем базовую стирку как опцию — она включена всегда
      setServices(data.filter((s) => s.slug !== 'base'))
    })
  }, [])

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
      <div className="step-buttons">
        <Button variant="outline" onClick={onBack}>Назад</Button>
        <Button onClick={onNext}>Далее</Button>
      </div>
    </div>
  )
}

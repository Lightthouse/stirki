import { useState } from 'react'
import { Button } from '../ui/Button'
import { InfoModal } from '../ui/InfoModal'

interface Props {
  onNext: () => void
}

export function WelcomeStep({ onNext }: Props) {
  const [showInfo, setShowInfo] = useState(false)

  return (
    <div className="step welcome-step">
      <div className="welcome-hero">
        <h2 className="welcome-title">Стирки ON</h2>
        <p className="welcome-subtitle">
          Сервис по стирке и глажке повседневной одежды за 3 часа
        </p>
      </div>

      <div className="welcome-features">
        <div className="welcome-feature">
          <span className="welcome-feature-icon">🚪</span>
          <span>Забираем у двери в обычном пакете</span>
        </div>
        <div className="welcome-feature">
          <span className="welcome-feature-icon">👕</span>
          <span>Индивидуальная стирка — только ваши вещи</span>
        </div>
        <div className="welcome-feature">
          <span className="welcome-feature-icon">🧺</span>
          <span>Стираем, сушим, гладим и возвращаем к двери</span>
        </div>
      </div>

      <Button onClick={onNext} className="btn-full">Оформить заказ</Button>
      <button className="welcome-info-link" onClick={() => setShowInfo(true)}>
        Подробнее о сервисе
      </button>

      {showInfo && <InfoModal onClose={() => setShowInfo(false)} />}
    </div>
  )
}

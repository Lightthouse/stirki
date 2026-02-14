import { Button } from '../ui/Button'

interface Props {
  count: number
  onCountChange: (count: number) => void
  onNext: () => void
  onBack: () => void
}

const BAG_OPTIONS = [1, 2, 3, 4, 5, 6, 7, 8, 9]

export function BagsStep({ count, onCountChange, onNext, onBack }: Props) {
  return (
    <div className="step">
      <h2>Количество пакетов</h2>
      <p className="step-description">Сколько пакетов с одеждой нужно постирать?</p>
      <div className="options-grid options-grid-compact">
        {BAG_OPTIONS.map((n) => (
          <button
            key={n}
            type="button"
            className={`option-btn option-btn-square ${count === n ? 'option-btn-selected' : ''}`}
            onClick={() => onCountChange(n)}
          >
            {n}
          </button>
        ))}
      </div>
      <div className="step-buttons">
        <Button variant="outline" onClick={onBack}>Назад</Button>
        <Button onClick={onNext} disabled={!count}>Далее</Button>
      </div>
    </div>
  )
}

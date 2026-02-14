import { Button } from '../ui/Button'
import { Input } from '../ui/Input'

interface Props {
  apartment: number
  onApartmentChange: (val: number) => void
  onNext: () => void
  onBack: () => void
}

export function ApartmentStep({ apartment, onApartmentChange, onNext, onBack }: Props) {
  return (
    <div className="step">
      <h2>Номер квартиры</h2>
      <Input
        id="apartment"
        type="number"
        inputMode="numeric"
        placeholder="42"
        value={apartment || ''}
        onChange={(e) => onApartmentChange(Number(e.target.value))}
        autoFocus
      />
      <div className="step-buttons">
        <Button variant="outline" onClick={onBack}>Назад</Button>
        <Button onClick={onNext} disabled={!apartment}>Далее</Button>
      </div>
    </div>
  )
}

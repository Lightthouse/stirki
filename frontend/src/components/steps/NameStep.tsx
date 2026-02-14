import { Button } from '../ui/Button'
import { Input } from '../ui/Input'

interface Props {
  name: string
  onNameChange: (name: string) => void
  onNext: () => void
  onBack: () => void
}

export function NameStep({ name, onNameChange, onNext, onBack }: Props) {
  return (
    <div className="step">
      <h2>Ваше имя</h2>
      <Input
        id="name"
        type="text"
        placeholder="Иван"
        value={name}
        onChange={(e) => onNameChange(e.target.value)}
        autoFocus
      />
      <div className="step-buttons">
        <Button variant="outline" onClick={onBack}>Назад</Button>
        <Button onClick={onNext} disabled={!name.trim()}>Далее</Button>
      </div>
    </div>
  )
}

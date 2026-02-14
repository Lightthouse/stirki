import { useState } from 'react'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { requestCode } from '../../api'

interface Props {
  phone: string
  onPhoneChange: (phone: string) => void
  onNext: () => void
}

export function PhoneStep({ phone, onPhoneChange, onNext }: Props) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async () => {
    if (!phone || phone.length < 10) {
      setError('Введите корректный номер телефона')
      return
    }
    setLoading(true)
    setError('')
    try {
      const result = await requestCode(phone)
      // MVP: показываем код (потом убрать)
      if (result.code) {
        alert(`Код подтверждения: ${result.code}`)
      }
      onNext()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка отправки кода')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="step">
      <h2>Номер телефона</h2>
      <p className="step-description">Введите ваш номер для входа</p>
      <Input
        id="phone"
        type="tel"
        placeholder="+7 (999) 000-00-00"
        value={phone}
        onChange={(e) => onPhoneChange(e.target.value)}
        autoFocus
      />
      {error && <p className="error">{error}</p>}
      <Button fullWidth onClick={handleSubmit} disabled={loading}>
        {loading ? 'Отправка...' : 'Получить код'}
      </Button>
    </div>
  )
}

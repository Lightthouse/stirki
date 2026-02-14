import { useState } from 'react'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { verifyCode } from '../../api'
import type { ClientInfo } from '../../types'

interface Props {
  phone: string
  code: string
  onCodeChange: (code: string) => void
  onNext: () => void
  onBack: () => void
  onClientFound: (client: ClientInfo) => void
}

export function CodeStep({ phone, code, onCodeChange, onNext, onBack, onClientFound }: Props) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async () => {
    if (code.length !== 4) {
      setError('Введите 4-значный код')
      return
    }
    setLoading(true)
    setError('')
    try {
      const result = await verifyCode(phone, code)
      if (!result.is_new_client && result.client) {
        onClientFound(result.client)
      }
      onNext()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Неверный код')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="step">
      <h2>Код подтверждения</h2>
      <p className="step-description">Введите код, отправленный на {phone}</p>
      <Input
        id="code"
        type="text"
        inputMode="numeric"
        maxLength={4}
        placeholder="0000"
        value={code}
        onChange={(e) => onCodeChange(e.target.value)}
        autoFocus
      />
      {error && <p className="error">{error}</p>}
      <div className="step-buttons">
        <Button variant="outline" onClick={onBack}>Назад</Button>
        <Button onClick={handleSubmit} disabled={loading}>
          {loading ? 'Проверка...' : 'Подтвердить'}
        </Button>
      </div>
    </div>
  )
}

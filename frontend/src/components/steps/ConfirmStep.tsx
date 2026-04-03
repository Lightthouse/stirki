import { useState, useEffect } from 'react'
import { Button } from '../ui/Button'
import { createOrder, getServices } from '../../api'
import type { OrderFormData, ServiceItem } from '../../types'

interface Props {
  formData: OrderFormData
  onPaymentUrl: (url: string) => void
  onOrderCreated: (orderId: number) => void
  onBack: () => void
}

export function ConfirmStep({ formData, onPaymentUrl, onOrderCreated, onBack }: Props) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [services, setServices] = useState<ServiceItem[]>([])

  useEffect(() => {
    getServices().then(setServices)
  }, [])

  const handleConfirm = async () => {
    setLoading(true)
    setError('')
    try {
      const result = await createOrder({
        street: formData.street,
        house: formData.house,
        apartment: formData.apartment,
        entrance: formData.entrance,
        floor: formData.floor,
        washing_type: 'bag',
        bags_number: formData.bags_number,
        services: formData.services,
        comment: formData.comment || undefined,
      })

      onOrderCreated(result.order_id)

      if (result.confirmation_url) {
        onPaymentUrl(result.confirmation_url)
        window.location.href = result.confirmation_url
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка создания заказа')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="step">
      <h2>Подтверждение заказа</h2>
      <div className="confirm-details">
        <div className="confirm-row">
          <span>Адрес:</span>
          <span>{formData.street}, д. {formData.house}, кв. {formData.apartment}</span>
        </div>
        <div className="confirm-row">
          <span>Пакетов:</span>
          <span>{formData.bags_number}</span>
        </div>
        {formData.services.length > 0 && (
          <div className="confirm-row">
            <span>Доп. услуги:</span>
            <span>{formData.services.map(slug => services.find(s => s.slug === slug)?.name ?? slug).join(', ')}</span>
          </div>
        )}
        {formData.comment && (
          <div className="confirm-row">
            <span>Комментарий:</span>
            <span>{formData.comment}</span>
          </div>
        )}
      </div>
      {error && <p className="error">{error}</p>}
      <div className="step-buttons">
        <Button variant="outline" onClick={onBack}>Назад</Button>
        <Button onClick={handleConfirm} disabled={loading}>
          {loading ? 'Создание заказа...' : 'Оформить заказ'}
        </Button>
      </div>
    </div>
  )
}

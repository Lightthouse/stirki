import { useState, useCallback } from 'react'
import type { Step, OrderFormData, ClientInfo } from '../types'

const INITIAL_FORM: OrderFormData = {
  phone: '',
  code: '',
  name: '',
  street: '',
  house: '',
  apartment: 0,
  entrance: 1,
  floor: 1,
  bags_number: 1,
  services: [],
  comment: '',
}

const NEW_CLIENT_STEPS: Step[] = [
  'phone', 'code', 'name', 'street', 'house', 'apartment', 'bags', 'services', 'confirm',
]

const RETURNING_CLIENT_STEPS: Step[] = [
  'phone', 'code', 'bags', 'services', 'confirm',
]

// Уже авторизован — пропускаем auth и ввод адреса
const AUTH_STEPS: Step[] = [
  'bags', 'services', 'confirm',
]

export function useOrderFlow(startAuthenticated = false) {
  const [step, setStep] = useState<Step>(startAuthenticated ? 'bags' : 'phone')
  const [formData, setFormData] = useState<OrderFormData>(INITIAL_FORM)
  const [isReturningClient, setIsReturningClient] = useState(startAuthenticated)
  const [orderId, setOrderId] = useState<number | null>(null)

  const steps = startAuthenticated
    ? AUTH_STEPS
    : (isReturningClient ? RETURNING_CLIENT_STEPS : NEW_CLIENT_STEPS)

  const currentStepIndex = steps.indexOf(step)

  const updateField = useCallback(<K extends keyof OrderFormData>(
    key: K,
    value: OrderFormData[K],
  ) => {
    setFormData((prev) => ({ ...prev, [key]: value }))
  }, [])

  const nextStep = useCallback(() => {
    const idx = steps.indexOf(step)
    if (idx < steps.length - 1) {
      setStep(steps[idx + 1])
    }
  }, [step, steps])

  const prevStep = useCallback(() => {
    const idx = steps.indexOf(step)
    if (idx > 0) {
      setStep(steps[idx - 1])
    }
  }, [step, steps])

  const prefillFromClient = useCallback((client: ClientInfo) => {
    setFormData((prev) => ({
      ...prev,
      name: client.name || '',
      street: client.street,
      house: client.house,
      apartment: client.apartment,
      entrance: client.entrance,
      floor: client.floor,
    }))
    setIsReturningClient(true)
  }, [])

  const goToPayment = useCallback(() => setStep('payment'), [])
  const goToStatus = useCallback(() => setStep('status'), [])

  const reset = useCallback(() => {
    setStep(startAuthenticated ? 'bags' : 'phone')
    setFormData(INITIAL_FORM)
    setIsReturningClient(startAuthenticated)
    setOrderId(null)
  }, [startAuthenticated])

  return {
    step,
    setStep,
    formData,
    updateField,
    nextStep,
    prevStep,
    prefillFromClient,
    isReturningClient,
    orderId,
    setOrderId,
    goToPayment,
    goToStatus,
    reset,
    currentStepIndex,
    totalSteps: steps.length,
  }
}

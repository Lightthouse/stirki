import { Link } from 'react-router-dom'
import { useOrderFlow } from '../hooks/useOrderFlow'
import { isAuthenticated } from '../api/client'
import { StepIndicator } from '../components/ui/StepIndicator'
import { PhoneStep } from '../components/steps/PhoneStep'
import { CodeStep } from '../components/steps/CodeStep'
import { NameStep } from '../components/steps/NameStep'
import { StreetStep } from '../components/steps/StreetStep'
import { HouseStep } from '../components/steps/HouseStep'
import { ApartmentStep } from '../components/steps/ApartmentStep'
import { BagsStep } from '../components/steps/BagsStep'
import { ServicesStep } from '../components/steps/ServicesStep'
import { ConfirmStep } from '../components/steps/ConfirmStep'
import { StatusStep } from '../components/steps/StatusStep'

export function OrderPage() {
  const flow = useOrderFlow()

  const toggleService = (slug: string) => {
    const current = flow.formData.services
    if (current.includes(slug)) {
      flow.updateField('services', current.filter((s) => s !== slug))
    } else {
      flow.updateField('services', [...current, slug])
    }
  }

  const renderStep = () => {
    switch (flow.step) {
      case 'phone':
        return (
          <PhoneStep
            phone={flow.formData.phone}
            onPhoneChange={(v) => flow.updateField('phone', v)}
            onNext={flow.nextStep}
          />
        )
      case 'code':
        return (
          <CodeStep
            phone={flow.formData.phone}
            code={flow.formData.code}
            onCodeChange={(v) => flow.updateField('code', v)}
            onNext={flow.nextStep}
            onBack={flow.prevStep}
            onClientFound={flow.prefillFromClient}
          />
        )
      case 'name':
        return (
          <NameStep
            name={flow.formData.name}
            onNameChange={(v) => flow.updateField('name', v)}
            onNext={flow.nextStep}
            onBack={flow.prevStep}
          />
        )
      case 'street':
        return (
          <StreetStep
            selected={flow.formData.street}
            onSelect={(v) => flow.updateField('street', v)}
            onNext={flow.nextStep}
            onBack={flow.prevStep}
          />
        )
      case 'house':
        return (
          <HouseStep
            street={flow.formData.street}
            selected={flow.formData.house}
            onSelect={(v) => flow.updateField('house', v)}
            onNext={flow.nextStep}
            onBack={flow.prevStep}
          />
        )
      case 'apartment':
        return (
          <ApartmentStep
            apartment={flow.formData.apartment}
            onApartmentChange={(v) => flow.updateField('apartment', v)}
            onNext={flow.nextStep}
            onBack={flow.prevStep}
          />
        )
      case 'bags':
        return (
          <BagsStep
            count={flow.formData.bags_number}
            onCountChange={(v) => flow.updateField('bags_number', v)}
            onNext={flow.nextStep}
            onBack={flow.prevStep}
          />
        )
      case 'services':
        return (
          <ServicesStep
            selected={flow.formData.services}
            onToggle={toggleService}
            onNext={flow.nextStep}
            onBack={flow.prevStep}
          />
        )
      case 'confirm':
        return (
          <ConfirmStep
            formData={flow.formData}
            onPaymentUrl={() => flow.goToPayment()}
            onOrderCreated={(id) => {
              flow.setOrderId(id)
              flow.goToStatus()
            }}
            onBack={flow.prevStep}
          />
        )
      case 'payment':
        return (
          <div className="step">
            <h2>Перенаправление на оплату...</h2>
            <p>Если перенаправление не произошло, обновите страницу.</p>
          </div>
        )
      case 'status':
        return flow.orderId ? (
          <StatusStep orderId={flow.orderId} onNewOrder={flow.reset} />
        ) : null
      default:
        return null
    }
  }

  return (
    <div className="page">
      <header className="header">
        <h1>Стирки ON</h1>
        {isAuthenticated() && (
          <Link to="/orders" className="nav-link">Мои заказы</Link>
        )}
      </header>
      {flow.step !== 'status' && flow.step !== 'payment' && (
        <StepIndicator current={flow.currentStepIndex} total={flow.totalSteps} />
      )}
      <main className="main">{renderStep()}</main>
    </div>
  )
}

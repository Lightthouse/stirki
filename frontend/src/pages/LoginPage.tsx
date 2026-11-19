import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { isAuthenticated } from '../api/client'
import { requestCode, verifyCode, updateMe } from '../api'
import { InfoModal } from '../components/ui/InfoModal'
import { OfferModal } from '../components/ui/OfferModal'
import { PrivacyModal } from '../components/ui/PrivacyModal'


// phone — только номер; register — галочки согласий, только для нового номера; code — ввод кода; name — имя нового клиента
type Phase = 'phone' | 'register' | 'code' | 'name'

function formatName(raw: string): string {
  const cleaned = raw.replace(/[^а-яА-ЯёЁ ]/g, '')
  return cleaned
    .split(' ')
    .map((word) => (word.length > 0 ? word[0].toUpperCase() + word.slice(1).toLowerCase() : ''))
    .join(' ')
}


function formatPhone(raw: string): string {
  let digits = raw.replace(/\D/g, '')
  if (digits.startsWith('8')) digits = '7' + digits.slice(1)
  if (digits.length > 0 && !digits.startsWith('7')) digits = '7' + digits
  digits = digits.slice(0, 11)

  if (digits.length === 0) return ''
  const d = digits
  if (d.length <= 1) return '+' + d
  if (d.length <= 4) return `+${d[0]} ${d.slice(1)}`
  if (d.length <= 7) return `+${d[0]} ${d.slice(1, 4)} ${d.slice(4)}`
  if (d.length <= 9) return `+${d[0]} ${d.slice(1, 4)} ${d.slice(4, 7)}-${d.slice(7)}`
  return `+${d[0]} ${d.slice(1, 4)} ${d.slice(4, 7)}-${d.slice(7, 9)}-${d.slice(9)}`
}

export function LoginPage() {
  const navigate = useNavigate()
  const [phase, setPhase] = useState<Phase>('phone')
  const [phone, setPhone] = useState('')
  const [code, setCode] = useState('')
  const [name, setName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [timer, setTimer] = useState(0)
  const [smsCode, setSmsCode] = useState('')
  const [showInfo, setShowInfo] = useState(false)
  const [showOffer, setShowOffer] = useState(false)
  const [showPrivacy, setShowPrivacy] = useState(false)
  // номер не зарегистрирован: при проверке кода отправляем согласия
  const [registering, setRegistering] = useState(false)
  // галочки на шаге регистрации: оферта обязательна, рассылка — по желанию
  const [offerAccepted, setOfferAccepted] = useState(false)
  const [smsMarketing, setSmsMarketing] = useState(false)
  const [offerError, setOfferError] = useState(false)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (isAuthenticated()) {
      navigate('/')
    }
  }, [])

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [])

  function startTimer() {
    setTimer(60)
    timerRef.current = setInterval(() => {
      setTimer((t) => {
        if (t <= 1) {
          clearInterval(timerRef.current!)
          return 0
        }
        return t - 1
      })
    }, 1000)
  }

  function showCodeStep(code: string | null) {
    setSmsCode(code ?? '')
    setCode('')
    setPhase('code')
    startTimer()
  }

  // Шаг 1: только номер. Зарегистрированному сервер сразу шлёт код, новому — просит регистрацию.
  async function handleContinue() {
    if (!phone.trim()) {
      setError('Введите номер телефона')
      return
    }
    setLoading(true)
    setError('')
    try {
      const res = await requestCode(phone.trim(), false)
      if (res.registration_required) {
        setRegistering(true)
        setPhase('register')
      } else {
        setRegistering(false)
        showCodeStep(res.code)
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка отправки кода')
    } finally {
      setLoading(false)
    }
  }

  // Шаг регистрации: согласия, затем код. Email для чеков спрашивается в корзине платного заказа.
  async function handleRegister() {
    if (!offerAccepted) {
      setError('')
      setOfferError(true)
      return
    }
    setLoading(true)
    setError('')
    try {
      const res = await requestCode(phone.trim(), true)
      showCodeStep(res.code)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка отправки кода')
    } finally {
      setLoading(false)
    }
  }

  function changePhone() {
    if (timerRef.current) clearInterval(timerRef.current)
    setTimer(0)
    setError('')
    setOfferError(false)
    setPhase('phone')
  }

  async function handleVerifyCode() {
    if (!code.trim()) {
      setError('Введите код из SMS')
      return
    }
    setLoading(true)
    setError('')
    try {
      const registration = registering
        ? { offerAccepted, smsMarketingConsent: smsMarketing }
        : undefined
      const res = await verifyCode(phone.trim(), code.trim(), registration)
      if (res.is_new_client) {
        setPhase('name')
      } else {
        navigate('/order')
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Неверный код')
    } finally {
      setLoading(false)
    }
  }

  async function handleNameDone() {
    if (!name.trim()) {
      setError('Введите ваше имя')
      return
    }
    setLoading(true)
    setError('')
    try {
      await updateMe({ name: name.trim() })
      navigate('/order')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка сохранения')
    } finally {
      setLoading(false)
    }
  }

  async function handleResend() {
    if (timer > 0) return
    setLoading(true)
    setError('')
    try {
      const res = await requestCode(phone.trim(), registering && offerAccepted)
      setSmsCode(res.code ?? '')
      startTimer()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка отправки кода')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="start-screen">
      <div className="app-header">
        <div className="app-logo">
          <img src="/logo.png" alt="стиркаON" />
        </div>
        <div className="header-actions">
          <div className="header-icon" onClick={() => setShowInfo(true)} title="О сервисе">
            <i className="fas fa-info-circle" />
          </div>
          <div className="header-icon" onClick={() => navigate('/')} title="На главную">
            <i className="fas fa-home" />
          </div>
        </div>
      </div>
      <div className="form-card">
        {phase === 'phone' && (
          <>
            <div className="hero-title-large" style={{ marginBottom: 28 }}>
              Бесплатный сервис<br />
              по стирке и глажке<br />
              повседневной одежды<br />
              с доставкой
            </div>
            <div className="field-label-text">Номер телефона</div>
            <div className="input-underline">
              <input
                type="tel"
                placeholder="+7 999 887-76-65"
                value={phone}
                onChange={(e) => setPhone(formatPhone(e.target.value))}
                onKeyDown={(e) => e.key === 'Enter' && handleContinue()}
                autoFocus
              />
            </div>
            {error && <p className="error-text">{error}</p>}
            <button className="btn-pill btn-pill-accent" onClick={handleContinue} disabled={loading}>
              {loading ? 'Проверка...' : 'Продолжить'}
            </button>
          </>
        )}

        {phase === 'register' && (
          <>
            <div className="login-title">Регистрация</div>
            <div className="login-subtitle">
              Номер <span>{phone}</span> ещё не зарегистрирован.
              <br />
              <span className="link-text" onClick={changePhone}>Изменить номер</span>
            </div>
            <label className={`consent-check${offerError ? ' consent-check--error' : ''}`}>
              <input
                type="checkbox"
                checked={offerAccepted}
                onChange={(e) => { setOfferAccepted(e.target.checked); setOfferError(false) }}
              />
              <span>
                Я принимаю условия{' '}
                {/* preventDefault — клик по ссылке открывает документ, а не переключает галочку */}
                <span className="link-text" onClick={(e) => { e.preventDefault(); setShowOffer(true) }}>Публичной оферты</span> и{' '}
                <span className="link-text" onClick={(e) => { e.preventDefault(); setShowPrivacy(true) }}>Политики конфиденциальности</span>
              </span>
            </label>
            <label className="consent-check">
              <input
                type="checkbox"
                checked={smsMarketing}
                onChange={(e) => setSmsMarketing(e.target.checked)}
              />
              <span>Я согласен(на) на получение рекламных и информационных СМС-рассылок</span>
            </label>
            {offerError && <p className="error-text">Чтобы продолжить, примите условия оферты и политики</p>}
            {error && <p className="error-text">{error}</p>}
            <button className="btn-pill btn-pill-accent" onClick={handleRegister} disabled={loading}>
              {loading ? 'Отправка...' : 'Получить код'}
            </button>
          </>
        )}

        {phase === 'code' && (
          <>
            <div className="login-title">Подтверждение</div>
            <div className="login-subtitle">
              Введите код, отправленный на номер
              <br/>
              <span>{phone}</span>
              <br />
              <span className="link-text" onClick={changePhone}>Изменить номер</span>
            </div>
            {smsCode && (
              <p style={{ fontSize: 13, color: '#9AAEAA', marginBottom: 8 }}>
                код: {smsCode}
              </p>
            )}
            <div className="field-label-text">Код из SMS</div>
            <div className="input-underline">
              <input
                type="text"
                inputMode="numeric"
                placeholder="Введите код"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleVerifyCode()}
                autoFocus
              />
            </div>
            {error && <p className="error-text">{error}</p>}
            <button className="btn-pill btn-pill-accent" onClick={handleVerifyCode} disabled={loading}>
              {loading ? 'Проверка...' : 'Подтвердить'}
            </button>
            <p className="timer-text">
              {timer > 0 ? (
                <>Отправить повторно через {timer} сек</>
              ) : (
                <span className="timer-resend" onClick={handleResend}>
                  Отправить повторно
                </span>
              )}
            </p>
          </>
        )}

        {phase === 'name' && (
          <>
            <div className="login-title" style={{ marginBottom: 28 }}>Заполните данные</div>
            <div className="field-label-text">Ваше имя</div>
            <div className="input-underline">
              <input
                type="text"
                placeholder="Александр"
                value={name}
                onChange={(e) => setName(formatName(e.target.value))}
                onKeyDown={(e) => e.key === 'Enter' && handleNameDone()}
                autoFocus
              />
            </div>
            {error && <p className="error-text">{error}</p>}
            <button className="btn-pill btn-pill-accent" onClick={handleNameDone} disabled={loading}>
              {loading ? 'Сохранение...' : 'Сохранить'}
            </button>
          </>
        )}

        <button className="btn-ghost" onClick={() => navigate('/')} style={{ marginTop: 12 }}>
          <i className="fas fa-arrow-left" /> Назад
        </button>
      </div>

      {showInfo && <InfoModal onClose={() => setShowInfo(false)} />}
      {showOffer && <OfferModal onClose={() => setShowOffer(false)} />}
      {showPrivacy && <PrivacyModal onClose={() => setShowPrivacy(false)} />}
    </div>
  )
}

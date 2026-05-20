import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { isAuthenticated } from '../api/client'
import { requestCode, verifyCode, updateMe } from '../api'
import { InfoModal } from '../components/ui/InfoModal'
import { OfferModal } from '../components/ui/OfferModal'
import { PrivacyModal } from '../components/ui/PrivacyModal'


type Phase = 'phone' | 'code' | 'name'

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

  async function handleSendCode() {
    if (!phone.trim()) {
      setError('Введите номер телефона')
      return
    }
    setLoading(true)
    setError('')
    try {
      console.log('[DEBUG] отправка кода на:', phone.trim())
      const res = await requestCode(phone.trim())
      console.log('[DEBUG] ответ сервера:', res)
      if (res.code) setSmsCode(res.code)
      setPhase('code')
      startTimer()
    } catch (e) {
      console.error('[DEBUG] ошибка:', e)
      setError(e instanceof Error ? e.message : 'Ошибка отправки кода')
    } finally {
      setLoading(false)
    }
  }

  async function handleVerifyCode() {
    if (!code.trim()) {
      setError('Введите код из SMS')
      return
    }
    setLoading(true)
    setError('')
    try {
      const res = await verifyCode(phone.trim(), code.trim())
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
      const res = await requestCode(phone.trim())
      if (res.code) setSmsCode(res.code)
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
          стирка<span>он</span>
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
                onKeyDown={(e) => e.key === 'Enter' && handleSendCode()}
                autoFocus
              />
            </div>
            {error && <p className="error-text">{error}</p>}
            <button className="btn-pill btn-pill-accent" onClick={handleSendCode} disabled={loading}>
              {loading ? 'Отправка...' : 'Получить код'}
            </button>
            <div className="login-agreement">
              Нажимая «Получить код», вы соглашаетесь с{' '}
              <span className="link-text" onClick={() => setShowOffer(true)}>публичной офертой</span> и{' '}
              <span className="link-text" onClick={() => setShowPrivacy(true)}>политикой обработки данных</span>
            </div>
          </>
        )}

        {phase === 'code' && (
          <>
            <div className="login-title">Подтверждение</div>
            <div className="login-subtitle">
              Введите код, отправленный на номер
              <br/>
              <span>{phone}</span>
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

import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { isAuthenticated } from '../api/client'
import { requestCode, verifyCode, updateMe } from '../api'

type Phase = 'phone' | 'code' | 'name'

export function LoginPage() {
  const navigate = useNavigate()
  const [phase, setPhase] = useState<Phase>('phone')
  const [phone, setPhone] = useState('')
  const [code, setCode] = useState('')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [timer, setTimer] = useState(0)
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
      const res = await requestCode(phone.trim())
      console.log('[DEBUG] SMS код:', res.code)
      setPhase('code')
      startTimer()
    } catch (e) {
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
      await updateMe({ name: name.trim(), email: email.trim() || undefined })
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
      console.log('[DEBUG] SMS код (повтор):', res.code)
      startTimer()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка отправки кода')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="start-screen">
      <div className="form-card">
        <div className="logo-large">стирка<span className="accent">он</span></div>
        <h3 style={{ textAlign: 'center', marginBottom: 20, fontSize: 18, color: 'rgba(255,255,255,0.9)' }}>
          Вход / Регистрация
        </h3>

        {phase === 'phone' && (
          <>
            <div className="input-field">
              <i className="fas fa-phone" />
              <input
                type="tel"
                placeholder="+7 (___) ___-__-__"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSendCode()}
                autoFocus
              />
            </div>
            {error && <p className="error-text">{error}</p>}
            <button className="btn-pill" onClick={handleSendCode} disabled={loading}>
              <i className="fas fa-paper-plane" />
              {loading ? 'Отправка...' : 'Получить код по SMS'}
            </button>
          </>
        )}

        {phase === 'code' && (
          <>
            <div className="input-field" style={{ opacity: 0.6 }}>
              <i className="fas fa-phone" />
              <input type="tel" value={phone} disabled />
            </div>
            <div className="input-field">
              <i className="fas fa-key" />
              <input
                type="text"
                inputMode="numeric"
                placeholder="Код из SMS"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleVerifyCode()}
                autoFocus
              />
            </div>
            {error && <p className="error-text">{error}</p>}
            <button className="btn-pill btn-pill-accent" onClick={handleVerifyCode} disabled={loading}>
              <i className="fas fa-check-circle" />
              {loading ? 'Проверка...' : 'Подтвердить код'}
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
            <div className="input-field">
              <i className="fas fa-user" />
              <input
                type="text"
                placeholder="Ваше имя"
                value={name}
                onChange={(e) => setName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleNameDone()}
                autoFocus
              />
            </div>
            <div className="input-field">
              <i className="fas fa-envelope" />
              <input
                type="email"
                placeholder="Email для чека (необязательно)"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleNameDone()}
              />
            </div>
            {error && <p className="error-text">{error}</p>}
            <button className="btn-pill btn-pill-accent" onClick={handleNameDone} disabled={loading}>
              <i className="fas fa-arrow-right" />
              {loading ? 'Сохранение...' : 'Продолжить'}
            </button>
          </>
        )}

        <button className="btn-ghost" onClick={() => navigate('/')} style={{ marginTop: 12 }}>
          <i className="fas fa-arrow-left" /> Назад
        </button>
      </div>
    </div>
  )
}

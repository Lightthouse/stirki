import { useEffect, useRef, useState } from 'react'

interface Props {
  images: string[]
  count: number
  durationSec: number
  onComplete: () => void
  onAdViewed?: (imagePath: string) => void
}

// Если картинка не загрузилась за это время — не держим клиента, показываем дальше.
const LOAD_TIMEOUT_MS = 15000

/**
 * Показ рекламы: `count` случайных картинок по `durationSec` секунд каждая.
 *
 * Отсчёт по картинке начинается только когда она загрузилась и видна на экране —
 * иначе на медленном интернете время уходило на загрузку, а таймер показывал
 * секунды следующей картинки, пока на экране ещё была предыдущая.
 * Время считается по часам (Date.now), а не по числу тиков setInterval,
 * который в фоне и на слабых телефонах срабатывает реже раза в секунду.
 */
export function AdViewer({ images, count, durationSec, onComplete, onAdViewed }: Props) {
  const onCompleteRef = useRef(onComplete)
  onCompleteRef.current = onComplete
  const onAdViewedRef = useRef(onAdViewed)
  onAdViewedRef.current = onAdViewed
  const duration = Math.max(1, durationSec)

  const [selected] = useState<string[]>(() => {
    if (images.length === 0 || count <= 0) return []
    const shuffled = [...images].sort(() => Math.random() - 0.5)
    return shuffled.slice(0, count)
  })
  const [current, setCurrent] = useState(0)
  // текущая картинка загружена (или не загрузилась, и мы перестали ждать) — идёт отсчёт
  const [ready, setReady] = useState(false)
  const [timeLeft, setTimeLeft] = useState(duration)
  // картинка так и не показалась — просмотр в статистику не пишем
  const failedRef = useRef(false)

  // Заранее грузим все выбранные картинки, чтобы следующая открылась без ожидания.
  useEffect(() => {
    selected.forEach((src) => { new Image().src = src })
  }, [selected])

  useEffect(() => {
    if (selected.length === 0) onCompleteRef.current()
  }, [selected])

  useEffect(() => {
    if (ready || selected.length === 0) return
    const id = setTimeout(() => {
      failedRef.current = true
      setReady(true)
    }, LOAD_TIMEOUT_MS)
    return () => clearTimeout(id)
  }, [current, ready, selected])

  useEffect(() => {
    if (!ready) return
    const startedAt = Date.now()
    setTimeLeft(duration)
    const id = setInterval(() => {
      const left = duration - Math.floor((Date.now() - startedAt) / 1000)
      if (left > 0) {
        setTimeLeft(left)
        return
      }
      clearInterval(id)
      if (!failedRef.current) onAdViewedRef.current?.(selected[current])
      if (current < selected.length - 1) {
        failedRef.current = false
        setReady(false)
        setCurrent(current + 1)
      } else {
        onCompleteRef.current()
      }
    }, 250)
    return () => clearInterval(id)
  }, [ready, current, duration, selected])

  function handleLoaded() {
    failedRef.current = false
    setReady(true)
  }

  function handleFailed() {
    failedRef.current = true
    setReady(true)
  }

  if (selected.length === 0) return null

  return (
    <div className="showcase-overlay">
      <div className="showcase-header">
        <span className="app-logo"><img src="/logo.png" alt="стиркаON" /></span>
      </div>
      {/* key — новый <img> на каждую картинку: предыдущая не висит на экране, пока грузится следующая */}
      <img
        key={current}
        ref={(img) => {
          // картинка из кэша могла загрузиться раньше, чем навесился onLoad
          if (img?.complete && img.naturalWidth > 0 && !ready) handleLoaded()
        }}
        className="showcase-image"
        src={selected[current]}
        alt={`Реклама ${current + 1}`}
        style={{ visibility: ready ? 'visible' : 'hidden' }}
        onLoad={handleLoaded}
        onError={handleFailed}
      />
      <div className="showcase-footer">
        <span className="showcase-counter">{current + 1}/{selected.length}</span>
        <span className="showcase-timer">{ready ? `${timeLeft} сек` : 'загрузка…'}</span>
      </div>
    </div>
  )
}

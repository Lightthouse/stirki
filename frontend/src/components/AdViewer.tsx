import { useEffect, useRef, useState } from 'react'

interface Props {
  images: string[]
  count: number
  durationSec: number
  onComplete: () => void
  onAdViewed?: (imagePath: string) => void
}

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
  const [timeLeft, setTimeLeft] = useState(duration)

  useEffect(() => {
    if (selected.length === 0) {
      onCompleteRef.current()
      return
    }

    let idx = 0
    let t = duration

    const interval = setInterval(() => {
      t--
      if (t > 0) {
        setTimeLeft(t)
      } else {
        onAdViewedRef.current?.(selected[idx])
        if (idx < selected.length - 1) {
          idx++
          t = duration
          setCurrent(idx)
          setTimeLeft(duration)
        } else {
          clearInterval(interval)
          onCompleteRef.current()
        }
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [selected, duration])

  if (selected.length === 0) return null

  return (
    <div className="ad-viewer-overlay">
      <div className="ad-viewer-header">
        <span className="app-logo">стирка<span>он</span></span>
      </div>
      <img
        className="ad-viewer-image"
        src={selected[current]}
        alt={`Реклама ${current + 1}`}
      />
      <div className="ad-viewer-footer">
        <span className="ad-viewer-counter">{current + 1}/{selected.length}</span>
        <span className="ad-viewer-timer">{timeLeft} сек</span>
      </div>
    </div>
  )
}

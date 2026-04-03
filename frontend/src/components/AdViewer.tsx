import { useEffect, useRef, useState } from 'react'

interface Props {
  images: string[]
  onComplete: () => void
}

const AD_DURATION = 5

export function AdViewer({ images, onComplete }: Props) {
  const onCompleteRef = useRef(onComplete)
  onCompleteRef.current = onComplete

  const [selected] = useState<string[]>(() => {
    if (images.length === 0) return []
    const shuffled = [...images].sort(() => Math.random() - 0.5)
    return shuffled.slice(0, 3)
  })
  const [current, setCurrent] = useState(0)
  const [timeLeft, setTimeLeft] = useState(AD_DURATION)

  useEffect(() => {
    if (selected.length === 0) {
      onCompleteRef.current()
      return
    }

    let idx = 0
    let t = AD_DURATION

    const interval = setInterval(() => {
      t--
      if (t > 0) {
        setTimeLeft(t)
      } else {
        if (idx < selected.length - 1) {
          idx++
          t = AD_DURATION
          setCurrent(idx)
          setTimeLeft(AD_DURATION)
        } else {
          clearInterval(interval)
          onCompleteRef.current()
        }
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [selected])

  if (selected.length === 0) return null

  return (
    <div className="ad-viewer-overlay">
      <div className="ad-viewer-box">
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
    </div>
  )
}

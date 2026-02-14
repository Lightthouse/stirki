interface StepIndicatorProps {
  current: number
  total: number
}

export function StepIndicator({ current, total }: StepIndicatorProps) {
  return (
    <div className="step-indicator">
      <div className="step-indicator-bar">
        <div
          className="step-indicator-fill"
          style={{ width: `${((current + 1) / total) * 100}%` }}
        />
      </div>
      <span className="step-indicator-text">
        {current + 1} / {total}
      </span>
    </div>
  )
}

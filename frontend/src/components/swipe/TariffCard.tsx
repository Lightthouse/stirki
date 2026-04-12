export type Tariff = 'free' | 'paid'

interface Props {
  selected: Tariff | null
  onSelect: (t: Tariff) => void
  onHintActivate: () => void
  hintActive: boolean
}

export function TariffCard({ selected, onSelect, onHintActivate, hintActive }: Props) {
  function choose(t: Tariff) {
    onSelect(t)
    onHintActivate()
  }

  return (
    <div className="swipe-card">
      <div className="card-content">
        <p className="tariff-prompt">Выберите тариф</p>
        <div className="tariff-grid">
          <div
            className={`tariff-card free${selected === 'free' ? ' selected' : ''}`}
            onClick={() => choose('free')}
          >
            <div className="tariff-header">
              <span className="tariff-name"><i className="fas fa-gift" /> Бесплатно</span>
              <span className="tariff-price">0 ₽</span>
            </div>
            <div className="tariff-desc">только пакет · допы недоступны · 1 позиция</div>
            <div className={`like-button${selected === 'free' ? ' selected' : ''}`}>
              <i className={`${selected === 'free' ? 'fas' : 'far'} fa-heart`} />
              {selected === 'free' ? 'выбрано' : 'выбрать'}
            </div>
          </div>

          <div
            className={`tariff-card paid${selected === 'paid' ? ' selected' : ''}`}
            onClick={() => choose('paid')}
          >
            <div className="tariff-header">
              <span className="tariff-name"><i className="fas fa-bolt" /> Платно</span>
              <span className="tariff-price">от 190 ₽</span>
            </div>
            <div className="tariff-desc">вещь или пакет · любые допы · до 3 позиций</div>
            <div className={`like-button${selected === 'paid' ? ' selected' : ''}`}>
              <i className={`${selected === 'paid' ? 'fas' : 'far'} fa-heart`} />
              {selected === 'paid' ? 'выбрано' : 'выбрать'}
            </div>
          </div>
        </div>

        <div className={`swipe-hint${hintActive ? ' active' : ''}`}>
          <i className="fas fa-chevron-up" /> потяните вверх <i className="fas fa-chevron-up" />
        </div>
        <div className="progress-dots">
          <span className="dot" />
          <span className="dot active" />
          <span className="dot" />
          <span className="dot" />
        </div>
      </div>
    </div>
  )
}

export type Tariff = 'free' | 'paid'

interface Props {
  minPaidPrice: number
  adsRequired: number
  selected: Tariff | null
  onSelect: (t: Tariff) => void
  onHintActivate: () => void
  hintActive: boolean
}

export function TariffCard({ minPaidPrice, adsRequired, selected, onSelect, onHintActivate, hintActive }: Props) {
  function choose(t: Tariff, e: React.MouseEvent) {
    e.stopPropagation()
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
            onClick={(e) => choose('free', e)}
          >
            <div className="tariff-header">
              <span className="tariff-name">Бесплатно</span>
              <span className="tariff-price">0 ₽</span>
            </div>
            <ul className="tariff-features">
              <li>пакет до 3 кг</li>
              {adsRequired > 0 && <li>просмотр рекламы</li>}
              <li>возможна очередь</li>
            </ul>
            <div className="tariff-tag">попробуйте сервис</div>
            <button
              className={`tariff-btn${selected === 'free' ? ' selected' : ''}`}
              onClick={(e) => choose('free', e)}
            >
              {selected === 'free' ? 'Выбрано' : 'Выбрать бесплатный'}
            </button>
          </div>

          <div
            className={`tariff-card paid${selected === 'paid' ? ' selected' : ''}`}
            onClick={(e) => choose('paid', e)}
          >
            <div className="tariff-header">
              <span className="tariff-name">Платно</span>
              <span className="tariff-price">от {minPaidPrice} ₽</span>
            </div>
            <ul className="tariff-features">
              <li>вещь или пакет</li>
              <li>допы</li>
              <li>без рекламы</li>
            </ul>
            <div className="tariff-tag">приоритетная стирка</div>
            <button
              className={`tariff-btn${selected === 'paid' ? ' selected' : ''}`}
              onClick={(e) => choose('paid', e)}
            >
              {selected === 'paid' ? 'Выбрано' : 'Выбрать платный'}
            </button>
          </div>

        </div>

        <div className={`nav-indicator${hintActive ? ' nav-indicator--active' : ''}`}>
          <div className="nav-line" />
          <div className="nav-text">
            <span>после выбора тарифа</span>
            <span>листайте вверх</span>
          </div>
        </div>
      </div>
    </div>
  )
}

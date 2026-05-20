export type Tariff = 'free' | 'paid'

interface Props {
  selected: Tariff | null
  onSelect: (t: Tariff) => void
  onHintActivate: () => void
  hintActive: boolean
}

export function TariffCard({ selected, onSelect, onHintActivate, hintActive }: Props) {
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
              <li>просмотр 3 рекламных объявлений</li>
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
              <span className="tariff-price">от 390 ₽</span>
            </div>
            <ul className="tariff-features">
              <li>вещь или пакет</li>
              <li>любые допуслуги</li>
              <li>до 3 позиций в корзине</li>
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

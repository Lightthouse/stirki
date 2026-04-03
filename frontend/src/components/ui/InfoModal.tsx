interface Props {
  onClose: () => void
}

export function InfoModal({ onClose }: Props) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()}>
        <h3><i className="fas fa-star" /> о стиркаОН</h3>

        <section>
          <h4>Как работаем</h4>
          <ul>
            <li>Забираем у двери в любом стандартном продуктовом пакете (25×40 см)</li>
            <li>Стираем, сушим и гладим</li>
            <li>Возвращаем упакованные вещи к двери или в руки</li>
          </ul>
        </section>

        <section>
          <h4>Важно</h4>
          <ul>
            <li>Каждый этап виден в приложении</li>
            <li>Индивидуально — в барабане только ваши вещи</li>
            <li>Бережная стирка — до 30°C, отжим до 800 об/мин</li>
            <li>По цветам не делим — один пакет = один цвет</li>
          </ul>
        </section>

        <section>
          <h4>Тарифы</h4>
          <ul>
            <li>Партия — 890 ₽ (пакет одежды или белья, до 3 кг)</li>
            <li>Глажка — 990 ₽</li>
            <li>Кондиционер — +100 ₽</li>
            <li>Вакуумный пакет — +150 ₽</li>
          </ul>
        </section>

        <section>
          <h4>Дополнительно</h4>
          <ul>
            <li>Локация — Мытищи</li>
            <li>Связь — <a href="https://t.me/stirkion_bot" target="_blank" rel="noopener noreferrer">@stirkion_bot</a></li>
            <li>График — ежедневно с 07:00 до 23:00</li>
          </ul>
        </section>

        <button className="btn-pill btn-pill-accent" onClick={onClose}>
          Понятно
        </button>
      </div>
    </div>
  )
}

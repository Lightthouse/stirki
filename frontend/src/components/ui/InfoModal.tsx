interface Props {
  onClose: () => void
}

export function InfoModal({ onClose }: Props) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>&times;</button>

        <h2>О сервисе</h2>

        <section className="modal-section">
          <h3>Как работаем</h3>
          <ul>
            <li>Забираем у двери в любом стандартном продуктовом пакете (25&times;40 см)</li>
            <li>Стираем, сушим и гладим</li>
            <li>Возвращаем упакованные вещи к двери или в руки</li>
          </ul>
        </section>

        <section className="modal-section">
          <h3>Важно</h3>
          <ul>
            <li>Каждый этап виден в приложении</li>
            <li>Индивидуально — в барабане стираем только ваши вещи (с другими не смешиваем)</li>
            <li>Бережная стирка — режимы до 30 градусов и отжим не более 800 оборотов/мин</li>
            <li>По цветам не делим — один пакет = один цвет (чёрное/белое/цветное)</li>
          </ul>
        </section>

        <section className="modal-section">
          <h3>Тариф</h3>
          <p><strong>Основное:</strong></p>
          <ul>
            <li>Партия — 890 ₽ (полный продуктовый пакет одежды или постельного белья, до 3 кг)</li>
          </ul>
          <p><strong>Добавить к основному:</strong></p>
          <ul>
            <li>Глажка — 990 ₽</li>
            <li>Кондиционер — 50 ₽</li>
            <li>Вакуумный пакет — 150 ₽</li>
            <li>Пятновыводитель — 80 ₽</li>
            <li>Отбеливатель — 80 ₽</li>
            <li>Тряпочка для цветного — 30 ₽</li>
            <li>Стирка в мешочке — 30 ₽</li>
          </ul>
        </section>

        <section className="modal-section">
          <h3>Дополнительно</h3>
          <ul>
            <li>Локация — гипермаркет «Базарбай»</li>
            <li>Для связи — <a href="https://t.me/stirkion_bot" target="_blank" rel="noopener noreferrer">@stirkion_bot</a></li>
            <li>График работы — ежедневно с 07:00 до 23:00</li>
          </ul>
        </section>

        <button className="btn btn-primary btn-full" onClick={onClose}>Понятно</button>
      </div>
    </div>
  )
}

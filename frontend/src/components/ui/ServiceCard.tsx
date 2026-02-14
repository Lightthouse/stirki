interface ServiceCardProps {
  name: string
  price: number
  selected: boolean
  onToggle: () => void
}

export function ServiceCard({ name, price, selected, onToggle }: ServiceCardProps) {
  return (
    <button
      type="button"
      className={`service-card ${selected ? 'service-card-selected' : ''}`}
      onClick={onToggle}
    >
      <span className="service-card-check">{selected ? '\u2705' : '\u2B1C'}</span>
      <span className="service-card-name">{name}</span>
      <span className="service-card-price">{price} ₽</span>
    </button>
  )
}

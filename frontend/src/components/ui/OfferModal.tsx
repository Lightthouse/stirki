import { SiteTextBody, useSiteText } from './RichText'

interface Props {
  onClose: () => void
}

/** Публичная оферта — текст в админке «Тексты сайта» (offer). */
export function OfferModal({ onClose }: Props) {
  const text = useSiteText('offer')
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()}>
        {text && text.title && <h3><i className="fas fa-file-contract" /> {text.title}</h3>}
        <SiteTextBody text={text} />
        <button className="btn-pill btn-pill-accent" onClick={onClose}>
          Понятно
        </button>
      </div>
    </div>
  )
}

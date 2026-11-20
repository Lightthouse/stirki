import { SiteTextBody, useSiteText } from './RichText'

interface Props {
  onClose: () => void
}

/** Политика обработки ПДн — текст в админке «Тексты сайта» (privacy). */
export function PrivacyModal({ onClose }: Props) {
  const text = useSiteText('privacy')
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()}>
        {text && text.title && <h3><i className="fas fa-shield-alt" /> {text.title}</h3>}
        <SiteTextBody text={text} />
        <button className="btn-pill btn-pill-accent" onClick={onClose}>
          Понятно
        </button>
      </div>
    </div>
  )
}

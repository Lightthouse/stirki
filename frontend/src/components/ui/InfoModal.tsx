import { SiteTextBody, useSiteText } from './RichText'
import { SupportContacts } from './SupportContacts'

interface Props {
  onClose: () => void
}

/**
 * «Подробнее о сервисе» — текст в админке «Тексты сайта» (about). Цены и часы приёма в нём пишутся вручную
 * (решение 2026-11-20): при смене цен в «Услугах» или акции текст нужно поправить отдельно.
 * Контакты поддержки — из «Системных настроек».
 */
export function InfoModal({ onClose }: Props) {
  const text = useSiteText('about')
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()}>
        {text && text.title && <h3><i className="fas fa-info-circle" /> {text.title}</h3>}
        <SiteTextBody text={text} />

        <section>
          <h4>Поддержка</h4>
          <SupportContacts />
        </section>

        <button className="btn-pill btn-pill-accent" onClick={onClose}>
          Понятно
        </button>
      </div>
    </div>
  )
}

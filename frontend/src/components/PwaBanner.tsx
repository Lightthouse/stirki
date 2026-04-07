import { usePwaInstall } from '../hooks/usePwaInstall'

export function PwaBanner() {
  const { canInstall, isIos, install, dismiss } = usePwaInstall()

  if (canInstall) {
    return (
      <div className="pwa-banner">
        <div className="pwa-banner-icon">
          <i className="fas fa-download" />
        </div>
        <div className="pwa-banner-text">
          <div className="pwa-banner-title">Установить приложение</div>
          <div className="pwa-banner-sub">Работает без браузера, как обычное приложение</div>
        </div>
        <button className="pwa-banner-btn" onClick={install}>
          Установить
        </button>
        <button className="pwa-banner-close" onClick={dismiss} aria-label="Закрыть">
          <i className="fas fa-times" />
        </button>
      </div>
    )
  }

  if (isIos) {
    return (
      <div className="pwa-banner">
        <div className="pwa-banner-icon">
          <i className="fas fa-arrow-up-from-bracket" />
        </div>
        <div className="pwa-banner-text">
          <div className="pwa-banner-title">Установить приложение</div>
          <div className="pwa-banner-sub">
            Нажмите <i className="fas fa-arrow-up-from-bracket pwa-share-inline" /> → «На экран "Домой"»
          </div>
        </div>
        <button className="pwa-banner-close" onClick={dismiss} aria-label="Закрыть">
          <i className="fas fa-times" />
        </button>
      </div>
    )
  }

  return null
}

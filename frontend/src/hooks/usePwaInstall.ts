import { useState, useEffect } from 'react'

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

const DISMISSED_KEY = 'pwa_banner_dismissed'

function storageGet(key: string): boolean {
  try { return !!localStorage.getItem(key) } catch { return false }
}

function storageSet(key: string, value: string): void {
  try { localStorage.setItem(key, value) } catch { /* ignore */ }
}

function detectIos(): boolean {
  return /iphone|ipad|ipod/i.test(navigator.userAgent)
    && !navigator.userAgent.includes('CriOS')
    && !(window.navigator as unknown as { standalone?: boolean }).standalone
}

export function usePwaInstall() {
  const [prompt, setPrompt] = useState<BeforeInstallPromptEvent | null>(null)
  const [dismissed, setDismissed] = useState(() => storageGet(DISMISSED_KEY))
  const [isIos] = useState(() => detectIos())

  useEffect(() => {
    const handler = (e: Event) => {
      e.preventDefault()
      setPrompt(e as BeforeInstallPromptEvent)
    }
    window.addEventListener('beforeinstallprompt', handler)
    return () => window.removeEventListener('beforeinstallprompt', handler)
  }, [])

  const install = async () => {
    if (!prompt) return
    prompt.prompt()
    const { outcome } = await prompt.userChoice
    if (outcome === 'accepted') setPrompt(null)
  }

  const dismiss = () => {
    storageSet(DISMISSED_KEY, '1')
    setDismissed(true)
  }

  return {
    canInstall: !!prompt && !dismissed,
    isIos: isIos && !dismissed,
    install,
    dismiss,
  }
}

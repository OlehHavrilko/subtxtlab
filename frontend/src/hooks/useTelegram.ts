/**
 * useTelegram — хук для работы с Telegram WebApp API.
 * Автоматически инициализирует приложение.
 */
import { useEffect } from 'react'

declare global {
  interface Window {
    Telegram?: {
      WebApp: TelegramWebApp
    }
  }
}

interface TelegramWebApp {
  ready: () => void
  expand: () => void
  close: () => void
  initData: string
  initDataUnsafe: { user?: TGUser; query_id?: string }
  themeParams: Record<string, string>
  colorScheme: 'light' | 'dark'
  MainButton: {
    text: string
    show: () => void
    hide: () => void
    onClick: (fn: () => void) => void
    offClick: (fn: () => void) => void
    showProgress: (leaveActive?: boolean) => void
    hideProgress: () => void
    setParams: (params: Record<string, unknown>) => void
  }
  HapticFeedback: {
    impactOccurred: (style: 'light' | 'medium' | 'heavy') => void
    notificationOccurred: (type: 'error' | 'success' | 'warning') => void
  }
  openTelegramLink: (url: string) => void
  showAlert: (message: string, callback?: () => void) => void
  showConfirm: (message: string, callback: (confirmed: boolean) => void) => void
}

export interface TGUser {
  id: number
  first_name: string
  last_name?: string
  username?: string
  language_code?: string
}

export function useTelegram() {
  const tg = window.Telegram?.WebApp

  useEffect(() => {
    if (tg) {
      tg.ready()
      tg.expand()
    }
  }, [tg])

  return {
    tg,
    user: tg?.initDataUnsafe?.user,
    initData: tg?.initData ?? '',
    isDark: tg?.colorScheme === 'dark',
    haptic: tg?.HapticFeedback,
  }
}

import { useEffect, useState } from 'react'
import { TabBar, type Tab } from './components/TabBar'
import { IdeasPage } from './pages/IdeasPage'
import { PlanPage } from './pages/PlanPage'
import { TrendsPage } from './pages/TrendsPage'
import { ProcessPage } from './pages/ProcessPage'
import { SavedPage } from './pages/SavedPage'
import { useTelegram } from './hooks/useTelegram'

export default function App() {
  const { tg, user } = useTelegram()
  const [tab, setTab] = useState<Tab>('ideas')

  useEffect(() => {
    // BackButton: возврат к ideas если не на главной
    if (!tg) return
    if (tab !== 'ideas') {
      tg.MainButton?.hide?.()
    }
  }, [tab, tg])

  const pages: Record<Tab, JSX.Element> = {
    ideas: <IdeasPage />,
    plan: <PlanPage />,
    process: <ProcessPage />,
    saved: <SavedPage />,
    trends: <TrendsPage />,
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--tg-bg)' }}>
      {/* Header */}
      <header
        className="sticky top-0 z-40 flex items-center justify-between px-4 py-3"
        style={{ background: 'var(--tg-secondary-bg)', borderBottom: '1px solid rgba(255,255,255,0.06)' }}
      >
        <div className="flex items-center gap-2">
          <span className="text-xl">🎬</span>
          <span className="font-bold text-base" style={{ color: 'var(--tg-text)' }}>CinemaClip AI</span>
        </div>
        {user && (
          <span className="text-xs" style={{ color: 'var(--tg-hint)' }}>
            {user.first_name}
          </span>
        )}
      </header>

      {/* Page content */}
      <main>{pages[tab]}</main>

      {/* Bottom nav */}
      <TabBar active={tab} onChange={setTab} />
    </div>
  )
}

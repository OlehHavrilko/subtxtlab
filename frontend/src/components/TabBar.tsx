export type Tab = 'ideas' | 'plan' | 'process' | 'saved' | 'trends'

const TABS: { id: Tab; icon: string; label: string }[] = [
  { id: 'ideas',   icon: '🔍', label: 'Идеи'    },
  { id: 'plan',    icon: '📅', label: 'План'    },
  { id: 'process', icon: '🎬', label: 'Клип'    },
  { id: 'saved',   icon: '💾', label: 'Архив'   },
  { id: 'trends',  icon: '📈', label: 'Тренды'  },
]

interface Props {
  active: Tab
  onChange: (tab: Tab) => void
}

export function TabBar({ active, onChange }: Props) {
  return (
    <nav
      className="fixed bottom-0 left-0 right-0 flex border-t z-50"
      style={{
        background: 'var(--tg-secondary-bg)',
        borderColor: 'rgba(255,255,255,0.08)',
        paddingBottom: 'env(safe-area-inset-bottom)',
      }}
    >
      {TABS.map((tab) => {
        const isActive = tab.id === active
        return (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            className="flex-1 flex flex-col items-center py-2 text-xs transition-colors"
            style={{ color: isActive ? 'var(--tg-button)' : 'var(--tg-hint)' }}
          >
            <span className="text-xl leading-none mb-0.5">{tab.icon}</span>
            <span className={isActive ? 'font-semibold' : ''}>{tab.label}</span>
          </button>
        )
      })}
    </nav>
  )
}

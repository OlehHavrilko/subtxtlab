import React, { useState } from 'react'
import { generateIdeas } from '../api/client'
import { IdeaCard } from '../components/IdeaCard'
import type { Idea } from '../api/client'

export function IdeasPage() {
  const [theme, setTheme] = useState('')
  const [ideas, setIdeas] = useState<Idea[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSearch = async () => {
    if (!theme.trim()) return
    setLoading(true)
    setError('')
    try {
      const result = await generateIdeas(theme.trim())
      setIdeas(result)
      window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Ошибка')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="px-4 pt-4 pb-24">
      <h1 className="text-xl font-bold mb-1" style={{ color: 'var(--tg-text)' }}>🔍 Поиск сцен</h1>
      <p className="text-sm mb-4" style={{ color: 'var(--tg-hint)' }}>
        Введи тему — AI найдёт кинематографичные сцены с таймкодами
      </p>

      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={theme}
          onChange={(e) => setTheme(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="одиночество и смысл..."
          className="flex-1"
        />
        <button
          onClick={handleSearch}
          disabled={loading || !theme.trim()}
          className="px-4 py-3 rounded-xl font-semibold text-sm disabled:opacity-50 transition-opacity"
          style={{ background: 'var(--tg-button)', color: 'var(--tg-button-text)', minWidth: 72 }}
        >
          {loading ? '⏳' : 'Найти'}
        </button>
      </div>

      {/* Quick themes */}
      <div className="flex flex-wrap gap-2 mb-4">
        {['одиночество', 'смысл жизни', 'любовь и потеря', 'будущее AI', 'свобода'].map((t) => (
          <button
            key={t}
            onClick={() => { setTheme(t); }}
            className="text-xs px-3 py-1.5 rounded-full transition-colors"
            style={{ background: 'rgba(255,255,255,0.06)', color: 'var(--tg-hint)' }}
          >
            {t}
          </button>
        ))}
      </div>

      {error && (
        <div className="rounded-xl p-3 mb-4 text-sm" style={{ background: 'rgba(239,68,68,0.1)', color: '#f87171' }}>
          ❌ {error}
        </div>
      )}

      {loading && (
        <div className="flex flex-col items-center py-12 gap-3">
          <div className="w-10 h-10 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: 'var(--tg-button)' }} />
          <p className="text-sm" style={{ color: 'var(--tg-hint)' }}>Ищу лучшие сцены...</p>
        </div>
      )}

      {!loading && ideas.map((idea) => (
        <IdeaCard key={idea.scene_id} idea={idea} />
      ))}
    </div>
  )
}

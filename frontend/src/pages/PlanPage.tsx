import React, { useState } from 'react'
import { generatePlan } from '../api/client'
import { IdeaCard } from '../components/IdeaCard'
import type { Idea } from '../api/client'

const DAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

export function PlanPage() {
  const [genres, setGenres] = useState('')
  const [plan, setPlan] = useState<Idea[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleGenerate = async () => {
    setLoading(true)
    setError('')
    try {
      const result = await generatePlan(genres.trim())
      setPlan(result)
      window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Ошибка')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="px-4 pt-4 pb-24">
      <h1 className="text-xl font-bold mb-1" style={{ color: 'var(--tg-text)' }}>📅 Контент-план</h1>
      <p className="text-sm mb-4" style={{ color: 'var(--tg-hint)' }}>
        7 идей на неделю — разные фильмы, эмоции, эпохи
      </p>

      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={genres}
          onChange={(e) => setGenres(e.target.value)}
          placeholder="жанры: драма, sci-fi... (необязательно)"
          className="flex-1"
        />
        <button
          onClick={handleGenerate}
          disabled={loading}
          className="px-4 py-3 rounded-xl font-semibold text-sm disabled:opacity-50"
          style={{ background: 'var(--tg-button)', color: 'var(--tg-button-text)', minWidth: 80 }}
        >
          {loading ? '⏳' : 'Создать'}
        </button>
      </div>

      {error && (
        <div className="rounded-xl p-3 mb-4 text-sm" style={{ background: 'rgba(239,68,68,0.1)', color: '#f87171' }}>
          ❌ {error}
        </div>
      )}

      {loading && (
        <div className="flex flex-col items-center py-12 gap-3">
          <div className="w-10 h-10 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: 'var(--tg-button)' }} />
          <p className="text-sm" style={{ color: 'var(--tg-hint)' }}>Генерирую план на неделю...</p>
        </div>
      )}

      {!loading && plan.map((idea, i) => (
        <IdeaCard key={idea.scene_id} idea={idea} dayLabel={DAYS[i]} />
      ))}
    </div>
  )
}

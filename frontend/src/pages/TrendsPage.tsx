import React, { useState } from 'react'
import { getTrends } from '../api/client'

export function TrendsPage() {
  const [analysis, setAnalysis] = useState('')
  const [loading, setLoading] = useState(false)
  const [loaded, setLoaded] = useState(false)

  const handleLoad = async () => {
    setLoading(true)
    try {
      const result = await getTrends()
      setAnalysis(result)
      setLoaded(true)
    } catch (e: unknown) {
      setAnalysis(e instanceof Error ? `❌ ${e.message}` : '❌ Ошибка')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="px-4 pt-4 pb-24">
      <h1 className="text-xl font-bold mb-1" style={{ color: 'var(--tg-text)' }}>📈 Тренды ниши</h1>
      <p className="text-sm mb-4" style={{ color: 'var(--tg-hint)' }}>
        AI анализирует что сейчас работает в cinema TikTok
      </p>

      {!loaded && (
        <button
          onClick={handleLoad}
          disabled={loading}
          className="w-full py-4 rounded-2xl font-semibold text-base disabled:opacity-50 transition-opacity"
          style={{ background: 'var(--tg-button)', color: 'var(--tg-button-text)' }}
        >
          {loading ? '⏳ Анализирую...' : '📊 Загрузить анализ трендов'}
        </button>
      )}

      {loading && (
        <div className="flex flex-col items-center py-12 gap-3">
          <div className="w-10 h-10 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: 'var(--tg-button)' }} />
          <p className="text-sm" style={{ color: 'var(--tg-hint)' }}>Анализирую тренды...</p>
        </div>
      )}

      {analysis && !loading && (
        <div
          className="rounded-2xl p-4 mt-4 text-sm leading-relaxed whitespace-pre-wrap"
          style={{ background: 'var(--tg-secondary-bg)', color: 'var(--tg-text)' }}
        >
          {analysis}
        </div>
      )}

      {loaded && (
        <button
          onClick={() => { setLoaded(false); setAnalysis(''); }}
          className="mt-3 w-full py-2 rounded-xl text-sm"
          style={{ background: 'rgba(255,255,255,0.06)', color: 'var(--tg-hint)' }}
        >
          🔄 Обновить
        </button>
      )}
    </div>
  )
}

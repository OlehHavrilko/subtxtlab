import React, { useEffect, useState } from 'react'
import { getSavedScenes } from '../api/client'
import { IdeaCard } from '../components/IdeaCard'
import type { Idea } from '../api/client'

export function SavedPage() {
  const [scenes, setScenes] = useState<Idea[]>([])
  const [filtered, setFiltered] = useState<Idea[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getSavedScenes()
      .then((data) => { setScenes(data); setFiltered(data) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    const q = search.toLowerCase().trim()
    if (!q) return setFiltered(scenes)
    setFiltered(scenes.filter((s) =>
      s.film.toLowerCase().includes(q) ||
      s.scene_id.includes(q) ||
      (s.description ?? '').toLowerCase().includes(q) ||
      (s.hashtags ?? '').toLowerCase().includes(q)
    ))
  }, [search, scenes])

  return (
    <div className="px-4 pt-4 pb-24">
      <h1 className="text-xl font-bold mb-1" style={{ color: 'var(--tg-text)' }}>💾 Архив</h1>
      <p className="text-sm mb-4" style={{ color: 'var(--tg-hint)' }}>
        Сохранённые сцены — {scenes.length} идей
      </p>

      <input
        type="text"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Поиск по фильму, теме..."
        className="mb-4"
      />

      {loading && (
        <div className="flex justify-center py-12">
          <div className="w-8 h-8 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: 'var(--tg-button)' }} />
        </div>
      )}

      {!loading && filtered.length === 0 && (
        <div className="text-center py-12">
          <div className="text-5xl mb-3">{search ? '🔍' : '📭'}</div>
          <p style={{ color: 'var(--tg-hint)' }}>
            {search ? 'Ничего не найдено' : 'Архив пуст — сохрани первую идею во вкладке "Идеи"'}
          </p>
        </div>
      )}

      {filtered.map((idea) => (
        <IdeaCard key={idea.scene_id} idea={idea} onSaved={() => {}} />
      ))}
    </div>
  )
}

import React from 'react'
import type { Idea } from '../api/client'
import { saveIdea, markUsed } from '../api/client'

interface Props {
  idea: Idea
  dayLabel?: string
  onSaved?: () => void
}

export function IdeaCard({ idea, dayLabel, onSaved }: Props) {
  const [saved, setSaved] = React.useState(false)
  const [used, setUsed] = React.useState(idea.used ?? false)
  const [copied, setCopied] = React.useState(false)

  const handleSave = async () => {
    try {
      await saveIdea(idea)
      setSaved(true)
      window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light')
      onSaved?.()
    } catch { /* ignore */ }
  }

  const handleUse = async () => {
    try {
      await markUsed(idea.scene_id)
      setUsed(true)
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success')
    } catch { /* ignore */ }
  }

  const handleCopyId = () => {
    navigator.clipboard.writeText(idea.scene_id).catch(() => {})
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div className="fade-in rounded-2xl p-4 mb-3" style={{ background: 'var(--tg-secondary-bg)' }}>
      {dayLabel && (
        <div className="text-xs font-semibold mb-2" style={{ color: 'var(--tg-button)' }}>
          📆 {dayLabel}
        </div>
      )}

      <div className="flex items-start justify-between gap-2 mb-2">
        <div>
          <span className="font-bold text-base" style={{ color: 'var(--tg-text)' }}>
            🎥 {idea.film}
          </span>
          {idea.year && (
            <span className="text-sm ml-1" style={{ color: 'var(--tg-hint)' }}>
              ({idea.year})
            </span>
          )}
        </div>
        {used && <span className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full">✅ Использовано</span>}
      </div>

      <div className="text-sm mb-2" style={{ color: 'var(--tg-hint)' }}>
        ⏱ <code className="text-xs">{idea.timecode_start}</code> —{' '}
        <code className="text-xs">{idea.timecode_end}</code>
        {idea.duration_sec && <span className="ml-1">({idea.duration_sec}с)</span>}
      </div>

      {idea.quote && (
        <div className="text-sm italic mb-2 px-3 border-l-2" style={{ borderColor: 'var(--tg-button)', color: 'var(--tg-text)' }}>
          «{idea.quote}»
        </div>
      )}

      {idea.why_viral && (
        <div className="text-sm mb-2" style={{ color: 'var(--tg-link)' }}>
          🎯 {idea.why_viral}
        </div>
      )}

      {idea.description && (
        <p className="text-sm mb-2" style={{ color: 'var(--tg-text)' }}>
          {idea.description}
        </p>
      )}

      {idea.hashtags && (
        <p className="text-xs mb-3" style={{ color: 'var(--tg-hint)' }}>
          🏷 {idea.hashtags}
        </p>
      )}

      {/* Scene ID badge */}
      <button
        onClick={handleCopyId}
        className="text-xs px-2 py-1 rounded-lg mb-3 transition-colors"
        style={{ background: 'rgba(255,255,255,0.06)', color: 'var(--tg-hint)' }}
      >
        🆔 {copied ? '✓ Скопировано!' : idea.scene_id}
      </button>

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={handleSave}
          disabled={saved}
          className="flex-1 py-2 rounded-xl text-sm font-medium transition-opacity disabled:opacity-60"
          style={{ background: saved ? 'rgba(255,255,255,0.08)' : 'var(--tg-button)', color: 'var(--tg-button-text)' }}
        >
          {saved ? '✅ Сохранено' : '💾 Сохранить'}
        </button>
        <button
          onClick={handleUse}
          disabled={used}
          className="flex-1 py-2 rounded-xl text-sm font-medium transition-opacity disabled:opacity-50"
          style={{ background: 'rgba(255,255,255,0.08)', color: 'var(--tg-text)' }}
        >
          {used ? '✓ Снято' : '🎬 Использую'}
        </button>
      </div>
    </div>
  )
}

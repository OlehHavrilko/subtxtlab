import React, { useCallback, useRef, useState } from 'react'
import { startProcessing, subscribeProgress, getDownloadUrl } from '../api/client'
import type { ProgressEvent } from '../api/client'
import { ProgressBar } from '../components/ProgressBar'

type State = 'idle' | 'uploading' | 'processing' | 'done' | 'error'

export function ProcessPage() {
  const [videoFile, setVideoFile] = useState<File | null>(null)
  const [srtFile, setSrtFile] = useState<File | null>(null)
  const [sceneId, setSceneId] = useState('')
  const [state, setState] = useState<State>('idle')
  const [progress, setProgress] = useState<ProgressEvent | null>(null)
  const [jobId, setJobId] = useState('')
  const [errorMsg, setErrorMsg] = useState('')
  const videoDrop = useRef<HTMLLabelElement>(null)

  const handleProcess = async () => {
    if (!videoFile) return
    setState('uploading')
    setErrorMsg('')

    try {
      const id = await startProcessing(videoFile, srtFile, sceneId || undefined)
      setJobId(id)
      setState('processing')

      const unsub = subscribeProgress(id, (ev) => {
        setProgress(ev)
        if (ev.done) {
          setState('done')
          unsub()
          window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success')
        }
        if (ev.error) {
          setState('error')
          setErrorMsg(ev.error)
          unsub()
          window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error')
        }
      })
    } catch (e: unknown) {
      setState('error')
      setErrorMsg(e instanceof Error ? e.message : 'Ошибка загрузки')
    }
  }

  const handleReset = () => {
    setState('idle')
    setVideoFile(null)
    setSrtFile(null)
    setSceneId('')
    setProgress(null)
    setJobId('')
    setErrorMsg('')
  }

  const onVideoDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file?.type.startsWith('video/')) setVideoFile(file)
  }, [])

  return (
    <div className="px-4 pt-4 pb-24">
      <h1 className="text-xl font-bold mb-1" style={{ color: 'var(--tg-text)' }}>🎬 Обработка клипа</h1>
      <p className="text-sm mb-4" style={{ color: 'var(--tg-hint)' }}>
        .mp4 → 9:16 + русские субтитры + цветокоррекция
      </p>

      {/* ── Idle / Upload form ── */}
      {(state === 'idle') && (
        <>
          {/* Video drop zone */}
          <label
            ref={videoDrop}
            onDragOver={(e) => e.preventDefault()}
            onDrop={onVideoDrop}
            className="block w-full rounded-2xl border-2 border-dashed cursor-pointer mb-3 text-center py-8 transition-colors"
            style={{ borderColor: videoFile ? 'var(--tg-button)' : 'rgba(255,255,255,0.15)', background: 'var(--tg-secondary-bg)' }}
          >
            <input
              type="file"
              accept="video/mp4,video/*"
              className="hidden"
              onChange={(e) => setVideoFile(e.target.files?.[0] ?? null)}
            />
            {videoFile ? (
              <div>
                <div className="text-3xl mb-1">✅</div>
                <div className="text-sm font-medium" style={{ color: 'var(--tg-text)' }}>{videoFile.name}</div>
                <div className="text-xs" style={{ color: 'var(--tg-hint)' }}>{(videoFile.size / 1024 / 1024).toFixed(1)} MB</div>
              </div>
            ) : (
              <div>
                <div className="text-4xl mb-2">🎥</div>
                <div className="text-sm" style={{ color: 'var(--tg-hint)' }}>Нажми или перетащи .mp4</div>
              </div>
            )}
          </label>

          {/* SRT optional */}
          <label className="flex items-center gap-3 rounded-xl p-3 mb-3 cursor-pointer" style={{ background: 'var(--tg-secondary-bg)' }}>
            <input
              type="file"
              accept=".srt"
              className="hidden"
              onChange={(e) => setSrtFile(e.target.files?.[0] ?? null)}
            />
            <span className="text-2xl">{srtFile ? '✅' : '📄'}</span>
            <div>
              <div className="text-sm font-medium" style={{ color: 'var(--tg-text)' }}>
                {srtFile ? srtFile.name : 'Прикрепить .srt (необязательно)'}
              </div>
              <div className="text-xs" style={{ color: 'var(--tg-hint)' }}>
                Для точных субтитров вместо автотранскрипции
              </div>
            </div>
          </label>

          {/* Scene ID optional */}
          <input
            type="text"
            value={sceneId}
            onChange={(e) => setSceneId(e.target.value)}
            placeholder="scene_id (необязательно)"
            className="mb-4"
          />

          <button
            onClick={handleProcess}
            disabled={!videoFile}
            className="w-full py-4 rounded-2xl font-bold text-base disabled:opacity-40 transition-opacity"
            style={{ background: 'var(--tg-button)', color: 'var(--tg-button-text)' }}
          >
            🚀 Обработать клип
          </button>
        </>
      )}

      {/* ── Uploading ── */}
      {state === 'uploading' && (
        <div className="flex flex-col items-center py-12 gap-4">
          <div className="w-12 h-12 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: 'var(--tg-button)' }} />
          <p style={{ color: 'var(--tg-hint)' }}>Загружаю видео...</p>
        </div>
      )}

      {/* ── Processing ── */}
      {state === 'processing' && progress && (
        <div className="py-8">
          <ProgressBar percent={progress.percent} message={progress.message} />
        </div>
      )}

      {/* ── Done ── */}
      {state === 'done' && jobId && (
        <div className="py-8 text-center">
          <div className="text-6xl mb-4">🎉</div>
          <h2 className="text-xl font-bold mb-2" style={{ color: 'var(--tg-text)' }}>Готово!</h2>
          <p className="text-sm mb-6" style={{ color: 'var(--tg-hint)' }}>
            Клип 9:16 с русскими субтитрами готов
          </p>
          <a
            href={getDownloadUrl(jobId)}
            download="cinemaclip_output.mp4"
            className="block w-full py-4 rounded-2xl font-bold text-base text-center mb-3"
            style={{ background: 'var(--tg-button)', color: 'var(--tg-button-text)' }}
          >
            ⬇️ Скачать клип
          </a>
          <button
            onClick={handleReset}
            className="w-full py-3 rounded-2xl text-sm"
            style={{ background: 'rgba(255,255,255,0.06)', color: 'var(--tg-hint)' }}
          >
            🔄 Обработать ещё
          </button>
        </div>
      )}

      {/* ── Error ── */}
      {state === 'error' && (
        <div className="py-8">
          <div className="rounded-2xl p-4 mb-4 text-sm" style={{ background: 'rgba(239,68,68,0.1)', color: '#f87171' }}>
            ❌ {errorMsg}
          </div>
          <button
            onClick={handleReset}
            className="w-full py-3 rounded-2xl"
            style={{ background: 'var(--tg-button)', color: 'var(--tg-button-text)' }}
          >
            🔄 Попробовать снова
          </button>
        </div>
      )}
    </div>
  )
}

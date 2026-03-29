/**
 * API client — все запросы к FastAPI backend.
 * Автоматически прокидывает Telegram initData для auth.
 */

const BASE = import.meta.env.VITE_API_URL ?? ''

function getInitData(): string {
  return window.Telegram?.WebApp?.initData ?? ''
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-Telegram-Init-Data': getInitData(),
      ...(options.headers ?? {}),
    },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail ?? `HTTP ${res.status}`)
  }
  return res.json()
}

// ── Ideas ──────────────────────────────────────────────────────────────────

export interface Idea {
  scene_id: string
  film: string
  year: number
  timecode_start: string
  timecode_end: string
  duration_sec: number
  quote?: string
  description: string
  hashtags: string
  why_viral?: string
  theme?: string
  used?: boolean
}

export async function generateIdeas(theme: string, count = 5): Promise<Idea[]> {
  const data = await request<{ ideas: Idea[] }>('/api/ideas/generate', {
    method: 'POST',
    body: JSON.stringify({ theme, count }),
  })
  return data.ideas
}

export async function generatePlan(genres = ''): Promise<Idea[]> {
  const data = await request<{ ideas: Idea[] }>('/api/ideas/plan', {
    method: 'POST',
    body: JSON.stringify({ genres }),
  })
  return data.ideas
}

export async function getTrends(): Promise<string> {
  const data = await request<{ analysis: string }>('/api/ideas/trends')
  return data.analysis
}

export async function saveIdea(idea: Idea): Promise<void> {
  await request('/api/ideas/save', {
    method: 'POST',
    body: JSON.stringify(idea),
  })
}

export async function markUsed(sceneId: string): Promise<void> {
  await request(`/api/ideas/${sceneId}/use`, { method: 'POST' })
}

// ── Scenes ──────────────────────────────────────────────────────────────────

export async function getSavedScenes(): Promise<Idea[]> {
  const data = await request<{ scenes: Idea[] }>('/api/scenes/')
  return data.scenes
}

// ── Video ──────────────────────────────────────────────────────────────────

export interface ProcessResponse {
  job_id: string
}

export async function startProcessing(
  videoFile: File,
  srtFile?: File | null,
  sceneId?: string,
): Promise<string> {
  const form = new FormData()
  form.append('video', videoFile)
  if (srtFile) form.append('srt', srtFile)
  if (sceneId) form.append('scene_id', sceneId)

  const res = await fetch(`${BASE}/api/video/process`, {
    method: 'POST',
    headers: { 'X-Telegram-Init-Data': getInitData() },
    body: form,
  })
  if (!res.ok) throw new Error(`Upload failed: HTTP ${res.status}`)
  const data: ProcessResponse = await res.json()
  return data.job_id
}

export function subscribeProgress(
  jobId: string,
  onEvent: (event: ProgressEvent) => void,
): () => void {
  const initData = encodeURIComponent(getInitData())
  const es = new EventSource(`${BASE}/api/video/progress/${jobId}?init_data=${initData}`)
  es.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data)
      if (!data.heartbeat) onEvent(data)
    } catch { /* ignore */ }
  }
  return () => es.close()
}

export interface ProgressEvent {
  step: number
  total: number
  percent: number
  message: string
  done: boolean
  error?: string
}

export function getDownloadUrl(jobId: string): string {
  const initData = encodeURIComponent(getInitData())
  return `${BASE}/api/video/download/${jobId}?init_data=${initData}`
}

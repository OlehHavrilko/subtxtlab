interface Props {
  percent: number
  message: string
}

export function ProgressBar({ percent, message }: Props) {
  return (
    <div className="w-full">
      <div className="text-sm mb-2 text-center" style={{ color: 'var(--tg-text)' }}>{message}</div>
      <div className="w-full rounded-full h-2" style={{ background: 'rgba(255,255,255,0.1)' }}>
        <div
          className="h-2 rounded-full transition-all duration-500"
          style={{ width: `${percent}%`, background: 'var(--tg-button)' }}
        />
      </div>
      <div className="text-xs text-center mt-1" style={{ color: 'var(--tg-hint)' }}>{percent}%</div>
    </div>
  )
}

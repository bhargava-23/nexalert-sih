// Utility functions for NexAlert Dashboard

export function formatTimestamp(timestamp: string, timezone: string = 'Asia/Kolkata'): string {
  try {
    const date = new Date(timestamp)
    return new Intl.DateTimeFormat('en-IN', {
      timeZone: timezone,
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    }).format(date)
  } catch {
    return timestamp
  }
}

export function getTimeSince(timestamp: string): string {
  try {
    const date = new Date(timestamp)
    const now = new Date()
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)

    if (seconds < 60) return `${seconds}s ago`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
    return `${Math.floor(seconds / 86400)}d ago`
  } catch {
    return 'unknown'
  }
}

export function formatPercentage(value: number | null | undefined): string {
  if (value == null) return '—'
  return `${(value * 100).toFixed(0)}%`
}

export function formatValue(value: number | null | undefined, decimals: number = 1): string {
  if (value == null) return '—'
  return value.toFixed(decimals)
}

export function getSeverityColor(severity: number | null | undefined): string {
  if (severity == null) return 'text-zinc-400'
  if (severity >= 0.8) return 'text-red-400'
  if (severity >= 0.6) return 'text-orange-400'
  if (severity >= 0.4) return 'text-yellow-400'
  return 'text-green-400'
}

export function getStateColor(state: string | null | undefined): string {
  if (!state) return 'text-zinc-400'
  switch (state.toUpperCase()) {
    case 'CRITICAL':
      return 'text-red-400'
    case 'CONFIRMED':
      return 'text-orange-400'
    case 'SUSPECTED':
      return 'text-yellow-400'
    case 'WATCH':
      return 'text-blue-400'
    case 'NORMAL':
      return 'text-green-400'
    case 'RESOLVED':
      return 'text-zinc-400'
    default:
      return 'text-zinc-400'
  }
}

export function getStateBackground(state: string | null | undefined): string {
  if (!state) return 'bg-zinc-500/10'
  switch (state.toUpperCase()) {
    case 'CRITICAL':
      return 'bg-red-500/10'
    case 'CONFIRMED':
      return 'bg-orange-500/10'
    case 'SUSPECTED':
      return 'bg-yellow-500/10'
    case 'WATCH':
      return 'bg-blue-500/10'
    case 'NORMAL':
      return 'bg-green-500/10'
    case 'RESOLVED':
      return 'bg-zinc-500/10'
    default:
      return 'bg-zinc-500/10'
  }
}

export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ')
}

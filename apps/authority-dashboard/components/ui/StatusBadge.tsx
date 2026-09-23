// StatusBadge - Glassmorphic status indicator component

import { cn } from '@/lib/utils'

interface StatusBadgeProps {
  status: string | null | undefined
  size?: 'sm' | 'md' | 'lg'
  variant?: 'hazard' | 'node' | 'info'
  className?: string
}

export function StatusBadge({
  status,
  size = 'md',
  variant = 'hazard',
  className
}: StatusBadgeProps) {
  if (!status) return null

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-3 py-1',
    lg: 'text-base px-4 py-1.5'
  }

  const getVariantStyles = () => {
    const upperStatus = status.toUpperCase()

    if (variant === 'hazard') {
      switch (upperStatus) {
        case 'CRITICAL':
          return 'bg-red-500/20 text-red-300 border-red-500/30'
        case 'CONFIRMED':
          return 'bg-orange-500/20 text-orange-300 border-orange-500/30'
        case 'SUSPECTED':
          return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30'
        case 'WATCH':
          return 'bg-blue-500/20 text-blue-300 border-blue-500/30'
        case 'NORMAL':
          return 'bg-green-500/20 text-green-300 border-green-500/30'
        case 'RESOLVED':
          return 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30'
        default:
          return 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30'
      }
    }

    if (variant === 'node') {
      switch (upperStatus) {
        case 'ACTIVE':
        case 'ONLINE':
          return 'bg-green-500/20 text-green-300 border-green-500/30'
        case 'OFFLINE':
        case 'INACTIVE':
          return 'bg-red-500/20 text-red-300 border-red-500/30'
        case 'DEGRADED':
          return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30'
        default:
          return 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30'
      }
    }

    // info variant
    return 'bg-blue-500/20 text-blue-300 border-blue-500/30'
  }

  return (
    <span
      className={cn(
        'inline-flex items-center justify-center',
        'rounded-full border backdrop-blur-sm',
        'font-semibold uppercase tracking-wide',
        sizeClasses[size],
        getVariantStyles(),
        className
      )}
    >
      {status}
    </span>
  )
}

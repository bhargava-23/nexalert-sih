// LoadingSpinner - Glassmorphic loading indicator

import { cn } from '@/lib/utils'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export function LoadingSpinner({ size = 'md', className }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'w-4 h-4 border-2',
    md: 'w-8 h-8 border-3',
    lg: 'w-12 h-12 border-4'
  }

  return (
    <div
      className={cn(
        'animate-spin rounded-full',
        'border-white/20 border-t-white/80',
        sizeClasses[size],
        className
      )}
      role="status"
      aria-label="Loading"
    />
  )
}

export function LoadingSkeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'animate-pulse rounded-lg',
        'bg-gradient-to-r from-white/5 via-white/10 to-white/5',
        'bg-[length:200%_100%]',
        className
      )}
    />
  )
}

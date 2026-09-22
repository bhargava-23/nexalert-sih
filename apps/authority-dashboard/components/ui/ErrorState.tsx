// ErrorState - Glassmorphic error state with retry

import { GlassPanel } from './GlassPanel'
import { cn } from '@/lib/utils'

interface ErrorStateProps {
  title?: string
  message: string
  onRetry?: () => void
  className?: string
}

export function ErrorState({
  title = 'Error',
  message,
  onRetry,
  className
}: ErrorStateProps) {
  return (
    <GlassPanel className={cn('text-center py-12 border-red-500/20', className)}>
      <div className="flex justify-center mb-4 text-red-400 text-4xl">
        ⚠
      </div>
      <h3 className="text-lg font-semibold text-red-300 mb-2">{title}</h3>
      <p className="text-sm text-zinc-400 max-w-md mx-auto mb-6">
        {message}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          className={cn(
            'px-4 py-2 rounded-lg',
            'bg-red-500/20 hover:bg-red-500/30',
            'border border-red-500/30',
            'text-sm font-medium text-red-300',
            'transition-colors'
          )}
        >
          Retry
        </button>
      )}
    </GlassPanel>
  )
}

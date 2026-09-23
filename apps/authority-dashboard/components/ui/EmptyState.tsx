// EmptyState - Glassmorphic empty state display

import { GlassPanel } from './GlassPanel'
import { cn } from '@/lib/utils'

interface EmptyStateProps {
  title: string
  description?: string
  icon?: React.ReactNode
  action?: {
    label: string
    onClick: () => void
  }
  className?: string
}

export function EmptyState({
  title,
  description,
  icon,
  action,
  className
}: EmptyStateProps) {
  return (
    <GlassPanel className={cn('text-center py-12', className)}>
      {icon && (
        <div className="flex justify-center mb-4 text-zinc-500 text-4xl">
          {icon}
        </div>
      )}
      <h3 className="text-lg font-semibold text-zinc-300 mb-2">{title}</h3>
      {description && (
        <p className="text-sm text-zinc-500 max-w-md mx-auto mb-6">
          {description}
        </p>
      )}
      {action && (
        <button
          onClick={action.onClick}
          className={cn(
            'px-4 py-2 rounded-lg',
            'bg-white/10 hover:bg-white/20',
            'border border-white/20',
            'text-sm font-medium text-zinc-300',
            'transition-colors'
          )}
        >
          {action.label}
        </button>
      )}
    </GlassPanel>
  )
}

// GlassPanel - Base glassmorphic container component

import { cn } from '@/lib/utils'

interface GlassPanelProps {
  children: React.ReactNode
  className?: string
  blur?: 'sm' | 'md' | 'lg'
  padding?: 'none' | 'sm' | 'md' | 'lg'
}

export function GlassPanel({
  children,
  className,
  blur = 'md',
  padding = 'md'
}: GlassPanelProps) {
  const blurClass = {
    sm: 'backdrop-blur-sm',
    md: 'backdrop-blur-md',
    lg: 'backdrop-blur-lg'
  }[blur]

  const paddingClass = {
    none: '',
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6'
  }[padding]

  return (
    <div
      className={cn(
        'rounded-xl border border-white/10',
        'bg-gradient-to-br from-white/5 to-white/[0.02]',
        blurClass,
        paddingClass,
        'shadow-xl shadow-black/20',
        className
      )}
    >
      {children}
    </div>
  )
}

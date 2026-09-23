// Glass card component with subtle glassmorphism

import { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface GlassCardProps {
  children: ReactNode
  className?: string
  onClick?: () => void
}

export function GlassCard({ children, className, onClick }: GlassCardProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        'bg-zinc-900/60 backdrop-blur-md border border-white/10 rounded-2xl p-4',
        onClick && 'cursor-pointer hover:bg-zinc-900/80 transition-colors',
        className
      )}
    >
      {children}
    </div>
  )
}

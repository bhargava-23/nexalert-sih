// MetricCard - Glassmorphic metric display component

import { GlassPanel } from './GlassPanel'
import { cn } from '@/lib/utils'

interface MetricCardProps {
  label: string
  value: string | number
  unit?: string
  trend?: 'up' | 'down' | 'stable'
  trendValue?: string
  status?: 'normal' | 'warning' | 'critical' | 'good'
  icon?: React.ReactNode
  className?: string
}

export function MetricCard({
  label,
  value,
  unit,
  trend,
  trendValue,
  status = 'normal',
  icon,
  className
}: MetricCardProps) {
  const statusColors = {
    normal: 'text-zinc-300',
    warning: 'text-yellow-400',
    critical: 'text-red-400',
    good: 'text-green-400'
  }

  const trendIcons = {
    up: '↑',
    down: '↓',
    stable: '→'
  }

  return (
    <GlassPanel className={cn('relative overflow-hidden', className)}>
      {/* Subtle gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/[0.03] to-transparent pointer-events-none" />

      <div className="relative">
        <div className="flex items-start justify-between mb-2">
          <div className="text-sm text-zinc-400 font-medium">{label}</div>
          {icon && <div className="text-zinc-400">{icon}</div>}
        </div>

        <div className="flex items-baseline gap-2">
          <div className={cn('text-3xl font-bold', statusColors[status])}>
            {value}
          </div>
          {unit && (
            <div className="text-sm text-zinc-500 font-medium">{unit}</div>
          )}
        </div>

        {trend && trendValue && (
          <div className="flex items-center gap-1 mt-2 text-xs">
            <span className={cn(
              'font-semibold',
              trend === 'up' ? 'text-green-400' : trend === 'down' ? 'text-red-400' : 'text-zinc-400'
            )}>
              {trendIcons[trend]} {trendValue}
            </span>
            <span className="text-zinc-500">vs last hour</span>
          </div>
        )}
      </div>
    </GlassPanel>
  )
}

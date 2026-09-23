// Severity badge component - shows hazard severity level

interface SeverityBadgeProps {
  value: number | null | undefined
  size?: 'sm' | 'md'
}

export function SeverityBadge({ value, size = 'md' }: SeverityBadgeProps) {
  if (value == null) {
    return (
      <span
        className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium bg-zinc-700 text-zinc-300 ${
          size === 'sm' ? 'text-xs' : 'text-sm'
        }`}
      >
        N/A
      </span>
    )
  }

  let color = 'bg-zinc-700 text-zinc-300'
  let label = 'Unknown'

  if (value >= 0.7) {
    color = 'bg-red-500/20 text-red-300 border border-red-500/50'
    label = 'High'
  } else if (value >= 0.4) {
    color = 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/50'
    label = 'Medium'
  } else {
    color = 'bg-green-500/20 text-green-300 border border-green-500/50'
    label = 'Low'
  }

  return (
    <span
      className={`inline-flex items-center rounded-md px-2 py-1 font-medium ${color} ${
        size === 'sm' ? 'text-xs' : 'text-sm'
      }`}
    >
      {label}
    </span>
  )
}

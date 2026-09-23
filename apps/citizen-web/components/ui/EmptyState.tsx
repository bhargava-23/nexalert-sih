// Empty state component

interface EmptyStateProps {
  icon?: string
  title: string
  message: string
}

export function EmptyState({ icon = '📭', title, message }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="text-5xl mb-4">{icon}</div>
      <h3 className="text-xl font-semibold text-zinc-100 mb-2">{title}</h3>
      <p className="text-zinc-400 max-w-md">{message}</p>
    </div>
  )
}

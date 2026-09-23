'use client'

// NodeGrid - Grid of node status cards

import { GlassPanel } from '@/components/ui/GlassPanel'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { SectionHeader } from '@/components/ui/SectionHeader'
import { formatTimestamp, getTimeSince } from '@/lib/utils'
import type { Node } from '@/types'
import { cn } from '@/lib/utils'

interface NodeGridProps {
  nodes: Node[]
}

export function NodeGrid({ nodes }: NodeGridProps) {
  return (
    <div>
      <SectionHeader
        title="Active Nodes"
        subtitle={`${nodes.length} nodes reporting`}
      />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {nodes.map((node) => (
          <GlassPanel key={node.node_id} className="relative">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="font-semibold text-zinc-100">{node.node_id}</h3>
                {node.location && (
                  <p className="text-xs text-zinc-500 mt-1">
                    {node.location.lat.toFixed(4)}, {node.location.lon.toFixed(4)}
                  </p>
                )}
              </div>
              <StatusBadge
                status={node.status || 'UNKNOWN'}
                variant="node"
                size="sm"
              />
            </div>

            {node.last_telemetry_at && (
              <div className="text-xs text-zinc-500 mb-3">
                Last seen: {getTimeSince(node.last_telemetry_at)}
              </div>
            )}

            {node.battery_pct != null && (
              <div className="flex items-center gap-2 mb-2">
                <div className="text-xs text-zinc-400">Battery:</div>
                <div className={cn(
                  'text-sm font-semibold',
                  node.battery_pct >= 50 ? 'text-green-400' :
                  node.battery_pct >= 20 ? 'text-yellow-400' : 'text-red-400'
                )}>
                  {node.battery_pct}%
                </div>
              </div>
            )}

            {node.current_hazard_state && node.current_hazard_state !== 'NORMAL' && (
              <div className="mt-3 pt-3 border-t border-white/10">
                <div className="flex items-center gap-2">
                  <div className="text-xs text-zinc-400">Hazard:</div>
                  <StatusBadge
                    status={node.current_hazard_state}
                    variant="hazard"
                    size="sm"
                  />
                </div>
              </div>
            )}
          </GlassPanel>
        ))}
      </div>
    </div>
  )
}

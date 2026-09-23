'use client'

// Nodes Page - Node list and status overview

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { GlassPanel } from '@/components/ui/GlassPanel'
import { SectionHeader } from '@/components/ui/SectionHeader'
import { LoadingSpinner } from '@/components/ui/Loading'
import { ErrorState } from '@/components/ui/ErrorState'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { api } from '@/lib/api'
import { formatTimestamp, cn } from '@/lib/utils'
import type { Node } from '@/types'

export default function NodesPage() {
  const [nodes, setNodes] = useState<Node[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<string>('')

  const fetchNodes = async () => {
    try {
      setError(null)
      const data = await api.getNodes()
      setNodes(data)
      setLastUpdate(formatTimestamp(new Date().toISOString()))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load nodes')
      console.error('Nodes fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchNodes()
    const interval = setInterval(fetchNodes, 10000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900 flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900 flex items-center justify-center p-4">
        <ErrorState title="Nodes Error" message={error} onRetry={fetchNodes} />
      </div>
    )
  }

  const activeNodes = nodes.filter(n => n.status === 'ACTIVE')
  const inactiveNodes = nodes.filter(n => n.status !== 'ACTIVE')

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <SectionHeader
          title="Field Nodes"
          subtitle={`${activeNodes.length} active, ${inactiveNodes.length} inactive • Updated ${lastUpdate}`}
        />

        {nodes.length === 0 ? (
          <GlassPanel className="text-center py-12">
            <p className="text-zinc-400">No nodes registered</p>
          </GlassPanel>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {nodes.map((node) => (
              <Link key={node.node_id} href={`/nodes/${node.node_id}`}>
                <GlassPanel className={cn(
                  'transition-all hover:bg-white/10 cursor-pointer',
                  node.status === 'ACTIVE' ? 'border-green-500/20' : 'border-red-500/20'
                )}>
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="font-semibold text-zinc-100 text-lg">{node.node_id}</h3>
                      {node.location && (
                        <p className="text-xs text-zinc-500 mt-1 font-mono">
                          {node.location.lat.toFixed(6)}, {node.location.lon.toFixed(6)}
                        </p>
                      )}
                    </div>
                    <StatusBadge status={node.status} variant="node" size="sm" />
                  </div>

                  {node.last_telemetry_at && (
                    <div className="text-sm text-zinc-500 mb-2">
                      Last telemetry: {formatTimestamp(node.last_telemetry_at)}
                    </div>
                  )}

                  {node.battery_pct != null && (
                    <div className="flex items-center gap-2">
                      <div className="text-xs text-zinc-500">Battery:</div>
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
                      <StatusBadge
                        status={node.current_hazard_state}
                        variant="hazard"
                        size="sm"
                      />
                    </div>
                  )}

                  <div className="mt-3 text-xs text-zinc-600 text-right">
                    View Details →
                  </div>
                </GlassPanel>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

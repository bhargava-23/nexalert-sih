'use client'

// Map Page - Geographic view of nodes and hazards

import { useEffect, useState } from 'react'
import { GlassPanel } from '@/components/ui/GlassPanel'
import { SectionHeader } from '@/components/ui/SectionHeader'
import { LoadingSpinner } from '@/components/ui/Loading'
import { ErrorState } from '@/components/ui/ErrorState'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { api } from '@/lib/api'
import { formatTimestamp } from '@/lib/utils'
import type { Node } from '@/types'

export default function MapPage() {
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
        <ErrorState title="Map Error" message={error} onRetry={fetchNodes} />
      </div>
    )
  }

  const nodesWithLocation = nodes.filter(n => n.location)

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <SectionHeader
          title="Node Map"
          subtitle={`${nodesWithLocation.length} nodes with location data • Updated ${lastUpdate}`}
        />

        {nodesWithLocation.length === 0 ? (
          <GlassPanel className="text-center py-12">
            <p className="text-zinc-400">No nodes with location data available</p>
          </GlassPanel>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Map Placeholder */}
            <GlassPanel className="lg:col-span-2 h-[600px] flex items-center justify-center">
              <div className="text-center">
                <div className="text-4xl mb-4">🗺️</div>
                <p className="text-zinc-400 mb-2">Interactive map view</p>
                <p className="text-sm text-zinc-600">
                  Map integration requires a mapping library (Leaflet, Mapbox, etc.)
                </p>
                <p className="text-sm text-zinc-600 mt-4">
                  Showing {nodesWithLocation.length} node{nodesWithLocation.length !== 1 ? 's' : ''} with coordinates
                </p>
              </div>
            </GlassPanel>

            {/* Node List */}
            <div className="space-y-3">
              <h3 className="text-lg font-semibold text-zinc-100 mb-4">Nodes</h3>
              {nodesWithLocation.map((node) => (
                <GlassPanel key={node.node_id}>
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="font-semibold text-zinc-100">{node.node_id}</h4>
                    <StatusBadge status={node.status} variant="node" size="sm" />
                  </div>
                  {node.location && (
                    <div className="text-xs font-mono text-zinc-500">
                      {node.location.lat.toFixed(6)}, {node.location.lon.toFixed(6)}
                    </div>
                  )}
                  {node.current_hazard_state && node.current_hazard_state !== 'NORMAL' && (
                    <div className="mt-2 pt-2 border-t border-white/10">
                      <StatusBadge
                        status={node.current_hazard_state}
                        variant="hazard"
                        size="sm"
                      />
                    </div>
                  )}
                </GlassPanel>
              ))}
            </div>
          </div>
        )}

        <div className="mt-8">
          <GlassPanel className="bg-blue-500/10 border-blue-500/20">
            <div className="text-sm text-zinc-400">
              <strong className="text-blue-300">Note:</strong> Full interactive map requires integration with
              a mapping library (Leaflet, Mapbox GL JS, or Google Maps). The above coordinates are from the
              actual backend node data and can be used to render markers on an interactive map.
            </div>
          </GlassPanel>
        </div>
      </div>
    </div>
  )
}
